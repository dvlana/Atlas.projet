# -*- coding: utf-8 -*-
"""
Origem.1 — Sistema Central de Orquestração
============================================
Ponto único de entrada para o cérebro digital do projeto.

Responsabilidades:
  - Inicializar todos os módulos do sistema
  - Manter estrutura de pastas obrigatória
  - Registrar logs centralizados com rotação automática
  - Expor health check para monitoramento

Uso:
  python _sistema/core/sistema.py            → inicializa e exibe status
  from _sistema.core.sistema import Origem   → uso como módulo
"""

import os
import sys
import json
import logging
import logging.handlers
from pathlib import Path
from datetime import datetime

# ─── RAIZ ABSOLUTA ────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent  # → /Origem.1

# ─── ESTRUTURA OBRIGATÓRIA ────────────────────────────────────────────────────
# Estas pastas devem sempre existir. Criadas automaticamente se ausentes.
ESTRUTURA_OBRIGATORIA = [
    "_sistema/core",
    "_sistema/config",
    "_sistema/logs",
    "_sistema/debug",
    "_sistema/temp",
    "_sistema/modules",
    "_sistema/utils",
]


def garantir_estrutura() -> list[str]:
    """Cria a estrutura de pastas obrigatória dentro de /Origem.1."""
    criadas = []
    for pasta in ESTRUTURA_OBRIGATORIA:
        caminho = ROOT / pasta
        if not caminho.exists():
            caminho.mkdir(parents=True, exist_ok=True)
            criadas.append(str(caminho))
    return criadas


def configurar_logging(nivel: str = "INFO") -> logging.Logger:
    """
    Configura logging centralizado com:
      - RotatingFileHandler: arquivo rotacionado em 1MB, 7 backups
      - StreamHandler: saída no console
      - Formato: timestamp | nível | módulo | mensagem
    """
    log_dir = ROOT / "_sistema" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"origem_{datetime.now().strftime('%Y-%m-%d')}.log"

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    logger = logging.getLogger("Origem")
    logger.setLevel(getattr(logging, nivel.upper(), logging.INFO))

    # Arquivo com rotação
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=1_000_000, backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)

    # Console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)

    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger


def carregar_config() -> dict:
    """Carrega configuração central do sistema."""
    config_path = ROOT / "_sistema" / "config" / "sistema.json"
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


class Origem:
    """
    Núcleo central do sistema Origem.1.
    Orquestra inicialização, estrutura e health check.
    """

    def __init__(self):
        self.root = ROOT
        self.config = carregar_config()
        self.log = configurar_logging(
            self.config.get("logging", {}).get("nivel", "INFO")
        )

        # Garante estrutura antes de qualquer outra operação
        criadas = garantir_estrutura()
        if criadas:
            for p in criadas:
                self.log.info(f"[ESTRUTURA] Pasta criada automaticamente: {p}")

        self.log.info(f"[BOOT] Origem.1 inicializado | raiz={self.root}")
        self.log.info(f"[BOOT] Versão: {self.config.get('sistema', {}).get('versao', 'N/A')}")

    def status(self) -> dict:
        """Retorna health check do sistema."""
        modulos = self.config.get("modulos", {})
        status_modulos = {}
        for nome, caminho in modulos.items():
            status_modulos[nome] = (self.root / caminho).exists()

        estrutura_ok = all(
            (self.root / p).exists() for p in ESTRUTURA_OBRIGATORIA
        )

        return {
            "sistema": "Origem.1",
            "root": str(self.root),
            "estrutura_ok": estrutura_ok,
            "modulos": status_modulos,
            "timestamp": datetime.now().isoformat(),
        }

    def relatorio(self) -> None:
        """Imprime relatório completo do sistema no console e no log."""
        s = self.status()
        self.log.info("─" * 60)
        self.log.info("[STATUS] Relatório do Sistema Origem.1")
        self.log.info(f"  Root      : {s['root']}")
        self.log.info(f"  Estrutura : {'✅ OK' if s['estrutura_ok'] else '❌ INCOMPLETA'}")
        self.log.info("  Módulos:")
        for nome, ativo in s["modulos"].items():
            icone = "✅" if ativo else "❌"
            self.log.info(f"    {icone} {nome}")
        self.log.info("─" * 60)


if __name__ == "__main__":
    sistema = Origem()
    sistema.relatorio()
