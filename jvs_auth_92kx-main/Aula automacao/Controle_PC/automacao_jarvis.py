from file_automation import FileAutomation
from system_automation import SystemAutomation
from web_automation import WebAutomation

class JarvisControl:
    """
    Controlador Central de Automações (Backend).
    Reorganizado em módulos para escalabilidade e clareza.
    """
    def __init__(self):
        self.files = FileAutomation()
        self.system = SystemAutomation()
        self.web = WebAutomation()

    # --- Métodos de Arquivos (Proxy vindo de FileAutomation) ---
    def cria_pasta(self, caminho):
        return self.files.cria_pasta(caminho)

    def abrir_pasta(self, nome_pasta):
        return self.files.abrir_pasta(nome_pasta)

    def buscar_e_abrir_arquivo(self, nome_arquivo):
        return self.files.buscar_e_abrir_arquivo(nome_arquivo)

    def deletar_arquivo(self, caminho):
        return self.files.deletar_item(caminho)

    def mover_item(self, origem, destino):
        return self.files.mover_item(origem, destino)

    def copiar_item(self, origem, destino):
        return self.files.copiar_item(origem, destino)

    def renomear_item(self, caminho, novo_nome):
        return self.files.renomear_item(caminho, novo_nome)

    def organizar_pasta(self, caminho):
        return self.files.organizar_pasta(caminho)

    def compactar_pasta(self, caminho):
        return self.files.compactar_pasta(caminho)

    # --- Métodos de Sistema (Proxy vindo de SystemAutomation) ---
    def controle_volume(self, nivel):
        return self.system.controle_volume(nivel)

    def controle_brilho(self, nivel):
        return self.system.controle_brilho(nivel)

    def abrir_aplicativo(self, nome_app):
        return self.system.abrir_aplicativo(nome_app)

    def energia_pc(self, acao):
        return self.system.energia_pc(acao)

    # --- Métodos de Web (Proxy vindo de WebAutomation) ---
    async def pesquisar_na_web(self, consulta: str, tipo: str = "google"):
        return await self.web.pesquisar_na_web(consulta, tipo)

    async def pausar_retomar_youtube(self):
        return await self.web.pausar_retomar_youtube()

    async def atalhos_navegacao(self, site: str):
        return await self.web.abrir_site(site)

    # --- Handler Central para Eventos da Interface ---
    async def processar_evento(self, evento: str, params: dict = None):
        """
        Recebe eventos da interface (clique, comando, gesto) e executa a ação.
        """
        params = params or {}
        print(f"[JarvisControl] Processando evento: {evento} com params: {params}")

        # MAPEAMENTO DE EVENTOS PARA AÇÕES
        try:
            if evento == "abrir_app":
                return self.abrir_aplicativo(params.get("nome_app"))
            elif evento == "ajuste_volume":
                return self.controle_volume(params.get("nivel", 50))
            elif evento == "ajuste_brilho":
                return self.controle_brilho(params.get("nivel", 50))
            elif evento == "media_play_pause":
                return await self.pausar_retomar_youtube()
            elif evento == "pesquisa_web":
                return await self.pesquisar_na_web(params.get("consulta"), params.get("tipo", "google"))
            elif evento == "abrir_site":
                return await self.atalhos_navegacao(params.get("site"))
            elif evento == "energia":
                return self.energia_pc(params.get("acao"))
            elif evento == "abrir_pasta":
                return self.abrir_pasta(params.get("nome_pasta"))
            else:
                return f"Evento desconhecido: {evento}"
        except Exception as e:
            return f"Erro ao processar evento backend: {str(e)}"
