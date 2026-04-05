import logging
import time
import subprocess
import os
import ctypes
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Importações Condicionais de GUI ───────────────────────────────────────────
# pyautogui: controle de mouse/teclado
try:
    import pyautogui
    pyautogui.FAILSAFE = True   # Mover mouse para canto superior esquerdo = emergência
    pyautogui.PAUSE = 0.05      # Pequena pausa entre ações para estabilidade
    PYAUTOGUI_OK = True
except ImportError:
    PYAUTOGUI_OK = False
    logger.warning("[UI] pyautogui não instalado. Instale com: pip install pyautogui")

# pygetwindow: gerenciamento de janelas
try:
    import pygetwindow as gw
    PYGW_OK = True
except ImportError:
    PYGW_OK = False
    logger.warning("[UI] pygetwindow não instalado. Instale com: pip install pygetwindow")

# Pillow: screenshots e análise de imagem
try:
    from PIL import ImageGrab, Image
    PIL_OK = True
except ImportError:
    PIL_OK = False
    logger.warning("[UI] Pillow não instalado. Instale com: pip install pillow")

# pywinauto: interação profunda com UI elements do Windows
try:
    from pywinauto import Application, Desktop
    from pywinauto.findwindows import ElementNotFoundError
    PYWINAUTO_OK = True
except ImportError:
    PYWINAUTO_OK = False
    logger.warning("[UI] pywinauto não instalado. Instale com: pip install pywinauto")

# keyboard: hotkeys e teclas especiais
try:
    import keyboard
    KEYBOARD_OK = True
except ImportError:
    KEYBOARD_OK = False
    logger.warning("[UI] keyboard não instalado. Instale com: pip install keyboard")


