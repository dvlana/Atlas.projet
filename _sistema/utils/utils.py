# -*- coding: utf-8 -*-
"""
Utils — Funções auxiliares do sistema Origem.1
===============================================
Coleção de utilitários compartilhados entre todos os módulos.

Funções disponíveis:
  - singleton_guard()    → impede execução duplicada de scripts
  - safe_run()           → executa função com tratamento de erro padronizado
  - dentro_de_origem()   → valida que um caminho está dentro de /Origem.1
  - limpar_temp()        → limpa pasta temp automaticamente
  - log_evento()         → registra evento estruturado no log central
"""

import os
import sys
import time
import logging
import functools
import threading
from pathlib import Path
from typing import Callable, Any

logger = logging.getLogger("Origem.Utils")

ROOT = Path(__file__).resolve().parent.parent.parent  # → /Origem.1
TEMP_DIR = ROOT / "_sistema" / "temp"
LOG_DIR = ROOT / "_sistema" / "logs"


# ─── SINGLETON GUARD ──────────────────────────────────────────────────────────

_singletons: dict[str, float] = {}
_singleton_lock = threading.Lock()


def singleton_guard(nome: str, ttl_seconds: float = 5.0) -> bool:
    """
    Verifica se uma operação com esse nome já está em execução.

    Retorna True se PODE prosseguir (singleton livre).
    Retorna False se JÁ está em execução dentro do TTL.

    Uso:
      if not singleton_guard("clap_trigger", ttl_seconds=2.0):
          return  # já está rodando, ignora
    """
    with _singleton_lock:
        ultimo = _singletons.get(nome, 0.0)
        agora = time.monotonic()
        if (agora - ultimo) < ttl_seconds:
            logger.debug(f"[SINGLETON] '{nome}' bloqueado (TTL={ttl_seconds}s, elapsed={agora-ultimo:.2f}s)")
            return False
        _singletons[nome] = agora
        return True


def debounce(ttl_seconds: float = 1.0):
    """
    Decorator: impede que uma função seja chamada mais de uma vez
    dentro da janela de tempo especificada.

    Uso:
      @debounce(ttl_seconds=2.0)
      def disparar_acao():
          ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            nome = fn.__qualname__
            if not singleton_guard(nome, ttl_seconds):
                logger.debug(f"[DEBOUNCE] '{nome}' ignorado (dentro do TTL).")
                return None
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ─── SAFE RUN ─────────────────────────────────────────────────────────────────

def safe_run(fn: Callable, *args, nome: str = None, **kwargs) -> tuple[Any, Exception | None]:
    """
    Executa uma função com captura de erro padronizada.
    Retorna (resultado, None) em sucesso ou (None, Exception) em falha.

    Uso:
      resultado, erro = safe_run(minha_funcao, arg1, nome="descricao")
      if erro:
          print(f"Falhou: {erro}")
    """
    label = nome or getattr(fn, "__name__", "func")
    try:
        resultado = fn(*args, **kwargs)
        return resultado, None
    except Exception as e:
        logger.error(f"[SAFE-RUN] Erro em '{label}': {e}")
        return None, e


# ─── VALIDAÇÃO DE CAMINHO ─────────────────────────────────────────────────────

def dentro_de_origem(caminho: str | Path) -> bool:
    """
    Verifica se um caminho está DENTRO de /Origem.1.
    Impede operações em caminhos externos à raiz do sistema.

    Uso:
      if not dentro_de_origem(novo_arquivo):
          raise ValueError("Caminho fora de /Origem.1 — proibido pelo sistema")
    """
    try:
        Path(caminho).resolve().relative_to(ROOT.resolve())
        return True
    except ValueError:
        logger.warning(f"[SEGURANÇA] Caminho fora de /Origem.1: {caminho}")
        return False


# ─── LIMPEZA DE TEMP ──────────────────────────────────────────────────────────

def limpar_temp(max_age_hours: float = 24.0) -> int:
    """
    Remove arquivos antigos da pasta /temp.
    Retorna número de arquivos removidos.
    """
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    removidos = 0
    limite = time.time() - (max_age_hours * 3600)

    for arquivo in TEMP_DIR.iterdir():
        if arquivo.is_file() and arquivo.stat().st_mtime < limite:
            try:
                arquivo.unlink()
                removidos += 1
                logger.debug(f"[TEMP] Removido arquivo antigo: {arquivo.name}")
            except Exception as e:
                logger.warning(f"[TEMP] Falha ao remover {arquivo.name}: {e}")

    if removidos:
        logger.info(f"[TEMP] {removidos} arquivo(s) temporário(s) removido(s).")
    return removidos


# ─── LOG DE EVENTO ESTRUTURADO ────────────────────────────────────────────────

def log_evento(categoria: str, acao: str, detalhes: dict = None) -> None:
    """
    Registra evento estruturado no log central.
    Formato: [CATEGORIA] acao | chave=valor ...

    Uso:
      log_evento("SPAWN", "open_app", {"app": "spotify", "caller": "voice"})
    """
    partes = [f"{k}={v!r}" for k, v in (detalhes or {}).items()]
    linha = f"[{categoria.upper()}] {acao}"
    if partes:
        linha += " | " + " | ".join(partes)
    logger.info(linha)
