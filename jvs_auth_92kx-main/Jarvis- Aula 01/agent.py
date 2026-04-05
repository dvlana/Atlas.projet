# -*- coding: utf-8 -*-
"""
agent.py — Orquestrador principal do Jarvis (LiveKit Agent).

OTIMIZAÇÕES APLICADAS:
  - Encoding UTF-8 explícito (fix de acentuação no terminal Windows)
  - stdout/stderr configurados para UTF-8 antes de qualquer import
  - Logging com filtro INFO (sem DEBUG de bibliotecas externas)
  - Bio-Claps com encerramento limpo no shutdown hook
"""
import sys
import io

# ENCODING FIX: Garante UTF-8 no terminal Windows (fix de acentuação em prints)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

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
from typing import Optional

# REFACTORED: Centralized Automation Nucleus
from automacao_jarvis import JarvisControl

load_dotenv()

# Logging configurado: INFO para o nosso código, WARNING para libs externas
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)],
)
# Reduz ruído de libs externas no log
for _noisy_lib in ('httpx', 'httpcore', 'livekit', 'urllib3', 'asyncio'):
    logging.getLogger(_noisy_lib).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────
# AGENTE (ASSISTENTE)
# ─────────────────────────────────────────

class Assistant(Agent, llm.ToolContext):
    def __init__(self, chat_ctx: Optional[ChatContext] = None):
        llm.ToolContext.__init__(self, [])
        super().__init__(
            instructions=AGENT_INSTRUCTION,
            llm=google.beta.realtime.RealtimeModel(
                voice="Charon",
                temperature=0.6,
            ),
            chat_ctx=chat_ctx,
        )
        # NÚCLEO CENTRAL DE AUTOMAÇÃO
        self.jarvis_control = JarvisControl()

    # ────────────────────────────────
    # MÍDIA E WEB (VIA CONTROLADOR)
    # ────────────────────────────────

    @agents.function_tool
    async def pesquisar_na_web(self, consulta: str, tipo: str = "google"):
        """Busca no Google, YouTube ou abre uma URL."""
        return await self.jarvis_control.controller.run_event("web.search_web", {"consulta": consulta, "tipo": tipo})

    @agents.function_tool
    async def atalhos_navegacao(self, site: str):
        """Abre sites populares por nome (ex: 'youtube', 'github', 'chatgpt')."""
        return await self.jarvis_control.controller.run_event("web.open_shortcut", {"site": site})

    @agents.function_tool
    async def pausar_retomar_youtube(self):
        """Pausa ou retoma o vídeo do YouTube que estiver tocando."""
        return await self.jarvis_control.controller.run_event("web.media_control", {})

    @agents.function_tool
    async def fechar_programa(self, programa: str):
        """Fecha um programa pelo nome (ex: 'chrome', 'notepad')."""
        import subprocess
        exe = programa if programa.lower().endswith(".exe") else f"{programa}.exe"
        res = subprocess.run(["taskkill", "/f", "/im", exe], capture_output=True)
        if res.returncode == 0:
            return f"Programa '{programa}' fechado com sucesso."
        return f"Não foi possível fechar '{programa}'."

    # ────────────────────────────────
    # ARQUIVOS E PASTAS (VIA CONTROLADOR)
    # ────────────────────────────────

    @agents.function_tool
    async def criar_pasta(self, caminho: str):
        """Cria uma pasta na Área de Trabalho ou subpastas."""
        return await self.jarvis_control.controller.run_event("file.create_folder", {"caminho": caminho})

    @agents.function_tool
    async def deletar_item(self, caminho: str):
        """Deleta um arquivo ou pasta."""
        return await self.jarvis_control.controller.run_event("file.delete_item", {"caminho": caminho})

    @agents.function_tool
    async def abrir_pasta(self, nome_pasta: str):
        """Abre uma pasta pelo nome."""
        return await self.jarvis_control.controller.run_event("file.open_folder", {"nome_pasta": nome_pasta})

    # ────────────────────────────────
    # SISTEMA (VIA CONTROLADOR)
    # ────────────────────────────────

    @agents.function_tool
    async def controle_volume(self, nivel: int):
        """Ajusta o volume do sistema de 0 a 100."""
        return await self.jarvis_control.controller.run_event("system.set_volume", {"nivel": nivel})

    @agents.function_tool
    async def controle_brilho(self, nivel: int):
        """Ajusta o brilho da tela de 0 a 100."""
        return await self.jarvis_control.controller.run_event("system.set_brightness", {"nivel": nivel})

    @agents.function_tool
    async def energia_pc(self, acao: str):
        """Controle de energia: 'desligar', 'reiniciar', 'bloquear'."""
        return await self.jarvis_control.controller.run_event("system.power_action", {"acao": acao})

    @agents.function_tool
    async def abrir_aplicativo(self, nome_app: str):
        """Abre aplicativos conhecidos pelo nome."""
        return await self.jarvis_control.controller.run_event("system.open_app", {"nome_app": nome_app})

    # ────────────────────────────────
    # CONTROLE DE MOUSE (VIA UI)
    # ────────────────────────────────

    @agents.function_tool
    async def clicar_na_tela(self, x: int, y: int, botao: str = "left", cliques: int = 1):
        """Clica em uma posição específica da tela pelas coordenadas X e Y."""
        return await self.jarvis_control.controller.run_event("ui.click", {"x": x, "y": y, "botao": botao, "cliques": cliques})

    @agents.function_tool
    async def duplo_clique(self, x: int, y: int):
        """Realiza duplo clique em uma posição (x, y) da tela."""
        return await self.jarvis_control.controller.run_event("ui.double_click", {"x": x, "y": y})

    @agents.function_tool
    async def clique_direito(self, x: int, y: int):
        """Clica com o botão direito do mouse em uma posição (x, y)."""
        return await self.jarvis_control.controller.run_event("ui.right_click", {"x": x, "y": y})

    @agents.function_tool
    async def mover_mouse(self, x: int, y: int):
        """Move o cursor do mouse para uma posição (x, y) sem clicar."""
        return await self.jarvis_control.controller.run_event("ui.move_mouse", {"x": x, "y": y})

    @agents.function_tool
    async def rolar_tela(self, clicks: int, x: int = None, y: int = None):
        """Rola a roda do mouse. Use clicks positivo para cima e negativo para baixo."""
        params = {"clicks": clicks}
        if x is not None: params["x"] = x
        if y is not None: params["y"] = y
        return await self.jarvis_control.controller.run_event("ui.scroll", params)

    @agents.function_tool
    async def arrastar_e_soltar(self, x1: int, y1: int, x2: int, y2: int):
        """Arrasta o mouse de uma posição (x1, y1) até outra (x2, y2)."""
        return await self.jarvis_control.controller.run_event("ui.drag_and_drop", {"x1": x1, "y1": y1, "x2": x2, "y2": y2})

    # ────────────────────────────────
    # CONTROLE DE TECLADO (VIA UI)
    # ────────────────────────────────

    @agents.function_tool
    async def digitar_texto(self, texto: str):
        """Digita um texto na janela ou campo atualmente focado."""
        return await self.jarvis_control.controller.run_event("ui.type_text", {"texto": texto})

    @agents.function_tool
    async def pressionar_tecla(self, tecla: str):
        """Pressiona uma tecla do teclado (ex: 'enter', 'esc', 'tab', 'delete', 'F5')."""
        return await self.jarvis_control.controller.run_event("ui.press_key", {"tecla": tecla})

    @agents.function_tool
    async def executar_atalho(self, atalho: str):
        """Executa um atalho de teclado como 'ctrl+c', 'alt+F4', 'ctrl+shift+esc', 'win+d'."""
        return await self.jarvis_control.controller.run_event("ui.hotkey", {"atalho": atalho})

    @agents.function_tool
    async def segurar_tecla(self, tecla: str, segundos: float = 1.0):
        """Mantém uma tecla pressionada por X segundos."""
        return await self.jarvis_control.controller.run_event("ui.hold_key", {"tecla": tecla, "segundos": segundos})

    # ────────────────────────────────
    # CONTROLE DE JANELAS (VIA UI)
    # ────────────────────────────────

    @agents.function_tool
    async def focar_janela(self, titulo: str):
        """Traz uma janela para o foco/frente pelo título (ou parte do título)."""
        return await self.jarvis_control.controller.run_event("ui.focus_window", {"titulo": titulo})

    @agents.function_tool
    async def minimizar_janela(self, titulo: str):
        """Minimiza uma janela pelo título."""
        return await self.jarvis_control.controller.run_event("ui.minimize_window", {"titulo": titulo})

    @agents.function_tool
    async def maximizar_janela(self, titulo: str):
        """Maximiza uma janela pelo título."""
        return await self.jarvis_control.controller.run_event("ui.maximize_window", {"titulo": titulo})

    @agents.function_tool
    async def fechar_janela_por_titulo(self, titulo: str):
        """Fecha uma janela específica pelo título."""
        return await self.jarvis_control.controller.run_event("ui.close_window", {"titulo": titulo})

    @agents.function_tool
    async def listar_janelas(self):
        """Lista todas as janelas abertas no sistema operacional no momento."""
        return await self.jarvis_control.controller.run_event("ui.list_windows", {})

    # ────────────────────────────────
    # SCREENSHOT E VISÃO
    # ────────────────────────────────

    @agents.function_tool
    async def tirar_screenshot(self, caminho: str = None):
        """Tira um print da tela e salva em um arquivo. Retorna o caminho do arquivo salvo."""
        params = {}
        if caminho:
            params["caminho"] = caminho
        return await self.jarvis_control.controller.run_event("ui.screenshot", params)

    @agents.function_tool
    async def obter_resolucao_tela(self):
        """Retorna a resolução atual da tela em pixels (largura x altura)."""
        return await self.jarvis_control.controller.run_event("ui.screen_size", {})

    @agents.function_tool
    async def posicao_atual_mouse(self):
        """Retorna as coordenadas X e Y atuais do cursor do mouse."""
        return await self.jarvis_control.controller.run_event("ui.mouse_position", {})

    # ────────────────────────────────
    # PERMISSÕES E INTERAÇÃO AVANÇADA
    # ────────────────────────────────

    @agents.function_tool
    async def aceitar_permissao_uac(self):
        """Detecta e aceita automaticamente um prompt de permissão UAC do Windows."""
        return await self.jarvis_control.controller.run_event("ui.accept_uac", {})

    @agents.function_tool
    async def clicar_botao_em_janela(self, janela: str, botao: str):
        """Clica em um botão pelo nome dentro de uma janela específica, sem precisar das coordenadas."""
        return await self.jarvis_control.controller.run_event("ui.click_button", {"janela": janela, "botao": botao})

    @agents.function_tool
    async def preencher_campo_em_janela(self, janela: str, campo: str, texto: str):
        """Preenche um campo de texto dentro de uma janela específica pelo nome do campo."""
        return await self.jarvis_control.controller.run_event("ui.fill_field", {"janela": janela, "campo": campo, "texto": texto})

    @agents.function_tool
    async def executar_como_admin(self, programa: str, argumentos: str = ""):
        """Executa um programa com privilégios de administrador (abre o prompt UAC)."""
        return await self.jarvis_control.controller.run_event("ui.run_as_admin", {"programa": programa, "argumentos": argumentos})

    # ────────────────────────────────
    # CLIPBOARD
    # ────────────────────────────────

    @agents.function_tool
    async def copiar_texto(self, texto: str):
        """Copia um texto para a área de transferência (clipboard)."""
        return await self.jarvis_control.controller.run_event("ui.clipboard_copy", {"texto": texto})

    @agents.function_tool
    async def colar_clipboard(self):
        """Cola o conteúdo da área de transferência na janela atualmente focada."""
        return await self.jarvis_control.controller.run_event("ui.clipboard_paste", {})

    @agents.function_tool
    async def aguardar(self, segundos: float):
        """Aguarda um número de segundos antes de executar o próximo comando (útil para esperar carregamentos)."""
        return await self.jarvis_control.controller.run_event("ui.wait", {"segundos": segundos})


