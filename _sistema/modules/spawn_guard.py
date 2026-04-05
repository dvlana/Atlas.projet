# -*- coding: utf-8 -*-
"""
SpawnGuard — Sistema de Controle de Processos Externos
=======================================================
Módulo de segurança central do Origem.1.

Responsabilidades:
  - Bloquear abertura de apps proibidos (ex: notepad sem intenção explícita)
  - Registrar TODA abertura de processo externo em log auditável
  - Singleton guard: impedir spawns duplicados do mesmo processo
  - Debounce: impedir re-trigger dentro de janela de tempo configurável

Uso:
  from _sistema.modules.spawn_guard import SpawnGuard
  guard = SpawnGuard()
  guard.open("calculadora")           # OK — app permitido
  guard.open("notepad")              # BLOQUEADO — app proibido
  guard.open("spotify", force=True)  # Força abertura com flag explícita
"""

import subprocess
import os
import time
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("Origem.SpawnGuard")

# ─── RAIZ DO SISTEMA ──────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent  # → /Origem.1
_LOG_DIR = _ROOT / "_sistema" / "logs"


class SpawnGuard:
    """
    Controlador central de spawn de processos externos.

    Princípios:
      1. Todo spawn é auditado — sem exceção
      2. Apps bloqueados jamais são abertos por automações
      3. Spawns duplicados são ignorados dentro da janela de debounce
      4. force=True exige intenção explícita do código chamador
    """

    # Apps permanentemente bloqueados para abertura automática
    BLOCKED: frozenset = frozenset({
        "notepad", "notepad.exe",
        "regedit", "regedit.exe",
        "cmd", "cmd.exe",       # cmd só pode ser aberto via open() com force=True
    })

    # Mapa de nomes amigáveis → executáveis reais
    APP_MAP: dict = {
        "calculadora":          "calc.exe",
        "paint":                "mspaint.exe",
        "navegador":            "msedge",
        "explorador":           "explorer.exe",
        "terminal":             "wt",
        "vscode":               "code",
        "spotify":              "spotify",
        "chrome":               "chrome",
        "edge":                 "msedge",
        "firefox":              "firefox",
        "discord":              "discord",
        "vlc":                  "vlc",
    }

    def __init__(self, debounce_seconds: float = 1.5):
        self.debounce_seconds = debounce_seconds
        self._last_spawn: dict[str, float] = {}  # app → timestamp do último spawn
        self._audit_log = self._init_audit_log()

    def _init_audit_log(self) -> Path:
        """Cria pasta de logs e retorna caminho do arquivo de auditoria."""
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        return _LOG_DIR / "spawn_audit.log"

    def _write_audit(self, app: str, status: str, motivo: str = "") -> None:
        """Escreve linha no log de auditoria de spawns."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linha = f"{timestamp} | {status:10s} | app={app!r:<20s} | {motivo}\n"
        try:
            with open(self._audit_log, "a", encoding="utf-8") as f:
                f.write(linha)
        except Exception as e:
            logger.error(f"[SPAWN-AUDIT] Falha ao escrever log: {e}")

        # Também envia para logger estruturado
        if status == "BLOCKED":
            logger.warning(f"[SPAWN-GUARD] BLOQUEADO: app={app!r} | {motivo}")
        elif status == "DEBOUNCE":
            logger.debug(f"[SPAWN-GUARD] DEBOUNCE: app={app!r} | {motivo}")
        else:
            logger.info(f"[SPAWN-AUDIT] {status}: app={app!r} | {motivo}")

    def is_running(self, app_name: str) -> bool:
        """Verifica se um processo com esse nome já está rodando no sistema."""
        try:
            result = subprocess.run(
                ["tasklist", "/fi", f"imagename eq {app_name}"],
                capture_output=True, text=True
            )
            return app_name.lower() in result.stdout.lower()
        except Exception:
            return False

    def open(self, app: str, force: bool = False, caller: str = "unknown") -> str:
        """
        Abre um aplicativo com todas as proteções ativas.

        Args:
            app:    Nome amigável ou executável do app.
            force:  True = contorna debounce (mas NÃO contorna BLOCKED).
            caller: Identificador de quem chamou (para auditoria).

        Returns:
            String descrevendo o resultado da operação.
        """
        app_norm = app.strip().lower()

        # ─── 1. BLOCKED CHECK ─────────────────────────────────────────────────
        if app_norm in self.BLOCKED:
            motivo = f"app está na lista BLOCKED | caller={caller}"
            self._write_audit(app, "BLOCKED", motivo)
            return f"[SPAWN-GUARD] '{app}' bloqueado — não pode ser aberto por automação."

        # ─── 2. DEBOUNCE CHECK ────────────────────────────────────────────────
        if not force:
            ultimo = self._last_spawn.get(app_norm, 0.0)
            elapsed = time.monotonic() - ultimo
            if elapsed < self.debounce_seconds:
                motivo = f"debounce {elapsed:.2f}s < {self.debounce_seconds}s | caller={caller}"
                self._write_audit(app, "DEBOUNCE", motivo)
                return f"[SPAWN-GUARD] '{app}' ignorado (debounce {elapsed:.1f}s)."

        # ─── 3. RESOLVE EXECUTÁVEL ────────────────────────────────────────────
        executavel = self.APP_MAP.get(app_norm, app)

        # ─── 4. SPAWN ─────────────────────────────────────────────────────────
        try:
            os.startfile(executavel)
            self._last_spawn[app_norm] = time.monotonic()
            motivo = f"caller={caller} | executavel={executavel!r}"
            self._write_audit(app, "OPENED", motivo)
            return f"Abrindo '{app}'."
        except Exception as e:
            try:
                subprocess.Popen(["cmd", "/c", "start", "", executavel], shell=True)
                self._last_spawn[app_norm] = time.monotonic()
                motivo = f"fallback cmd | caller={caller} | executavel={executavel!r}"
                self._write_audit(app, "OPENED_FALLBACK", motivo)
                return f"Abrindo '{app}' (fallback)."
            except Exception as e2:
                motivo = f"ERRO: {e2} | caller={caller}"
                self._write_audit(app, "ERROR", motivo)
                logger.error(f"[SPAWN-GUARD] Falha ao abrir '{app}': {e2}")
                return f"Erro ao abrir '{app}': {e2}"

    def status(self) -> dict:
        """Retorna estado atual do SpawnGuard."""
        return {
            "blocked_apps": sorted(self.BLOCKED),
            "debounce_seconds": self.debounce_seconds,
            "recent_spawns": {
                app: round(time.monotonic() - ts, 1)
                for app, ts in self._last_spawn.items()
            },
        }
