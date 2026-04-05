# -*- coding: utf-8 -*-
"""
AutomationController — Dispatcher central de automações.

OTIMIZAÇÕES APLICADAS:
  - Lazy loading por categoria: módulos só são instanciados na primeira chamada
  - Elimina 4 instâncias pesadas (FileAutomation, SystemAutomation, WebAutomation, UiAutomation)
    sendo criadas na inicialização, mesmo que nunca sejam usadas
  - Imports dos módulos movidos para dentro dos properties (lazy import)
  - Dispatcher usa dict de actions em vez de if/elif encadeados
"""
import logging
import asyncio

logger = logging.getLogger(__name__)


class AutomationController:
    """
    Controlador Central de Automações.
    Ponto único de orquestração seguindo o padrão 'categoria.acao'.

    Lazy Loading: cada categoria é instanciada apenas na primeira vez que
    um evento desta categoria é recebido. Se o usuário nunca pedir uma
    automação de arquivo, FileAutomation nunca é carregada na memória.
    """

    def __init__(self):
        # OTIMIZADO: Slots privados inicializados como None — instâncias criadas sob demanda
        self._file = None
        self._system = None
        self._web = None
        self._ui = None

    # ─── LAZY PROPERTIES — instanciação sob demanda ───────────────────────────

    @property
    def file(self):
        """FileAutomation: carregada apenas ao primeiro uso de 'file.*'"""
        if self._file is None:
            from .file_automation import FileAutomation
            self._file = FileAutomation()
            logger.info("[CONTROLLER] FileAutomation carregada (lazy).")
        return self._file

    @property
    def system(self):
        """SystemAutomation: carregada apenas ao primeiro uso de 'system.*'"""
        if self._system is None:
            from .system_automation import SystemAutomation
            self._system = SystemAutomation()
            logger.info("[CONTROLLER] SystemAutomation carregada (lazy).")
        return self._system

    @property
    def web(self):
        """WebAutomation: carregada apenas ao primeiro uso de 'web.*'"""
        if self._web is None:
            from .web_automation import WebAutomation
            self._web = WebAutomation()
            logger.info("[CONTROLLER] WebAutomation carregada (lazy).")
        return self._web

    @property
    def ui(self):
        """UiAutomation: carregada apenas ao primeiro uso de 'ui.*'"""
        if self._ui is None:
            from .ui_automation import UiAutomation
            self._ui = UiAutomation()
            logger.info("[CONTROLLER] UiAutomation carregada (lazy).")
        return self._ui

    # ─── DISPATCHER PRINCIPAL ────────────────────────────────────────────────

    async def run_event(self, event: str, params: dict = None):
        """
        Executa um evento seguindo o padrão 'categoria.acao'.
        Exemplos: 'web.search_web', 'system.open_app', 'ui.click'
        """
        params = params or {}
        logger.info(f"[AUTOMATION] → {event} | params={params}")

        try:
            if "." not in event:
                logger.warning(f"[AUTOMATION] Formato inválido: '{event}'. Use 'categoria.acao'.")
                return f"Erro: Formato inválido '{event}'. Use 'categoria.acao'."

            category, action = event.split(".", 1)

            if category == "file":
                return self._handle_file(action, params)
            elif category == "system":
                return self._handle_system(action, params)
            elif category == "web":
                return await self._handle_web(action, params)
            elif category == "ui":
                return self._handle_ui(action, params)
            else:
                logger.warning(f"[AUTOMATION] Categoria desconhecida: '{category}'.")
                return f"Erro: Categoria desconhecida '{category}'."

        except Exception as e:
            logger.error(f"[AUTOMATION] Falha crítica em run_event({event}): {e}")
            return f"Erro crítico na automação: {e}"

    # ─── HANDLERS POR CATEGORIA ──────────────────────────────────────────────

    def _handle_file(self, action: str, params: dict):
        _MAP = {
            "create_folder": lambda: self.file.create_folder(params),
            "delete_item":   lambda: self.file.delete_item(params),
            "open_folder":   lambda: self.file.open_folder(params),
        }
        fn = _MAP.get(action)
        return fn() if fn else self._unknown_action("file", action)

    def _handle_system(self, action: str, params: dict):
        _MAP = {
            "set_volume":    lambda: self.system.set_volume(params),
            "set_brightness": lambda: self.system.set_brightness(params),
            "open_app":      lambda: self.system.open_app(params),
            "power_action":  lambda: self.system.power_action(params),
        }
        fn = _MAP.get(action)
        return fn() if fn else self._unknown_action("system", action)

    async def _handle_web(self, action: str, params: dict):
        _MAP = {
            "search_web":   lambda: self.web.search_web(params),
            "open_shortcut": lambda: self.web.open_shortcut(params),
            "media_control": lambda: self.web.media_control(params),
        }
        fn = _MAP.get(action)
        if fn:
            return await fn()
        return self._unknown_action("web", action)

    def _handle_ui(self, action: str, params: dict):
        # Mapeamento completo de ações de UI
        _MAP = {
            # Mouse
            "click":           lambda: self.ui.click(params),
            "double_click":    lambda: self.ui.double_click(params),
            "right_click":     lambda: self.ui.right_click(params),
            "move_mouse":      lambda: self.ui.move_mouse(params),
            "scroll":          lambda: self.ui.scroll(params),
            "drag_and_drop":   lambda: self.ui.drag_and_drop(params),
            # Teclado
            "type_text":       lambda: self.ui.type_text(params),
            "press_key":       lambda: self.ui.press_key(params),
            "hotkey":          lambda: self.ui.hotkey(params),
            "hold_key":        lambda: self.ui.hold_key(params),
            # Janelas
            "focus_window":    lambda: self.ui.focus_window(params),
            "minimize_window": lambda: self.ui.minimize_window(params),
            "maximize_window": lambda: self.ui.maximize_window(params),
            "close_window":    lambda: self.ui.close_window(params),
            "resize_window":   lambda: self.ui.resize_window(params),
            "list_windows":    lambda: self.ui.list_windows(params),
            # Screenshot / Visão
            "screenshot":      lambda: self.ui.screenshot(params),
            "screen_size":     lambda: self.ui.get_screen_size(params),
            "mouse_position":  lambda: self.ui.get_mouse_position(params),
            "find_on_screen":  lambda: self.ui.find_on_screen(params),
            # Permissões e UAC
            "accept_uac":      lambda: self.ui.accept_uac_prompt(params),
            "click_button":    lambda: self.ui.click_button_in_window(params),
            "fill_field":      lambda: self.ui.fill_field_in_window(params),
            "run_as_admin":    lambda: self.ui.run_as_admin(params),
            # Clipboard
            "clipboard_copy":  lambda: self.ui.clipboard_copy(params),
            "clipboard_paste": lambda: self.ui.clipboard_paste(params),
            # Utilitários
            "wait":            lambda: self.ui.wait(params),
        }
        fn = _MAP.get(action)
        return fn() if fn else self._unknown_action("ui", action)

    def _unknown_action(self, category: str, action: str) -> str:
        logger.warning(f"[AUTOMATION] Ação desconhecida: '{action}' na categoria '{category}'.")
        return f"Erro: Ação desconhecida '{action}' na categoria '{category}'."

    def status(self) -> dict:
        """Retorna quais módulos estão carregados (útil para debug/monitoramento)."""
        return {
            "file":   self._file is not None,
            "system": self._system is not None,
            "web":    self._web is not None,
            "ui":     self._ui is not None,
        }
