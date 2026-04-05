# -*- coding: utf-8 -*-
"""
Skill: audio_rms_detector
==========================
Detecta picos de energia em stream de áudio usando RMS com filtro EMA de ruído ambiente.

Skill ID  : skill_audio_rms_detector
Categoria : audio
Versão    : 1
Extraída de: jvs_auth_92kx-main/Jarvis- Aula 01/automation/clap_detector.py
"""

import time
import numpy as np

SKILL_META = {
    "id": "skill_audio_rms_detector",
    "name": "audio_rms_detector",
    "version": 1,
    "category": "audio",
}


def calcular_rms(indata: np.ndarray, frames: int) -> float:
    """
    Calcula RMS (Root Mean Square) de um bloco de áudio mono.
    Usa np.dot para máxima eficiência (mais rápido que np.linalg.norm).

    Args:
        indata: Array de áudio (shape: [frames, channels])
        frames: Número de frames no bloco

    Returns:
        float — nível RMS do bloco
    """
    return float(np.sqrt(np.dot(indata[:, 0], indata[:, 0]) / frames))


def atualizar_ruido_ambiente(
    rms_atual: float,
    ruido_anterior: float,
    alpha: float = 0.03,
) -> float:
    """
    Atualiza estimativa de ruído ambiente com filtro EMA (Exponential Moving Average).

    Args:
        rms_atual:      RMS do bloco atual
        ruido_anterior: Nível de ruído estimado anteriormente
        alpha:          Fator de suavização (0.03 = atualiza lentamente)

    Returns:
        float — novo nível de ruído ambiente estimado
    """
    return (1.0 - alpha) * ruido_anterior + alpha * rms_atual


def detectar_pico(
    indata: np.ndarray,
    frames: int,
    threshold: float,
    ambient_noise: float,
    last_event_time: float,
    debounce_seconds: float = 0.25,
) -> tuple[bool, float, float]:
    """
    Detecta pico de áudio acima do threshold com debounce e filtro de ruído.

    Args:
        indata:          Bloco de áudio bruto
        frames:          Número de frames
        threshold:       Amplitude mínima para considerar pico
        ambient_noise:   Nível de ruído ambiente atual
        last_event_time: Timestamp do último pico detectado (monotonic)
        debounce_seconds: Janela mínima entre detecções

    Returns:
        Tuple de (pico_detectado: bool, novo_ruido_ambiente: float, timestamp_evento: float)

    NOTA CRÍTICA:
        Esta função é chamada 21x/segundo pelo sounddevice.
        NUNCA fazer I/O aqui (sem print, sem logger, sem disco).
        Apenas operações numpy leves.
    """
    rms = calcular_rms(indata, frames)
    novo_ruido = atualizar_ruido_ambiente(rms, ambient_noise)
    agora = time.monotonic()

    pico = (
        rms > threshold and
        (agora - last_event_time) > debounce_seconds
    )

    return pico, novo_ruido, agora if pico else last_event_time
