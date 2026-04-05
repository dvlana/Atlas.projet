from dotenv import load_dotenv
from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, ChatContext, llm
from livekit.plugins import noise_cancellation, google
from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION
from mem0 import AsyncMemoryClient
import logging
import os
import asyncio
import json

# REFACTORED: Central Automation Controller
from automacao_jarvis import JarvisControl

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# AGENTE (ASSISTENTE)
# ─────────────────────────────────────────

class Assistant(Agent, llm.ToolContext):
    def __init__(self, chat_ctx: ChatContext = None):
        llm.ToolContext.__init__(self, [])
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice="Charon",
                temperature=0.6,
            ),
            chat_ctx=chat_ctx,
        )
        # REFACTORED: Centralizing controller
        self.jarvis_control = JarvisControl()

    # ────────────────────────────────
    # MÍDIA E WEB (REFACTORED)
    # ────────────────────────────────

    @agents.function_tool
    async def pesquisar_na_web(self, consulta: str, tipo: str = "google"):
        """
        Faz uma busca ou abre o YouTube.
        tipo = 'google' → busca no Google
        tipo = 'youtube' → abre a busca no YouTube (não inicia um vídeo automaticamente)
        tipo = 'url' → abre a URL diretamente
        """
        try:
            return await self.jarvis_control.pesquisar_na_web(consulta, tipo)
        except Exception as e:
            return f"Erro na pesquisa backend: {e}"

    @agents.function_tool
    async def pausar_retomar_youtube(self):
        """Pausa ou retoma o vídeo do YouTube que estiver tocando no Chrome."""
        try:
            return await self.jarvis_control.pausar_retomar_youtube()
        except Exception as e:
            return f"Erro no controle de mídia backend: {e}"

    @agents.function_tool
    async def atalhos_navegacao(self, site: str):
        """
        Abre sites populares por nome (ex: 'youtube', 'github', 'chatgpt', 'gemini', 'whatsapp').
        """
        return await self.jarvis_control.atalhos_navegacao(site)

    @agents.function_tool
    async def fechar_programa(self, programa: str):
        """Fecha um programa pelo nome (ex: 'chrome', 'notepad', 'spotify')."""
        import subprocess
        exe = programa if programa.lower().endswith(".exe") else f"{programa}.exe"
        res = subprocess.run(["taskkill", "/f", "/im", exe], capture_output=True)
        if res.returncode == 0:
            return f"Programa '{programa}' fechado com sucesso."
        return f"Não foi possível fechar '{programa}'. Verifique o nome do processo."

    @agents.function_tool
    async def abrir_programa(self, comando: str):
        """Abre um programa ou executável pelo nome ou caminho (ex: 'notepad', 'calc')."""
        try:
            import subprocess
            subprocess.Popen(comando, shell=True)
            return f"'{comando}' aberto."
        except Exception as e:
            return f"Erro ao abrir '{comando}': {e}"

    # ────────────────────────────────
    # ARQUIVOS E PASTAS (REFACTORED)
    # ────────────────────────────────

    @agents.function_tool
    async def criar_pasta(self, caminho: str):
        """Cria uma pasta. Ex: 'Projetos' na Área de Trabalho."""
        return self.jarvis_control.cria_pasta(caminho)

    @agents.function_tool
    async def deletar_item(self, caminho: str):
        """Deleta um arquivo ou pasta pelo nome ou caminho."""
        return self.jarvis_control.deletar_arquivo(caminho)

    @agents.function_tool
    async def mover_item(self, origem: str, destino: str):
        """Move um arquivo ou pasta de origem para destino."""
        return self.jarvis_control.mover_item(origem, destino)

    @agents.function_tool
    async def copiar_item(self, origem: str, destino: str):
        """Copia um arquivo ou pasta para um novo local."""
        return self.jarvis_control.copiar_item(origem, destino)

    @agents.function_tool
    async def renomear_item(self, caminho: str, novo_nome: str):
        """Renomeia um arquivo ou pasta."""
        return self.jarvis_control.renomear_item(caminho, novo_nome)

    @agents.function_tool
    async def organizar_pasta(self, caminho: str):
        """Organiza os arquivos de uma pasta por tipo (Imagens, Documentos, etc.)."""
        return self.jarvis_control.organizar_pasta(caminho)

    @agents.function_tool
    async def compactar_pasta(self, caminho: str):
        """Compacta uma pasta em um arquivo .zip."""
        return self.jarvis_control.compactar_pasta(caminho)

    @agents.function_tool
    async def abrir_pasta(self, nome_pasta: str):
        """Abre uma pasta no Explorador de Arquivos pelo nome."""
        return self.jarvis_control.abrir_pasta(nome_pasta)

    @agents.function_tool
    async def buscar_e_abrir_arquivo(self, nome_arquivo: str):
        """Busca um arquivo por nome e o abre automaticamente."""
        return self.jarvis_control.buscar_e_abrir_arquivo(nome_arquivo)

    # ────────────────────────────────
    # SISTEMA (REFACTORED)
    # ────────────────────────────────

    @agents.function_tool
    async def controle_volume(self, nivel: int):
        """Ajusta o volume do sistema de 0 a 100."""
        return self.jarvis_control.controle_volume(nivel)

    @agents.function_tool
    async def controle_brilho(self, nivel: int):
        """Ajusta o brilho da tela de 0 a 100."""
        return self.jarvis_control.controle_brilho(nivel)

    @agents.function_tool
    async def energia_pc(self, acao: str):
        """Controla a energia do PC. Ações: 'desligar', 'reiniciar', 'bloquear'."""
        return self.jarvis_control.energia_pc(acao)

    @agents.function_tool
    async def abrir_aplicativo(self, nome_app: str):
        """Abre aplicativos conhecidos pelo nome."""
        return self.jarvis_control.abrir_aplicativo(nome_app)


