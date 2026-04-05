# -*- coding: utf-8 -*-
"""
Skill: lazy_module_loader
==========================
Carrega módulos Python apenas na primeira utilização (lazy loading).
Reduz uso de memória e tempo de inicialização do sistema.

Skill ID  : skill_lazy_module_loader
Categoria : performance
Versão    : 1
Extraída de: jvs_auth_92kx-main/Jarvis- Aula 01/automation/automation_controller.py
"""

import importlib
import logging
from typing import Any

logger = logging.getLogger("Origem.Skills.LazyLoader")

SKILL_META = {
    "id": "skill_lazy_module_loader",
    "name": "lazy_module_loader",
    "version": 1,
    "category": "performance",
}


class LazyLoader:
    """
    Carregador lazy de módulos Python.

    Instancia um módulo/classe apenas na primeira chamada ao atributo.
    Após carregado, o resultado é cacheado (sem re-import).

    Uso:
        loader = LazyLoader()

        # Registra módulos para load lazy
        loader.registrar("file_auto", "automation.file_automation", "FileAutomation")
        loader.registrar("web_auto", "automation.web_automation", "WebAutomation")

        # Carrega apenas quando necessário
        fa = loader.obter("file_auto")   # importado agora
        fa = loader.obter("file_auto")   # usa cache, sem re-import
    """

    def __init__(self):
        self._cache: dict[str, Any] = {}
        self._specs: dict[str, tuple[str, str | None]] = {}

    def registrar(self, alias: str, modulo_path: str, classe: str = None) -> None:
        """
        Registra um módulo para carregamento lazy.

        Args:
            alias:       Nome de acesso ao módulo
            modulo_path: Caminho do módulo Python (ex: "automation.file_automation")
            classe:      Nome da classe a instanciar (None = retorna o módulo inteiro)
        """
        self._specs[alias] = (modulo_path, classe)
        logger.debug(f"[LAZY] Registrado: {alias} → {modulo_path}" + (f".{classe}" if classe else ""))

    def obter(self, alias: str) -> Any:
        """
        Retorna instância do módulo/classe (carrega na primeira chamada).

        Args:
            alias: Nome registrado via registrar()

        Returns:
            Instância da classe ou módulo importado

        Raises:
            KeyError: Se alias não foi registrado
            ImportError: Se módulo não encontrado
        """
        if alias in self._cache:
            return self._cache[alias]

        if alias not in self._specs:
            raise KeyError(f"[LAZY] Alias '{alias}' não registrado. Use registrar() primeiro.")

        modulo_path, classe = self._specs[alias]
        modulo = importlib.import_module(modulo_path)

        if classe:
            cls = getattr(modulo, classe)
            instancia = cls()
            self._cache[alias] = instancia
            logger.info(f"[LAZY] Carregado (lazy): {modulo_path}.{classe}")
        else:
            self._cache[alias] = modulo
            logger.info(f"[LAZY] Carregado (lazy): {modulo_path}")

        return self._cache[alias]

    def esta_carregado(self, alias: str) -> bool:
        """Retorna True se o módulo já foi carregado (está em cache)."""
        return alias in self._cache

    def status(self) -> dict[str, bool]:
        """Retorna status de carregamento de todos os módulos registrados."""
        return {alias: alias in self._cache for alias in self._specs}
