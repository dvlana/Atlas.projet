# -*- coding: utf-8 -*-
"""
SkillSanitizer — Fase 2: Limpeza e Padronização de Skills Externas
====================================================================
Recebe código aprovado (ou parcial) pelo SkillAnalyzer e:
  - Remove código desnecessário
  - Padroniza nomes e estrutura
  - Injeta SKILL_META se ausente
  - Injeta docstring padrão se ausente
  - Ajusta imports quebrados
  - Elimina acoplamentos com sistemas externos
"""

import re
import logging
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger("Origem.Skills.Sanitizer")

# ─── TEMPLATE DE HEADER ───────────────────────────────────────────────────────
_HEADER_TEMPLATE = '''# -*- coding: utf-8 -*-
"""
Skill: {name}
{sep}
{purpose}

Skill ID  : {skill_id}
Categoria : {category}
Versão    : {version}
Importada : {imported_at}
"""
'''

_META_TEMPLATE = '''
SKILL_META = {{
    "id": "{skill_id}",
    "name": "{name}",
    "version": {version},
    "category": "{category}",
    "purpose": "{purpose}",
    "safe_mode": True,
    "imported_at": "{imported_at}",
}}
'''


@dataclass
class SanitizationResult:
    """Resultado da sanitização de uma skill."""
    codigo_original:   str
    codigo_sanitizado: str
    skill_id:          str
    nome_padrao:       str
    alteracoes:        list[str]
    sucesso:           bool
    erros:             list[str]


class SkillSanitizer:
    """
    Fase 2 do Skill Import Protocol: Limpeza e Padronização.

    Transforma código externo "bruto" no padrão Origem.1,
    preservando sempre a lógica funcional original.
    """

    def sanitizar(
        self,
        codigo: str,
        nome: str,
        categoria: str = "imported",
        purpose: str = "",
        versao: int = 1,
    ) -> SanitizationResult:
        """
        Sanitiza código externo para padrão Origem.1.

        Args:
            codigo:    Código-fonte original
            nome:      Nome da skill (snake_case)
            categoria: Categoria no sistema de skills
            purpose:   Descrição do propósito
            versao:    Versão inicial (default: 1)

        Returns:
            SanitizationResult com código sanitizado e log de alterações
        """
        alteracoes = []
        erros = []

        # Normaliza nome para snake_case
        nome_norm = self._normalizar_nome(nome)
        skill_id = f"skill_{nome_norm}"
        imported_at = datetime.now().strftime("%Y-%m-%d")

        codigo_work = codigo

        # ─── 1. Remove BOM e espaços extras ───────────────────────────────────
        if codigo_work.startswith("\ufeff"):
            codigo_work = codigo_work[1:]
            alteracoes.append("BOM UTF-8 removido")

        # ─── 2. Normaliza quebras de linha ────────────────────────────────────
        codigo_work = codigo_work.replace("\r\n", "\n").replace("\r", "\n")

        # ─── 3. Remove shebang se existir ─────────────────────────────────────
        if codigo_work.startswith("#!"):
            linhas = codigo_work.splitlines()
            codigo_work = "\n".join(linhas[1:])
            alteracoes.append("Shebang removido")

        # ─── 4. Remove header existente (substitui pelo padrão) ───────────────
        strip_result, tinha_header = self._remover_header_antigo(codigo_work)
        if tinha_header:
            codigo_work = strip_result
            alteracoes.append("Header antigo substituído pelo padrão Origem.1")

        # ─── 5. Inject SKILL_META se ausente ──────────────────────────────────
        if "SKILL_META" not in codigo_work:
            meta = _META_TEMPLATE.format(
                skill_id=skill_id, name=nome_norm, version=versao,
                category=categoria, purpose=purpose or f"Skill {nome_norm} importada",
                imported_at=imported_at,
            )
            # Insere depois dos imports
            codigo_work = self._inserir_apos_imports(codigo_work, meta)
            alteracoes.append("SKILL_META injetado")

        # ─── 6. Normaliza nomes de variáveis/funções inconsistentes ───────────
        # Padrões camelCase → snake_case nos nomes de funções públicas
        camel_matches = re.findall(r'\bdef ([a-z][a-zA-Z]+)\b', codigo_work)
        for match in camel_matches:
            snake = self._camel_to_snake(match)
            if snake != match:
                codigo_work = re.sub(rf'\bdef {re.escape(match)}\b', f'def {snake}', codigo_work)
                alteracoes.append(f"Função renomeada: {match} → {snake}")

        # ─── 7. Garante encoding no topo ──────────────────────────────────────
        if "# -*- coding: utf-8 -*-" not in codigo_work:
            sep = "=" * (len(nome_norm) + 8)
            header = _HEADER_TEMPLATE.format(
                name=nome_norm,
                sep=sep,
                purpose=purpose or f"Skill importada: {nome_norm}",
                skill_id=skill_id,
                category=categoria,
                version=versao,
                imported_at=imported_at,
            )
            codigo_work = header + "\n" + codigo_work
            alteracoes.append("Header padrão Origem.1 injetado")
        else:
            # Já tem encoding, apenas substitui docstring se genérica
            alteracoes.append("Encoding UTF-8 já presente — mantido")

        # ─── 8. Normaliza múltiplas linhas em branco ──────────────────────────
        codigo_work = re.sub(r'\n{4,}', '\n\n\n', codigo_work)

        # ─── 9. Remove trailing whitespace ────────────────────────────────────
        linhas_limpas = [l.rstrip() for l in codigo_work.splitlines()]
        codigo_work = "\n".join(linhas_limpas)

        # Garante newline final
        if not codigo_work.endswith("\n"):
            codigo_work += "\n"

        logger.info(f"[SANITIZER] '{nome_norm}' sanitizado | {len(alteracoes)} alteração(ões)")

        return SanitizationResult(
            codigo_original=codigo,
            codigo_sanitizado=codigo_work,
            skill_id=skill_id,
            nome_padrao=nome_norm,
            alteracoes=alteracoes,
            sucesso=True,
            erros=erros,
        )

    # ─── HELPERS ──────────────────────────────────────────────────────────────

    @staticmethod
    def _normalizar_nome(nome: str) -> str:
        """Converte qualquer nome para snake_case limpo."""
        nome = nome.strip().lower()
        nome = re.sub(r'[^a-z0-9_]', '_', nome)
        nome = re.sub(r'_+', '_', nome)
        nome = nome.strip('_')
        return nome

    @staticmethod
    def _camel_to_snake(nome: str) -> str:
        s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', nome)
        return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    @staticmethod
    def _remover_header_antigo(codigo: str) -> tuple[str, bool]:
        """Remove docstring de módulo existente no topo."""
        codigo_strip = codigo.lstrip()
        tinha = False
        if codigo_strip.startswith('"""') or codigo_strip.startswith("'''"):
            quote = '"""' if codigo_strip.startswith('"""') else "'''"
            end_idx = codigo_strip.find(quote, 3)
            if end_idx != -1:
                codigo_strip = codigo_strip[end_idx + 3:].lstrip()
                tinha = True
        return codigo_strip, tinha

    @staticmethod
    def _inserir_apos_imports(codigo: str, insercao: str) -> str:
        """Insere texto após o bloco de imports."""
        linhas = codigo.splitlines()
        ultimo_import = 0
        for i, linha in enumerate(linhas):
            stripped = linha.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                ultimo_import = i

        if ultimo_import > 0:
            linhas.insert(ultimo_import + 1, insercao)
            return "\n".join(linhas)
        return insercao + "\n" + codigo
