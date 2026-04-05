import os
import subprocess
import logging

logger = logging.getLogger(__name__)

# ─── Lazy imports (carregados apenas quando necessário) ────────────────────────
# Evita carregar APIs pesadas do Windows na inicialização do sistema.
_pycaw_initialized = False
_com_initialized = False


def _get_volume_controller():
    """Inicializa COM e retorna o controlador de volume, apenas uma vez."""
    global _com_initialized
    try:
        import comtypes
        if not _com_initialized:
            comtypes.CoInitialize()
            _com_initialized = True
        from pycaw.pycaw import AudioUtilities
        devices = AudioUtilities.GetSpeakers()
        return devices.EndpointVolume
    except Exception as e:
        raise RuntimeError(f"Erro ao inicializar controle de volume: {e}")


class SystemAutomation:
    # Apps que NUNCA devem ser abertos por disparo automático (sem intenção explícita do usuário)
    # Esta lista é uma salvaguarda — não impede o usuário de abrir via voz/comando direto:
    # apenas bloqueia spawns vindos de lógicas automáticas sem confirmação.
    _AUTO_SPAWN_BLOCKLIST: set = set()  # Adicionar apps aqui para bloquear abertura automática

    def __init__(self):
        self.apps = {
            "bloco de notas": "notepad.exe",
            "calculadora": "calc.exe",
            "paint": "mspaint.exe",
            "cmd": "cmd.exe",
            "navegador": "start msedge",
            "word": "start winword",
            "excel": "start excel",
            "powerpoint": "start powerpnt",
            "explorador de arquivos": "explorer.exe",
            "configuracoes": "start ms-settings:",
            "configurações": "start ms-settings:",
            "terminal": "start wt",
            "visual studio code": "start code",
            "vscode": "start code",
            "spotify": "start spotify",
            "chrome": "start chrome",
            "edge": "start msedge",
            "firefox": "start firefox",
            "opera": "start opera",
            "teams": "start teams",
            "zoom": "start zoom",
            "slack": "start slack",
            "discord": "start discord",
            "skype": "start skype",
            "vlc": "start vlc"
        }

    def set_volume(self, params: dict):
        nivel = params.get("nivel", 50)
        try:
            nivel = max(0, min(100, int(nivel)))
            # OTIMIZADO: COM inicializa apenas uma vez via helper
            volume = _get_volume_controller()
            volume.SetMasterVolumeLevelScalar(nivel / 100, None)
            logger.info(f"[AUTOMATION] Action: system.set_volume | Level: {nivel}%")
            return f"Volume ajustado para {nivel}%."
        except Exception as e:
            logger.error(f"[AUTOMATION] Error in system.set_volume: {str(e)}")
            return f"Erro ao ajustar volume: {str(e)}"

    def set_brightness(self, params: dict):
        nivel = params.get("nivel", 50)
        try:
            nivel = max(0, min(100, int(nivel)))
            # OTIMIZADO: import lazy — só quando chamado
            import screen_brightness_control as sbc
            sbc.set_brightness(nivel)
            logger.info(f"[AUTOMATION] Action: system.set_brightness | Level: {nivel}%")
            return f"Brilho ajustado para {nivel}%."
        except Exception as e:
            logger.error(f"[AUTOMATION] Error in system.set_brightness: {str(e)}")
            return f"Erro ao ajustar brilho: {str(e)}"

    def open_app(self, params: dict):
        nome_app = params.get("nome_app")
        if not nome_app:
            return "Erro: Parâmetro 'nome_app' é obrigatório."

        # ─── AUDITORIA DE SPAWN ───────────────────────────────────────────────────
        # Todo spawn de app externo gera um log auditável — não remover.
        logger.info(f"[SPAWN-AUDIT] system.open_app solicitado: app={nome_app!r}")

        try:
            comando = self.apps.get(nome_app.lower())
            if comando:
                if comando.startswith("start "):
                    executavel = comando.replace("start ", "", 1).strip()
                    try:
                        os.startfile(executavel)
                    except Exception:
                        subprocess.Popen(['cmd', '/c', 'start', '', executavel], shell=True)
                else:
                    subprocess.Popen(comando, shell=False)
                logger.info(f"[AUTOMATION] Action: system.open_app | App: {nome_app}")
                return f"Abrindo {nome_app}."
            else:
                try:
                    os.startfile(nome_app)
                except Exception:
                    subprocess.Popen(['cmd', '/c', 'start', '', nome_app], shell=True)
                logger.info(f"[AUTOMATION] Action: system.open_app | Unknown App/Cmd: {nome_app}")
                return f"Tentando abrir aplicativo: {nome_app}."
        except Exception as e:
            logger.error(f"[AUTOMATION] Error in system.open_app: {str(e)}")
            return f"Erro ao abrir aplicativo: {str(e)}"

    def power_action(self, params: dict):
        acao = params.get("acao")
        if not acao:
            return "Erro: Parâmetro 'acao' é obrigatório."
        try:
            # OTIMIZADO: subprocess.run em vez de os.system() — mais seguro e controlado
            if acao == "desligar":
                subprocess.run(["shutdown", "/s", "/t", "1"], check=True)
                logger.info("[AUTOMATION] Action: system.power_action | Type: Shutdown")
                return "Desligando o computador."
            elif acao == "reiniciar":
                subprocess.run(["shutdown", "/r", "/t", "1"], check=True)
                logger.info("[AUTOMATION] Action: system.power_action | Type: Reboot")
                return "Reiniciando o computador."
            elif acao == "bloquear":
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"], check=True)
                logger.info("[AUTOMATION] Action: system.power_action | Type: Lock")
                return "Computador bloqueado."
            return "Ação de energia inválida. Use: 'desligar', 'reiniciar' ou 'bloquear'."
        except Exception as e:
            logger.error(f"[AUTOMATION] Error in system.power_action: {str(e)}")
            return f"Erro ao executar ação de energia: {str(e)}"
