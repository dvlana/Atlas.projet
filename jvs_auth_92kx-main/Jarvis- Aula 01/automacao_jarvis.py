# -*- coding: utf-8 -*-
"""
JarvisControl — Núcleo de orquestração do backend Jarvis.

OTIMIZAÇÕES APLICADAS:
  - asyncio.run() nos métodos legados substituído por get_event_loop().run_until_complete()
    com fallback seguro — evita criar novo event loop por chamada
  - ClapDetector com debug_mode=False por padrão (sem spam de print)
  - Indentação corrigida em start_bio_claps
  - Método status() adicionado para monitoramento do estado interno
"""
import logging
import asyncio
from automation.automation_controller import AutomationController
from automation.clap_detector import ClapDetector

logger = logging.getLogger(__name__)


def _run_sync(coro):
    """
    Executa uma coroutine de forma síncrona sem criar novo event loop.
    Reutiliza o loop existente se disponível, ou cria um novo como último recurso.

    ATENÇÃO: Usar apenas nos métodos legados. O ideal é chamar run_event() diretamente
    de dentro de contexto async (via await).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Contexto já tem loop rodando (ex: Jupyter, scripts) — usa run_coroutine_threadsafe
            import concurrent.futures
            future = asyncio.run_coroutine_threadsafe(coro, loop)
            return future.result(timeout=10)
        return loop.run_until_complete(coro)
    except RuntimeError:
        # Nenhum loop disponível — cria um novo (último recurso)
        return asyncio.run(coro)


class JarvisControl:
    """
    Núcleo de Automação (Backend) — Jarvis Aula 01.
    Atua como ponto central de orquestração usando estrutura modular em 'automation/'.
    """

    def __init__(self):
        # AutomationController agora usa lazy loading — inicialização é instantânea
        self.controller = AutomationController()

        # Bio-Claps: debug desligado por padrão (evita spam de logs de áudio)
        # PROTEÇÃO: default_app vazio = nenhum app abre automaticamente.
        # Para ativar, chame: jarvis.set_clap_action('nome_do_app')
        self.clap_system = ClapDetector(
            automation_controller=self.controller,
            threshold=0.15,
            default_app="",              # CORRIGIDO: NÃO abre nada sem configuração explícita
            debug_mode=False,           # Muda para True se precisar calibrar o microfone
            preferred_device=9,         # Device 9 = fallback automático padrão
        )

    def start_bio_claps(self, loop: asyncio.AbstractEventLoop):
        """Inicia o sistema de Bio-Claps. Idempotente (seguro para chamar várias vezes)."""
        if self.clap_system.is_running:
            return
        self.clap_system.start(loop)

    def stop_bio_claps(self):
        """Para o sistema de Bio-Claps de forma segura."""
        self.clap_system.stop()

    def set_clap_action(self, app_name: str):
        """Define qual app abre ao detectar palmas."""
        self.clap_system.set_action(app_name)

    def status(self) -> dict:
        """Retorna estado atual do sistema para monitoramento."""
        return {
            "bio_claps_active": self.clap_system.is_running,
            "clap_threshold": self.clap_system.threshold,
            "clap_default_app": self.clap_system.default_app,
            "modules_loaded": self.controller.status(),
        }

    # ─────────────────────────────────────────────────────────────────────────
    # MÉTODOS LEGADOS — mantidos para compatibilidade com código existente
    # Preferir chamar self.controller.run_event() diretamente em contexto async
    # ─────────────────────────────────────────────────────────────────────────

    def cria_pasta(self, caminho):
        return _run_sync(self.controller.run_event("file.create_folder", {"caminho": caminho}))

    def abrir_pasta(self, nome_pasta):
        return _run_sync(self.controller.run_event("file.open_folder", {"nome_pasta": nome_pasta}))

    def deletar_arquivo(self, caminho):
        return _run_sync(self.controller.run_event("file.delete_item", {"caminho": caminho}))

    def controle_volume(self, nivel):
        return _run_sync(self.controller.run_event("system.set_volume", {"nivel": nivel}))

    def controle_brilho(self, nivel):
        return _run_sync(self.controller.run_event("system.set_brightness", {"nivel": nivel}))

    def abrir_aplicativo(self, nome_app):
        return _run_sync(self.controller.run_event("system.open_app", {"nome_app": nome_app}))

    def energia_pc(self, acao):
        return _run_sync(self.controller.run_event("system.power_action", {"acao": acao}))


if __name__ == "__main__":
    jc = JarvisControl()
    print("Núcleo de Automação Jarvis inicializado.")
    print("Status:", jc.status())
    print()
    print("AVISO: Bio-Claps não abre nenhum app por padrão.")
    print("Use jc.set_clap_action('nome_do_app') para configurar a ação.")