# ─────────────────────────────────────────
# ENTRYPOINT (GERENCIAMENTO DE CONEXÃO)
# ─────────────────────────────────────────

async def entrypoint(ctx: agents.JobContext):

    

    mem0_client = AsyncMemoryClient()
    user_id = "PedroLucas"

    await ctx.connect()

    session = AgentSession()
    agent = Assistant(chat_ctx=ChatContext())

    # ── Iniciar Bio-Claps (Sempre Ativo) ─────────────────
    try:
        loop = asyncio.get_running_loop()
        agent.jarvis_control.start_bio_claps(loop)
    except Exception as e:
        logger.error(f"[AUDIO] Erro ao iniciar bio-claps: {e}")

    await session.start(
        room=ctx.room,
        agent=agent,
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # ── HANDLER DE EVENTOS DATA CHANNEL (PADRONIZADO CATEGORIA.ACAO) ─────────
    @ctx.room.on("data_received")
    def on_data_received(data: bytes, participant, kind):
        try:
            payload = json.loads(data.decode("utf-8"))
            if payload.get("type") == "automation_event":
                event = payload.get("event")
                params = payload.get("params", {})
                logger.info(f"[AUTOMATION] DataChannel Event: {event} | Params: {params}")
                
                # Executa a automação no controlador central de forma assíncrona
                asyncio.create_task(agent.jarvis_control.controller.run_event(event, params))
        except Exception as e:
            logger.error(f"[DataChannel] Error: {e}")

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

    # ── Salvar Memória e Encerrar Recursos ao Desligar ──────────────────────
    async def shutdown_hook():
        # Encerra Bio-Claps de forma limpa (evita orphan threads)
        try:
            agent.jarvis_control.stop_bio_claps()
            logger.info("[AUDIO] Bio-Claps encerrado no shutdown.")
        except Exception as e:
            logger.warning(f"[AUDIO] Erro ao encerrar Bio-Claps: {e}")

        try:
            msgs = []
            if session._agent and hasattr(session._agent, 'chat_ctx') and session._agent.chat_ctx:
                for item in session._agent.chat_ctx.items:
                    if not hasattr(item, "role"): continue
                    role = getattr(item, "role", None)
                    if role not in ("user", "assistant"): continue
                    content = getattr(item, "content", None)
                    if not content: continue
                    conteudo = "".join(content) if isinstance(content, list) else str(content)
                    conteudo = conteudo.strip()
                    if conteudo: msgs.append({"role": role, "content": conteudo})
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
