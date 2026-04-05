# -*- coding: utf-8 -*-
"""
Skill: rotating_logger
========================
Configura logger com rotação de arquivo, formato padronizado e saída dupla.

Skill ID  : skill_rotating_logger
Categoria : logging
Versão    : 1
Extraída de: _sistema/core/sistema.py
"""

import sys
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

SKILL_META = {
    "id": "skill_rotating_logger",
    "name": "rotating_logger",
    "version": 1,
    "category": "logging",
}


def criar_logger(
    nome: str,
    log_dir: Path,
    nivel: str = "INFO",
    max_bytes: int = 1_000_000,
    backup_count: int = 7,
    console: bool = True,
    prefixo_arquivo: str = None,
) -> logging.Logger:
    """
    Cria e configura um logger com:
      - RotatingFileHandler: arquivo rotacionado por tamanho
      - StreamHandler: saída no console (opcional)
      - Formato: timestamp | nível | nome | mensagem

    Args:
        nome:           Nome do logger (ex: "Origem.Jarvis")
        log_dir:        Diretório onde salvar os arquivos de log
        nivel:          Nível de log ("DEBUG", "INFO", "WARNING", "ERROR")
        max_bytes:      Tamanho máximo do arquivo antes de rotacionar (default: 1MB)
        backup_count:   Número de arquivos de backup mantidos (default: 7)
        console:        Se True, também exibe logs no console
        prefixo_arquivo: Prefixo do nome do arquivo (default: nome do logger)

    Returns:
        logging.Logger configurado e pronto para uso

    Uso:
        log = criar_logger("Jarvis", Path("logs/"), nivel="DEBUG")
        log.info("Sistema iniciado")
    """
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)

    prefixo = (prefixo_arquivo or nome.lower().replace(".", "_"))
    hoje = datetime.now().strftime("%Y-%m-%d")
    log_file = log_dir / f"{prefixo}_{hoje}.log"

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger(nome)
    logger.setLevel(getattr(logging, nivel.upper(), logging.INFO))

    # Evita duplicação de handlers
    if logger.handlers:
        return logger

    # Arquivo com rotação por tamanho
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # Console
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(fmt)
        logger.addHandler(console_handler)

    return logger


def criar_audit_logger(nome: str, log_file: Path) -> logging.Logger:
    """
    Cria logger dedicado para auditoria (append-only, sem rotação, sem console).
    Ideal para spawn_audit.log e logs de segurança.

    Args:
        nome:     Nome do logger de auditoria
        log_file: Caminho completo do arquivo de auditoria

    Returns:
        logging.Logger configurado para auditoria
    """
    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    fmt = logging.Formatter(
        fmt="%(asctime)s | AUDIT | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger(f"AUDIT.{nome}")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.FileHandler(log_file, encoding="utf-8")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        logger.propagate = False  # Não propaga para o root logger

    return logger
