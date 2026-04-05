# -*- coding: utf-8 -*-
"""
Skill: safe_run
================
Executa qualquer função com captura de erro padronizada e log estruturado.

Skill ID  : skill_safe_run
Categoria : error_handling
Versão    : 1
Extraída de: _sistema/utils/utils.py
"""

import logging
from typing import Callable, Any

logger = logging.getLogger("Origem.Skills.SafeRun")

SKILL_META = {
    "id": "skill_safe_run",
    "name": "safe_run",
    "version": 1,
    "category": "error_handling",
}


def safe_run(
    fn: Callable,
    *args,
    nome: str = None,
    fallback: Any = None,
    log_erro: bool = True,
    **kwargs,
) -> tuple[Any, Exception | None]:
    """
    Executa uma função com captura de erro padronizada.

    Args:
        fn:       Função a executar
        *args:    Argumentos posicionais
        nome:     Label para identificar no log (default: nome da função)
        fallback: Valor retornado em caso de erro (default: None)
        log_erro: Se True, loga o erro (default: True)
        **kwargs: Argumentos nomeados

    Returns:
        (resultado, None)    → em sucesso
        (fallback, exception) → em falha

    Uso:
        resultado, erro = safe_run(abrir_app, "spotify", nome="open_spotify")
        if erro:
            print(f"Falhou: {erro}")
        else:
            print(f"Resultado: {resultado}")
    """
    label = nome or getattr(fn, "__name__", "func")
    try:
        resultado = fn(*args, **kwargs)
        return resultado, None
    except Exception as e:
        if log_erro:
            logger.error(f"[SAFE-RUN] Erro em '{label}': {type(e).__name__}: {e}")
        return fallback, e


def safe_run_async_result(fn: Callable, *args, nome: str = None, **kwargs) -> Any:
    """
    Versão simplificada: executa e retorna resultado ou None em caso de erro.
    Útil quando o erro não precisa ser propagado mas deve ser logado.
    """
    resultado, _ = safe_run(fn, *args, nome=nome, **kwargs)
    return resultado
