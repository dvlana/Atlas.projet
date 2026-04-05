import os
import asyncio
import webbrowser
import subprocess
import urllib.request as _urllib
from urllib.parse import quote_plus

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_DISPONIVEL = True
except ImportError:
    PLAYWRIGHT_DISPONIVEL = False

CDP_URL = "http://localhost:9222"

class WebAutomation:
    def __init__(self):
        self.chrome_path = self._get_chrome_path()
        self.shortcuts = {
            "youtube": "https://www.youtube.com",
            "github": "https://www.github.com",
            "chatgpt": "https://chat.openai.com",
            "google": "https://www.google.com",
            "instagram": "https://www.instagram.com",
            "whatsapp": "https://web.whatsapp.com",
            "gemini": "https://gemini.google.com"
        }

    def _get_chrome_path(self):
        caminhos = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
        for c in caminhos:
            if os.path.exists(c):
                return c
        return None

    def _cdp_disponivel(self) -> bool:
        try:
            with _urllib.urlopen(f"{CDP_URL}/json/version", timeout=1) as r:
                return r.status == 200
        except:
            return False

    async def abrir_chrome_com_cdp(self, url: str = "about:blank"):
        if not self.chrome_path:
            webbrowser.open(url)
            return False
        if self._cdp_disponivel():
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.connect_over_cdp(CDP_URL)
                    page = await browser.contexts[0].new_page()
                    await page.goto(url)
                    await browser.disconnect()
                return True
            except:
                pass
        subprocess.Popen([self.chrome_path, f"--remote-debugging-port=9222", url])
        await asyncio.sleep(2.5)
        return self._cdp_disponivel()

    async def abrir_site(self, site: str):
        url = self.shortcuts.get(site.lower())
        if url:
            await self.abrir_chrome_com_cdp(url)
            return f"Abrindo {site}."
        return f"Site '{site}' não cadastrado nos atalhos."

    async def pesquisar_na_web(self, consulta: str, tipo: str = "google"):
        try:
            if tipo.lower() == "youtube":
                url = f"https://www.youtube.com/results?search_query={quote_plus(consulta)}"
                await self.abrir_chrome_com_cdp(url)
                return f"Abrindo busca do YouTube por '{consulta}'."
            elif tipo.lower() == "url":
                await self.abrir_chrome_com_cdp(consulta)
                return f"Abrindo: {consulta}"
            else: # google
                url = f"https://www.google.com/search?q={quote_plus(consulta)}"
                await self.abrir_chrome_com_cdp(url)
                return f"Pesquisando '{consulta}' no Google."
        except Exception as e:
            return f"Erro na pesquisa: {e}"

    async def pausar_retomar_youtube(self):
        try:
            try:
                import pygetwindow as gw
                import pyautogui
                import time
                janelas_yt = [w for w in gw.getAllWindows()
                              if "youtube" in w.title.lower() and w.visible]
                if janelas_yt:
                    janela = janelas_yt[0]
                    janela.activate()
                    time.sleep(0.4)
                    pyautogui.press("k")
                    return "Play/Pause alternado no YouTube ✓"
            except ImportError:
                pass

            if PLAYWRIGHT_DISPONIVEL and self._cdp_disponivel():
                async with async_playwright() as p:
                    browser = await p.chromium.connect_over_cdp(CDP_URL)
                    for ctx in browser.contexts:
                        for page in ctx.pages:
                            if "youtube.com/watch" in page.url:
                                await page.evaluate(
                                    "const v = document.querySelector('video'); if(v) { v.paused ? v.play() : v.pause(); }"
                                )
                                await browser.disconnect()
                                return "Play/Pause alternado via CDP ✓"
                    await browser.disconnect()
                return "Nenhum vídeo do YouTube encontrado no Chrome."
            return "Não foi possível controlar o YouTube. Requisitos faltando."
        except Exception as e:
            return f"Erro no controle de mídia: {e}"
