# -*- coding: utf-8 -*-
"""
Skill: debounce_decorator
==========================
Decorator que impede chamadas repetidas de uma função dentro de janela de tempo.

Skill ID  : skill_debounce_decorator
Categoria : control_flow
Versão    : 1
Extraída de: _sistema/utils/utils.py
"""

import time
import functools
import threading
import logging
from typing import Callable, Any

logger = logging.getLogger("Origem.Skills.Debounce")

SKILL_META = {
    "id": "skill_debounce_decorator",
    "name": "debounce_decorator",
    "version": 1,
    "category": "control_flow",
}

_timers: dict[str, float] = {}
_lock = threading.Lock()


def debounce(ttl_seconds: float = 1.0, return_on_block=None):
    """
    Decorator: impede que a função seja chamada mais de uma vez
    dentro da janela de tempo.

    Args:
        ttl_seconds:    Janela de tempo em segundos
        return_on_block: Valor retornado quando bloqueado (default: None)

    Uso:
        @debounce(ttl_seconds=2.0)
        def disparar_acao():
            open_app("spotify")

        @debounce(ttl_seconds=0.5, return_on_block="modo cooldown")
        def processar_clap():
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> Any:
            nome = fn.__qualname__
            with _lock:
                ultimo = _timers.get(nome, 0.0)
                agora = time.monotonic()
                elapsed = agora - ultimo
                if elapsed < ttl_seconds:
                    logger.debug(
                        f"[DEBOUNCE] '{nome}' bloqueado "
                        f"({elapsed:.3f}s < {ttl_seconds}s)"
                    )
                    return return_on_block
                _timers[nome] = agora

            return fn(*args, **kwargs)
        return wrapper
    return decorator


def debounce_fn(fn: Callable, ttl_seconds: float = 1.0, *args, **kwargs) -> Any:
    """
    Versão funcional do debounce (sem decorator).
    Útil quando não é possível decorar a função na definição.

    Uso:
        resultado = debounce_fn(minha_funcao, 2.0, arg1, arg2)
    """
    wrapped = debounce(ttl_seconds)(fn)
    return wrapped(*args, **kwargs)