# ─────────────────────────────────────────
# ENTRYPOINT (GERENCIAMENTO DE CONEXÃO E EVENTOS)
# ─────────────────────────────────────────

async def entrypoint(ctx: agents.JobContext):

    mem0_client = AsyncMemoryClient()
    user_id = "PedroLucas"

    await ctx.connect()

    session = AgentSession()
    agent = Assistant(chat_ctx=ChatContext())

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # ── HANDLER DE EVENTOS DATA CHANNEL (INTERFACE -> BACKEND) ─────────────────
    @ctx.room.on("data_received")
    def on_data_received(data: bytes, participant, kind):
        try:
            payload = json.loads(data.decode("utf-8"))
            if payload.get("type") == "automation_event":
                evento = payload.get("event")
                params = payload.get("params", {})
                logger.info(f"[DataChannel] Recebido evento da interface: {evento} params: {params}")
                
                # Executa a automação correspondente no controlador central
                # Usar call_soon_threadsafe ou similar se necessário, mas aqui estamos em asyncio
                asyncio.create_task(agent.jarvis_control.processar_evento(evento, params))
        except Exception as e:
            logger.error(f"[DataChannel] Erro ao processar mensagem: {e}")

    # ── Carregar Memória de Longo Prazo ─────────────────
    try:
        logger.info(f"[Mem0] Carregando memórias para '{user_id}'...")
        response = await mem0_client.search(
            query="histórico, preferências e informações pessoais do usuário",
            filters={"user_id": user_id},
            limit=20,
        )
        if isinstance(response, dict):
            results = response.get("results", [])
        elif isinstance(response, list):
            results = response
        else:
            results = []

        logger.info(f"[Mem0] {len(results)} memórias encontradas.")

        if results:
            memorias = []
            for r in results:
                texto = None
                if isinstance(r, dict):
                    texto = r.get("memory") or r.get("text") or r.get("content")
                if texto:
                    memorias.append(f"- {texto}")

            if memorias:
                bloco = "\n".join(memorias)
                ctx_copia = agent.chat_ctx.copy()
                ctx_copia.add_message(
                    role="assistant",
                    content=f"[Memória carregada — informações sobre o usuário]\n{bloco}"
                )
                await agent.update_chat_ctx(ctx_copia)
                logger.info(f"[Mem0] {len(memorias)} memórias injetadas no contexto.")
    except Exception as e:
        logger.error(f"[Mem0] Erro ao carregar memória: {e}")

    # ── Salvar Memória ao Desligar ───────────────────────
    async def shutdown_hook():
        try:
            msgs = []
            for item in session._agent.chat_ctx.items:
                if not hasattr(item, "content") or not item.content:
                    continue
                if item.role not in ("user", "assistant"):
                    continue
                conteudo = "".join(item.content) if isinstance(item.content, list) else str(item.content)
                conteudo = conteudo.strip()
                if conteudo:
                    msgs.append({"role": item.role, "content": conteudo})
            if msgs:
                await mem0_client.add(msgs, user_id=user_id)
                logger.info(f"[Mem0] {len(msgs)} mensagens salvas na memória.")
        except Exception as e:
            logger.warning(f"[Mem0] Erro ao salvar memória: {e}")

    ctx.add_shutdown_callback(shutdown_hook)

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION + "\nCumprimente o usuário de forma natural e confiante."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
