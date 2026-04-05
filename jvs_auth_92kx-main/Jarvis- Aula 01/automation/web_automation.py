import os
import asyncio
import webbrowser
import subprocess
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

CDP_URL = "http://localhost:9222"


class WebAutomation:
    def __init__(self):
        # OTIMIZADO: chrome_path agora é lazy — não faz os.path.exists() na inicialização
        self._chrome_path = None
        self._chrome_path_checked = False
        self.shortcuts = {
            "youtube": "https://www.youtube.com",
            "github": "https://www.github.com",
            "chatgpt": "https://chat.openai.com",
            "google": "https://www.google.com",
            "instagram": "https://www.instagram.com",
            "whatsapp": "https://web.whatsapp.com",
            "gemini": "https://gemini.google.com"
        }

    @property
    def chrome_path(self):
        """Lazy: só busca o Chrome quando realmente necessário."""
        if not self._chrome_path_checked:
            self._chrome_path_checked = True
            caminhos = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
            ]
            for c in caminhos:
                if os.path.exists(c):
                    self._chrome_path = c
                    break
        return self._chrome_path

    def _cdp_disponivel(self) -> bool:
        """Verifica se o Chrome com debug remoto está rodando."""
        try:
            import urllib.request as _urllib
            with _urllib.urlopen(f"{CDP_URL}/json/version", timeout=1) as r:
                return r.status == 200
        except Exception:
            return False

    async def open_chrome_cdp(self, url: str = "about:blank"):
        # OTIMIZADO: Playwright importado apenas quando o CDP está disponível
        if not self.chrome_path:
            webbrowser.open(url)
            return False

        if self._cdp_disponivel():
            try:
                from playwright.async_api import async_playwright
                async with async_playwright() as p:
                    browser = await p.chromium.connect_over_cdp(CDP_URL)
                    page = await browser.contexts[0].new_page()
                    await page.goto(url)
                return True
            except Exception:
                pass

        subprocess.Popen([self.chrome_path, "--remote-debugging-port=9222", url])
        await asyncio.sleep(2.5)
        return self._cdp_disponivel()

    async def search_web(self, params: dict):
        consulta = params.get("consulta")
        tipo = params.get("tipo", "google")
        if not consulta:
            return "Erro: Parâmetro 'consulta' é obrigatório."
        try:
            if tipo.lower() == "youtube":
                url = f"https://www.youtube.com/results?search_query={quote_plus(consulta)}"
                await self.open_chrome_cdp(url)
                logger.info(f"[AUTOMATION] Action: web.search_web | Youtube: {consulta}")
                return f"Buscando '{consulta}' no YouTube."
            elif tipo.lower() == "url":
                await self.open_chrome_cdp(consulta)
                logger.info(f"[AUTOMATION] Action: web.search_web | URL: {consulta}")
                return f"Abrindo: {consulta}"
            else:  # google
                url = f"https://www.google.com/search?q={quote_plus(consulta)}"
                await self.open_chrome_cdp(url)
                logger.info(f"[AUTOMATION] Action: web.search_web | Google: {consulta}")
                return f"Pesquisando '{consulta}' no Google."
        except Exception as e:
            logger.error(f"[AUTOMATION] Error in web.search_web: {str(e)}")
            return f"Erro na pesquisa web: {e}"

    async def open_shortcut(self, params: dict):
        site = params.get("site")
        if not site:
            return "Erro: Parâmetro 'site' é obrigatório."
        try:
            url = self.shortcuts.get(site.lower())
            if url:
                await self.open_chrome_cdp(url)
                logger.info(f"[AUTOMATION] Action: web.open_shortcut | Site: {site}")
                return f"Abrindo {site}."
            return f"Site '{site}' não cadastrado nos atalhos."
        except Exception as e:
            logger.error(f"[AUTOMATION] Error in web.open_shortcut: {str(e)}")
            return f"Erro ao abrir atalho web: {e}"

    async def media_control(self, params: dict):
        """Pausa/retoma mídia — tenta janela do YouTube primeiro, depois CDP."""
        try:
            try:
                import pygetwindow as gw
                import pyautogui
                import time
                janelas_yt = [w for w in gw.getAllWindows()
                              if "youtube" in w.title.lower() and w.visible]
                if janelas_yt:
                    janelas_yt[0].activate()
                    time.sleep(0.4)
                    pyautogui.press("k")
                    logger.info("[AUTOMATION] Action: web.media_control | YouTube Play/Pause via Keyboard")
                    return "Play/Pause alternado no YouTube ✓"
            except ImportError:
                pass

            if self._cdp_disponivel():
                try:
                    from playwright.async_api import async_playwright
                    async with async_playwright() as p:
                        browser = await p.chromium.connect_over_cdp(CDP_URL)
                        for ctx in browser.contexts:
                            for page in ctx.pages:
                                if "youtube.com/watch" in page.url:
                                    await page.evaluate(
                                        "const v = document.querySelector('video'); if(v) { v.paused ? v.play() : v.pause(); }"
                                    )
                                    logger.info("[AUTOMATION] Action: web.media_control | YouTube Play/Pause via CDP")
                                    return "Play/Pause alternado via CDP ✓"
                    return "Nenhum vídeo do YouTube encontrado no Chrome."
                except Exception:
                    pass

            return "Não foi possível controlar a mídia. Abra o YouTube no Chrome primeiro."
        except Exception as e:
            logger.error(f"[AUTOMATION] Error in web.media_control: {str(e)}")
            return f"Erro no controle de mídia: {e}"
