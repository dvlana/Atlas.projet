import os
import subprocess
import screen_brightness_control as sbc
from pycaw.pycaw import AudioUtilities

class SystemAutomation:
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

    def controle_volume(self, nivel):
        try:
            nivel = max(0, min(100, int(nivel)))
            import comtypes
            comtypes.CoInitialize()
            devices = AudioUtilities.GetSpeakers()
            volume = devices.EndpointVolume
            volume.SetMasterVolumeLevelScalar(nivel / 100, None)
            return f"Volume ajustado para {nivel}%."
        except Exception as e:
            return f"Erro ao ajustar volume: {str(e)}"

    def controle_brilho(self, nivel):
        try:
            nivel = max(0, min(100, int(nivel)))
            sbc.set_brightness(nivel)
            return f"Brilho ajustado para {nivel}%."
        except Exception as e:
            return f"Erro ao ajustar brilho: {str(e)}"

    def abrir_aplicativo(self, nome_app):
        try:
            comando = self.apps.get(nome_app.lower())
            if comando:
                if comando.startswith("start "):
                    executavel = comando.replace("start ", "", 1).strip()
                    try: os.startfile(executavel)
                    except: subprocess.Popen(['cmd', '/c', 'start', '', executavel], shell=True)
                else:
                    subprocess.Popen(comando, shell=False)
                return f"Abrindo {nome_app}."
            else:
                try: os.startfile(nome_app)
                except: subprocess.Popen(['cmd', '/c', 'start', '', nome_app], shell=True)
                return f"Tentando abrir {nome_app}."
        except Exception as e:
            return f"Erro ao abrir aplicativo: {str(e)}"

    def energia_pc(self, acao):
        try:
            if acao == "desligar":
                os.system("shutdown /s /t 1")
                return "Desligando o computador."
            elif acao == "reiniciar":
                os.system("shutdown /r /t 1")
                return "Reiniciando o computador."
            elif acao == "bloquear":
                import subprocess
                subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
                return "Computador bloqueado."
            return "Ação inválida."
        except Exception as e:
            return f"Erro: {str(e)}"
