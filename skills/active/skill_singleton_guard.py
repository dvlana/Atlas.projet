# -*- coding: utf-8 -*-
"""
Skill: singleton_guard
=======================
Impede execução duplicada de operações com TTL configurável.

Skill ID  : skill_singleton_guard
Categoria : control_flow
Versão    : 1
Extraída de: _sistema/utils/utils.py
"""

import time
import threading
import logging

logger = logging.getLogger("Origem.Skills.SingletonGuard")

SKILL_META = {
    "id": "skill_singleton_guard",
    "name": "singleton_guard",
    "version": 1,
    "category": "control_flow",
}

_registry: dict[str, float] = {}
_lock = threading.Lock()


def singleton_guard(nome: str, ttl_seconds: float = 5.0) -> bool:
    """
    Verifica se uma operação com esse nome já está em execução dentro do TTL.

    Thread-safe via Lock.

    Args:
        nome:        Identificador único da operação
        ttl_seconds: Janela de tempo em segundos para considerar "ainda executando"

    Returns:
        True  → livre para prosseguir (registra timestamp)
        False → bloqueado (já está dentro do TTL)

    Uso:
        if not singleton_guard("processar_audio", ttl_seconds=2.0):
            return   # já em execução, ignora
        # ... executa a operação
    """
    with _lock:
        ultimo = _registry.get(nome, 0.0)
        agora = time.monotonic()
        elapsed = agora - ultimo

        if elapsed < ttl_seconds:
            logger.debug(f"[SINGLETON] '{nome}' bloqueado | elapsed={elapsed:.3f}s < TTL={ttl_seconds}s")
            return False

        _registry[nome] = agora
        logger.debug(f"[SINGLETON] '{nome}' liberado | último há {elapsed:.2f}s")
        return True


def singleton_reset(nome: str) -> None:
    """Força reset do singleton para um nome específico (permite re-execução imediata)."""
    with _lock:
        _registry.pop(nome, None)
    logger.debug(f"[SINGLETON] '{nome}' resetado manualmente.")


def singleton_status() -> dict[str, float]:
    """Retorna timestamp de cada operação registrada (para diagnóstico)."""
    with _lock:
        agora = time.monotonic()
        return {nome: round(agora - ts, 2) for nome, ts in _registry.items()}
