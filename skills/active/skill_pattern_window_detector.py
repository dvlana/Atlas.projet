# -*- coding: utf-8 -*-
"""
Skill: pattern_window_detector
================================
Detecta padrão de N eventos dentro de uma janela de tempo usando buffer deque.

Skill ID  : skill_pattern_window_detector
Categoria : pattern_detection
Versão    : 1
Extraída de: jvs_auth_92kx-main/Jarvis- Aula 01/automation/clap_detector.py
"""

import time
from collections import deque

SKILL_META = {
    "id": "skill_pattern_window_detector",
    "name": "pattern_window_detector",
    "version": 1,
    "category": "pattern_detection",
}


def limpar_janela(timestamps: deque, window_seconds: float) -> deque:
    """
    Remove timestamps fora da janela de tempo atual.
    Opera diretamente na deque (in-place, O(k) onde k é número de itens antigos).

    Args:
        timestamps:     deque de floats (time.monotonic())
        window_seconds: janela de tempo em segundos

    Returns:
        deque atualizada (mesmo objeto, modificado in-place)
    """
    agora = time.monotonic()
    while timestamps and (agora - timestamps[0]) > window_seconds:
        timestamps.popleft()
    return timestamps


def detectar_padrao(
    timestamps: deque,
    window_seconds: float = 1.0,
    min_count: int = 2,
) -> bool:
    """
    Verifica se há N ou mais eventos dentro da janela de tempo.

    Args:
        timestamps:     deque com timestamps de eventos (time.monotonic())
        window_seconds: Janela de tempo retroativa para análise
        min_count:      Número mínimo de eventos para confirmação do padrão

    Returns:
        True se padrão confirmado (min_count+ eventos na janela)

    Uso típico (palmas, triggers, gestos):
        claps = deque(maxlen=20)
        # ... adiciona timestamps via callback ...
        if detectar_padrao(claps, window_seconds=1.0, min_count=2):
            disparar_acao()
            claps.clear()
    """
    limpar_janela(timestamps, window_seconds)
    return len(timestamps) >= min_count


def criar_buffer(maxlen: int = 20) -> deque:
    """
    Cria buffer de timestamps com tamanho máximo fixo.
    Tamanho fixo = sem crescimento ilimitado de memória.

    Args:
        maxlen: Número máximo de timestamps armazenados

    Returns:
        deque configurada e pronta para uso
    """
    return deque(maxlen=maxlen)
