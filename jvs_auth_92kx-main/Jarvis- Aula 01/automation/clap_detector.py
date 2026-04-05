# -*- coding: utf-8 -*-
"""
ClapDetector — Sistema de detecção de palmas bio-acústico.

OTIMIZAÇÕES APLICADAS:
  - Removido print() do callback de áudio (era chamado 21x/s — IO massivo)
  - Debug desabilitado por padrão (ativar via debug_mode=True)
  - Fallback automático de dispositivo (tenta device=9, depois padrão do sistema)
  - Thread do monitor com Event-based stop (sem polling puro)
  - Buffer de timestamps com deque de tamanho fixo (sem alocação dinâmica)
  - Graceful degradation: sistema continua funcionando mesmo sem microfone
"""
import numpy as np
import sounddevice as sd
import time
import threading
import logging
import asyncio
from typing import Optional
from collections import deque

logger = logging.getLogger(__name__)


class ClapDetector:
    """
    Detecção de palmas em tempo real integrada ao AutomationController.
    Projetada para máxima eficiência: mínimo de CPU, zero I/O no callback de áudio.
    """

    # ── PROTEÇÃO: apps que NUNCA devem ser abertos automaticamente ──────────
    _BLOCKED_APPS = {"notepad", "notepad.exe", ""}

    def __init__(
        self,
        automation_controller,
        threshold: float = 0.15,
        debounce_seconds: float = 0.25,
        window_seconds: float = 1.0,
        default_app: str = "",          # CORRIGIDO: vazio = nenhuma ação automática
        debug_mode: bool = False,       # debug desligado por padrão (evita spam de logs)
        preferred_device: int = None,   # None = usa dispositivo padrão do sistema
    ):
        self.controller = automation_controller
        self.threshold = threshold
        self.debounce_time = debounce_seconds
        self.window_time = window_seconds
        self.default_app = default_app
        self.debug_mode = debug_mode
        self.preferred_device = preferred_device

        # Estado interno
        self.is_running = False
        self.last_clap_time: float = 0.0
        # OTIMIZADO: deque com tamanho máximo fixo = sem crescimento ilimitado de memória
        self.claps_timestamps: deque = deque(maxlen=20)
        self.ambient_noise_level: float = 0.02
        self.stream: Optional[sd.InputStream] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None

        # OTIMIZADO: Event para parar a thread de forma limpa (sem polling de flag)
        self._stop_event = threading.Event()
        self._monitor_thread: Optional[threading.Thread] = None

    def _log(self, msg: str, level: str = "info"):
        """Log centralizado — nunca usa print() fora de contexto debug."""
        fmt = f"[AUDIO] {msg}"
        if level == "error":
            logger.error(fmt)
        elif level == "warning":
            logger.warning(fmt)
        else:
            logger.info(fmt)
        if self.debug_mode:
            print(fmt)

    # ─────────────────────────────────────────────────────────────────────────
    # CALLBACK DE ÁUDIO — executado pelo thread interno do sounddevice
    # REGRA CRÍTICA: ZERO I/O aqui (sem print, sem logger, sem disco)
    # Qualquer I/O bloqueia o callback e causa XRun (glitch de áudio)
    # ─────────────────────────────────────────────────────────────────────────
    def process_audio(self, indata, frames, time_info, status):
        """
        Processa bloco de áudio e detecta picos.
        Chamado ~21x por segundo (44100Hz / blocksize=2048).
        NÃO deve fazer I/O — apenas computação leve em numpy.
        """
        # OTIMIZADO: usa np.dot para RMS — mais rápido que np.linalg.norm
        rms = float(np.sqrt(np.dot(indata[:, 0], indata[:, 0]) / frames))
        current_time = time.monotonic()  # OTIMIZADO: monotonic é mais leve que time.time()

        # Atualiza ruído ambiente com filtro exponencial (EMA)
        self.ambient_noise_level = 0.97 * self.ambient_noise_level + 0.03 * rms

        # Detecção de pico acima do threshold com debounce
        if rms > self.threshold:
            if (current_time - self.last_clap_time) > self.debounce_time:
                self.last_clap_time = current_time
                self.claps_timestamps.append(current_time)
                # Debug condicional — só printa se debug_mode=True
                if self.debug_mode:
                    print(f"[AUDIO DEBUG] Clap! RMS={rms:.4f} | Total buffer={len(self.claps_timestamps)}")

    # ─────────────────────────────────────────────────────────────────────────
    # MONITOR THREAD — verifica padrões de palmas
    # ─────────────────────────────────────────────────────────────────────────
    def monitor_loop(self):
        """
        Thread de monitoramento. Usa Event-based sleep em vez de polling puro.
        Acorda a cada 150ms para verificar padrões no buffer de timestamps.
        """
        self._log("Monitor de padrões iniciado.")
        while not self._stop_event.wait(timeout=0.15):  # OTIMIZADO: Event.wait é mais eficiente que sleep + flag check
            current_time = time.monotonic()

            # Remove timestamps fora da janela de tempo (operação O(n) com deque — eficiente)
            while self.claps_timestamps and (current_time - self.claps_timestamps[0]) > self.window_time:
                self.claps_timestamps.popleft()

            # Dispara ação quando detecta 2+ palmas na janela
            if len(self.claps_timestamps) >= 2:
                # ── SPAWN GUARD ──────────────────────────────────────────────
                # Bloqueia abertura automática se nenhum app foi configurado
                # explicitamente pelo usuário ou se o app é o legado 'notepad'.
                app_normalizado = (self.default_app or "").strip().lower()
                if app_normalizado in self._BLOCKED_APPS:
                    logger.warning(
                        "[CLAP][SPAWN-GUARD] Palmas detectadas mas nenhum app configurado "
                        f"(default_app={self.default_app!r}). Ignorando disparo automático. "
                        "Use clap_detector.set_action('nome_do_app') para configurar."
                    )
                    self.claps_timestamps.clear()
                    continue

                self._log(
                    f"Padrão detectado: {len(self.claps_timestamps)} palmas → abrindo '{self.default_app}'"
                )
                logger.info(
                    f"[CLAP][SPAWN] Abrindo app externo via palmas: app={self.default_app!r}"
                )

                if self.loop and self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.controller.run_event("system.open_app", {"nome_app": self.default_app}),
                        self.loop
                    )

                # Limpa buffer após disparo para evitar re-triggers
                self.claps_timestamps.clear()

        self._log("Monitor de padrões encerrado.")

    # ─────────────────────────────────────────────────────────────────────────
    # CONTROLE DE CICLO DE VIDA
    # ─────────────────────────────────────────────────────────────────────────
    def start(self, loop: asyncio.AbstractEventLoop):
        """Inicia detecção. Seguro para chamar múltiplas vezes (idempotente)."""
        if self.is_running:
            self._log("Bio-Claps já está ativo — ignorando chamada duplicada.")
            return

        self.loop = loop
        self.is_running = True
        self._stop_event.clear()

        # Inicia thread de monitoramento
        self._monitor_thread = threading.Thread(
            target=self.monitor_loop,
            name="ClapMonitor",
            daemon=True
        )
        self._monitor_thread.start()

        # Tenta iniciar stream com dispositivo preferido, depois tenta padrão como fallback
        self._start_stream()

    def _start_stream(self):
        """
        Tenta abrir o stream de áudio.
        Estratégia: preferred_device → device=9 (legado) → default do sistema.
        """
        devices_to_try = []

        if self.preferred_device is not None:
            devices_to_try.append(self.preferred_device)
        devices_to_try.append(9)     # dispositivo legado (mantido por compatibilidade)
        devices_to_try.append(None)  # padrão do sistema (fallback final)

        for device in devices_to_try:
            try:
                self.stream = sd.InputStream(
                    callback=self.process_audio,
                    channels=1,
                    samplerate=44100,
                    blocksize=2048,
                    dtype='float32',   # OTIMIZADO: explícito evita conversão interna
                    device=device,
                    latency='low',     # OTIMIZADO: baixa latência reduz overhead de buffer
                )
                self.stream.start()
                device_label = f"device={device}" if device is not None else "device=default"
                self._log(f"Bio-Claps ativo [{device_label}]. Sistema de escuta calibrado.")
                return
            except Exception as e:
                label = f"device={device}" if device is not None else "device=default"
                logger.warning(f"[AUDIO] Falha ao abrir {label}: {e}. Tentando próximo...")

        # Nenhum dispositivo funcionou — degrada graciosamente
        self._log("AVISO: Nenhum microfone disponível. Bio-Claps desativado (sistema continua funcionando).", "warning")
        self.is_running = False
        self._stop_event.set()

    def stop(self):
        """Para a detecção de forma limpa e segura."""
        if not self.is_running:
            return

        self.is_running = False
        self._stop_event.set()  # Sinaliza a thread para parar

        if self.stream:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None

        # Aguarda thread encerrar (com timeout — não trava o shutdown)
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)

        self.claps_timestamps.clear()
        self._log("Bio-Claps em standby.")

    def set_action(self, app_name: str):
        """Atualiza o aplicativo padrão que será aberto ao detectar palmas."""
        self.default_app = app_name
        self._log(f"Ação atualizada: abrir '{app_name}' ao detectar palmas.")

    def set_threshold(self, threshold: float):
        """Atualiza threshold de sensibilidade em tempo real (sem reiniciar)."""
        self.threshold = max(0.01, min(1.0, threshold))
        self._log(f"Threshold atualizado para {self.threshold:.3f}")