class UiAutomation:
    """
    Módulo de Automação de Interface Gráfica (GUI).
    Permite ao Jarvis interagir com qualquer janela, programa ou elemento
    do sistema operacional — como se tivesse mãos digitais.
    """

    # ─── MOUSE ──────────────────────────────────────────────────────────────────

    def click(self, params: dict) -> str:
        """Clica em uma posição (x, y) na tela."""
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        x = params.get("x")
        y = params.get("y")
        button = params.get("botao", "left")  # left | right | middle
        clicks = params.get("cliques", 1)
        if x is None or y is None:
            return "Erro: parâmetros 'x' e 'y' são obrigatórios."
        try:
            pyautogui.click(x, y, button=button, clicks=clicks, interval=0.1)
            return f"Clique {'duplo ' if clicks == 2 else ''}em ({x}, {y}) com botão '{button}'."
        except Exception as e:
            return f"Erro no clique: {e}"

    def double_click(self, params: dict) -> str:
        """Clica duas vezes em uma posição (x, y)."""
        params["cliques"] = 2
        return self.click(params)

    def right_click(self, params: dict) -> str:
        """Clica com o botão direito em uma posição (x, y)."""
        params["botao"] = "right"
        return self.click(params)

    def move_mouse(self, params: dict) -> str:
        """Move o mouse para uma posição (x, y) sem clicar."""
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        x = params.get("x")
        y = params.get("y")
        duracao = params.get("duracao", 0.3)
        if x is None or y is None:
            return "Erro: parâmetros 'x' e 'y' são obrigatórios."
        try:
            pyautogui.moveTo(x, y, duration=duracao)
            return f"Mouse movido para ({x}, {y})."
        except Exception as e:
            return f"Erro ao mover mouse: {e}"

    def scroll(self, params: dict) -> str:
        """Rola a roda do mouse. clicks>0 = cima, clicks<0 = baixo."""
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        clicks = params.get("clicks", 3)
        x = params.get("x")
        y = params.get("y")
        try:
            if x and y:
                pyautogui.scroll(clicks, x=x, y=y)
            else:
                pyautogui.scroll(clicks)
            direcao = "cima" if clicks > 0 else "baixo"
            return f"Scroll para {direcao} ({abs(clicks)} unidades)."
        except Exception as e:
            return f"Erro no scroll: {e}"

    def drag_and_drop(self, params: dict) -> str:
        """Arrasta de (x1, y1) até (x2, y2)."""
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        x1 = params.get("x1")
        y1 = params.get("y1")
        x2 = params.get("x2")
        y2 = params.get("y2")
        duracao = params.get("duracao", 0.5)
        if None in [x1, y1, x2, y2]:
            return "Erro: parâmetros x1, y1, x2, y2 obrigatórios."
        try:
            pyautogui.moveTo(x1, y1, duration=0.2)
            pyautogui.dragTo(x2, y2, duration=duracao, button="left")
            return f"Arrastado de ({x1},{y1}) para ({x2},{y2})."
        except Exception as e:
            return f"Erro no drag-and-drop: {e}"

    # ─── TECLADO ────────────────────────────────────────────────────────────────

    def type_text(self, params: dict) -> str:
        """
        Digita um texto na janela/campo ativo.
        UNICODE FIX: Usa clipboard + Ctrl+V para garantir suporte total a acentos
        (ã, é, ç, ô, etc.), pois pyautogui.write() não suporta Unicode nativamente.
        """
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        texto = params.get("texto", "")
        if not texto:
            return "Erro: parâmetro 'texto' é obrigatório."
        try:
            # Estratégia 1: pyperclip (mais confiável para Unicode)
            try:
                import pyperclip
                pyperclip.copy(texto)
                pyautogui.hotkey("ctrl", "v")
                return f"Texto digitado via clipboard ({len(texto)} caracteres). Acentos preservados."
            except ImportError:
                pass

            # Estratégia 2: subprocess clip (fallback Windows)
            try:
                import subprocess
                subprocess.run(
                    "clip", input=texto.encode("utf-16-le"), check=True,
                    capture_output=True
                )
                pyautogui.hotkey("ctrl", "v")
                return f"Texto digitado via clip ({len(texto)} caracteres)."
            except Exception:
                pass

            # Estratégia 3: pyautogui nativo (sem garantia de Unicode)
            intervalo = params.get("intervalo", 0.03)
            pyautogui.write(texto, interval=intervalo)
            return f"Texto digitado (modo básico — instale pyperclip para suporte a acentos)."
        except Exception as e:
            return f"Erro ao digitar: {e}"


    def press_key(self, params: dict) -> str:
        """Pressiona uma tecla (ex: 'enter', 'esc', 'tab', 'F5')."""
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        tecla = params.get("tecla")
        if not tecla:
            return "Erro: parâmetro 'tecla' é obrigatório."
        try:
            pyautogui.press(tecla)
            return f"Tecla '{tecla}' pressionada."
        except Exception as e:
            return f"Erro ao pressionar tecla: {e}"

    def hotkey(self, params: dict) -> str:
        """Executa um atalho de teclado (ex: 'ctrl+c', 'alt+F4', 'win+d')."""
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        atalho = params.get("atalho")
        if not atalho:
            return "Erro: parâmetro 'atalho' é obrigatório."
        try:
            # Suporta formato: 'ctrl+c' ou ['ctrl', 'c']
            teclas = [t.strip() for t in atalho.split("+")]
            pyautogui.hotkey(*teclas)
            return f"Atalho '{atalho}' executado."
        except Exception as e:
            return f"Erro no atalho: {e}"

    def hold_key(self, params: dict) -> str:
        """Pressiona e segura uma tecla por X segundos."""
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        tecla = params.get("tecla")
        segundos = params.get("segundos", 1.0)
        if not tecla:
            return "Erro: parâmetro 'tecla' é obrigatório."
        try:
            pyautogui.keyDown(tecla)
            time.sleep(segundos)
            pyautogui.keyUp(tecla)
            return f"Tecla '{tecla}' mantida por {segundos}s."
        except Exception as e:
            return f"Erro ao segurar tecla: {e}"

    # ─── JANELAS ────────────────────────────────────────────────────────────────

    def focus_window(self, params: dict) -> str:
        """Traz uma janela para o foco pelo título (ou parte dele)."""
        if not PYGW_OK:
            return "Erro: pygetwindow não disponível."
        titulo = params.get("titulo")
        if not titulo:
            return "Erro: parâmetro 'titulo' é obrigatório."
        try:
            windows = gw.getWindowsWithTitle(titulo)
            if not windows:
                # Lista janelas disponíveis para debug
                all_titles = [w.title for w in gw.getAllWindows() if w.title.strip()]
                return f"Janela '{titulo}' não encontrada. Janelas abertas: {all_titles[:10]}"
            win = windows[0]
            win.restore()
            win.activate()
            time.sleep(0.3)
            return f"Janela '{win.title}' focada com sucesso."
        except Exception as e:
            return f"Erro ao focar janela: {e}"

    def minimize_window(self, params: dict) -> str:
        """Minimiza uma janela pelo título."""
        if not PYGW_OK:
            return "Erro: pygetwindow não disponível."
        titulo = params.get("titulo")
        if not titulo:
            return "Erro: parâmetro 'titulo' é obrigatório."
        try:
            windows = gw.getWindowsWithTitle(titulo)
            if not windows:
                return f"Janela '{titulo}' não encontrada."
            windows[0].minimize()
            return f"Janela '{titulo}' minimizada."
        except Exception as e:
            return f"Erro: {e}"

    def maximize_window(self, params: dict) -> str:
        """Maximiza uma janela pelo título."""
        if not PYGW_OK:
            return "Erro: pygetwindow não disponível."
        titulo = params.get("titulo")
        if not titulo:
            return "Erro: parâmetro 'titulo' é obrigatório."
        try:
            windows = gw.getWindowsWithTitle(titulo)
            if not windows:
                return f"Janela '{titulo}' não encontrada."
            windows[0].maximize()
            return f"Janela '{titulo}' maximizada."
        except Exception as e:
            return f"Erro: {e}"

    def close_window(self, params: dict) -> str:
        """Fecha uma janela pelo título."""
        if not PYGW_OK:
            return "Erro: pygetwindow não disponível."
        titulo = params.get("titulo")
        if not titulo:
            return "Erro: parâmetro 'titulo' é obrigatório."
        try:
            windows = gw.getWindowsWithTitle(titulo)
            if not windows:
                return f"Janela '{titulo}' não encontrada."
            windows[0].close()
            return f"Janela '{titulo}' fechada."
        except Exception as e:
            return f"Erro: {e}"

    def resize_window(self, params: dict) -> str:
        """Redimensiona uma janela (titulo, largura, altura)."""
        if not PYGW_OK:
            return "Erro: pygetwindow não disponível."
        titulo = params.get("titulo")
        largura = params.get("largura", 1280)
        altura = params.get("altura", 720)
        try:
            windows = gw.getWindowsWithTitle(titulo)
            if not windows:
                return f"Janela '{titulo}' não encontrada."
            windows[0].resizeTo(largura, altura)
            return f"Janela '{titulo}' redimensionada para {largura}x{altura}."
        except Exception as e:
            return f"Erro: {e}"

    def list_windows(self, params: dict) -> str:
        """Lista todas as janelas abertas atualmente."""
        if not PYGW_OK:
            return "Erro: pygetwindow não disponível."
        try:
            windows = [w.title for w in gw.getAllWindows() if w.title.strip()]
            if not windows:
                return "Nenhuma janela aberta encontrada."
            lista = "\n".join(f"  - {t}" for t in windows)
            return f"Janelas abertas ({len(windows)}):\n{lista}"
        except Exception as e:
            return f"Erro: {e}"

    # ─── SCREENSHOT & VISÃO ─────────────────────────────────────────────────────

    def screenshot(self, params: dict) -> str:
        """Tira um screenshot da tela e salva em arquivo ou retorna path."""
        if not PIL_OK:
            return "Erro: Pillow não disponível."
        caminho = params.get("caminho", os.path.join(os.path.expanduser("~"), "Desktop", "jarvis_screenshot.png"))
        regiao = params.get("regiao")  # (x, y, largura, altura)
        try:
            if regiao:
                x, y, w, h = regiao
                img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
            else:
                img = ImageGrab.grab()
            img.save(caminho)
            return f"Screenshot salvo em: {caminho}"
        except Exception as e:
            return f"Erro ao tirar screenshot: {e}"

    def get_screen_size(self, params: dict) -> str:
        """Retorna a resolução atual da tela."""
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        try:
            w, h = pyautogui.size()
            return f"Resolução da tela: {w}x{h} pixels."
        except Exception as e:
            return f"Erro: {e}"

    def get_mouse_position(self, params: dict) -> str:
        """Retorna a posição atual do cursor do mouse."""
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        try:
            x, y = pyautogui.position()
            return f"Posição atual do mouse: ({x}, {y})."
        except Exception as e:
            return f"Erro: {e}"

    # ─── PERMISSÕES E UAC ───────────────────────────────────────────────────────

    def accept_uac_prompt(self, params: dict) -> str:
        """
        Detecta e aceita automaticamente um prompt de UAC (User Account Control)
        do Windows usando pywinauto.
        """
        if not PYWINAUTO_OK:
            return "Erro: pywinauto não disponível. Instale com: pip install pywinauto"
        try:
            desktop = Desktop(backend="uia")
            # Busca por janelas típicas de UAC
            uac_titles = ["User Account Control", "Controle de Conta de Usuário", "Consent UI"]
            for title in uac_titles:
                try:
                    uac_win = desktop.window(title_re=f".*{title}.*")
                    if uac_win.exists(timeout=2):
                        # Tenta clicar em "Sim" ou "Yes"
                        try:
                            uac_win["Sim"].click()
                            return "Permissão UAC concedida (clicou em 'Sim')."
                        except Exception:
                            pass
                        try:
                            uac_win["Yes"].click()
                            return "Permissão UAC concedida (clicou em 'Yes')."
                        except Exception:
                            pass
                except Exception:
                    continue
            return "Nenhum prompt UAC encontrado no momento."
        except Exception as e:
            return f"Erro ao lidar com UAC: {e}"

    def click_button_in_window(self, params: dict) -> str:
        """
        Clica em um botão específico dentro de uma janela pelo nome.
        Usa pywinauto para interagir com elementos de UI sem precisar das coordenadas.
        """
        if not PYWINAUTO_OK:
            return "Erro: pywinauto não disponível."
        titulo_janela = params.get("janela")
        nome_botao = params.get("botao")
        if not titulo_janela or not nome_botao:
            return "Erro: parâmetros 'janela' e 'botao' são obrigatórios."
        try:
            app = Application(backend="uia").connect(title_re=f".*{titulo_janela}.*")
            dlg = app.top_window()
            dlg[nome_botao].click()
            return f"Botão '{nome_botao}' clicado na janela '{titulo_janela}'."
        except Exception as e:
            return f"Erro ao clicar no botão: {e}"

    def fill_field_in_window(self, params: dict) -> str:
        """
        Preenche um campo de texto em uma janela específica usando pywinauto.
        """
        if not PYWINAUTO_OK:
            return "Erro: pywinauto não disponível."
        titulo_janela = params.get("janela")
        nome_campo = params.get("campo")
        texto = params.get("texto", "")
        if not titulo_janela or not nome_campo:
            return "Erro: parâmetros 'janela', 'campo' e 'texto' são obrigatórios."
        try:
            app = Application(backend="uia").connect(title_re=f".*{titulo_janela}.*")
            dlg = app.top_window()
            field = dlg[nome_campo]
            field.set_focus()
            field.type_keys(texto, with_spaces=True)
            return f"Campo '{nome_campo}' preenchido com '{texto}' na janela '{titulo_janela}'."
        except Exception as e:
            return f"Erro ao preencher campo: {e}"

    def run_as_admin(self, params: dict) -> str:
        """
        Executa um programa com privilégios de administrador (elevação UAC).
        """
        programa = params.get("programa")
        argumentos = params.get("argumentos", "")
        if not programa:
            return "Erro: parâmetro 'programa' é obrigatório."
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", programa, argumentos, None, 1
            )
            return f"Programa '{programa}' iniciado como Administrador."
        except Exception as e:
            return f"Erro ao executar como admin: {e}"

    def clipboard_copy(self, params: dict) -> str:
        """Copia texto para a área de transferência com suporte a Unicode/acentos."""
        texto = params.get("texto", "")
        try:
            # Estratégia 1: pyperclip (melhor suporte a Unicode em qualquer plataforma)
            try:
                import pyperclip
                pyperclip.copy(texto)
                return f"Texto copiado para o clipboard ({len(texto)} chars). Acentos preservados."
            except ImportError:
                pass
            # Estratégia 2: subprocess clip com UTF-16-LE (encoding correto para Windows clip.exe)
            import subprocess
            subprocess.run(["clip"], input=texto.encode("utf-16-le"), check=True)
            return f"Texto copiado para o clipboard ({len(texto)} chars)."
        except Exception as e:
            return f"Erro ao copiar: {e}"


    def clipboard_paste(self, params: dict) -> str:
        """Cola o conteúdo da área de transferência na janela ativa."""
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        try:
            pyautogui.hotkey("ctrl", "v")
            return "Conteúdo colado da área de transferência."
        except Exception as e:
            return f"Erro ao colar: {e}"

    # ─── UTILITÁRIOS ────────────────────────────────────────────────────────────

    def wait(self, params: dict) -> str:
        """Aguarda X segundos (útil para esperar carregamento de telas)."""
        segundos = params.get("segundos", 1.0)
        time.sleep(segundos)
        return f"Aguardei {segundos} segundos."

    def find_on_screen(self, params: dict) -> str:
        """
        Procura uma imagem na tela e clica nela se encontrada.
        Exige o caminho de uma imagem de referência.
        """
        if not PYAUTOGUI_OK:
            return "Erro: pyautogui não disponível."
        imagem_ref = params.get("imagem")
        clicar = params.get("clicar", True)
        confianca = params.get("confianca", 0.8)
        if not imagem_ref:
            return "Erro: parâmetro 'imagem' (caminho do arquivo) é obrigatório."
        if not os.path.exists(imagem_ref):
            return f"Erro: imagem de referência não encontrada em '{imagem_ref}'."
        try:
            location = pyautogui.locateOnScreen(imagem_ref, confidence=confianca)
            if location is None:
                return f"Imagem '{imagem_ref}' não encontrada na tela."
            center = pyautogui.center(location)
            if clicar:
                pyautogui.click(center)
                return f"Imagem encontrada e clicada em {center}."
            return f"Imagem encontrada em {location} (centro: {center})."
        except Exception as e:
            return f"Erro ao procurar imagem: {e}"
