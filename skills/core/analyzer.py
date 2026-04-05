# -*- coding: utf-8 -*-
"""
SkillAnalyzer — Fase 1: Inspeção de Skills Externas
=====================================================
Analisa estrutura, dependências, riscos e compatibilidade
de qualquer código candidato antes de entrar no sistema.

Saída: AnalysisReport com classificação e lista de problemas encontrados.
"""

import ast
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("Origem.Skills.Analyzer")

# ─── PADRÕES DE RISCO ─────────────────────────────────────────────────────────

# Chamadas que exigem análise de contexto
RISK_PATTERNS = {
    "spawn_externo": [
        r"os\.system\s*\(", r"subprocess\.Popen\s*\(", r"subprocess\.run\s*\(",
        r"os\.startfile\s*\(", r"ShellExecute", r"child_process",
        r"spawn\s*\(", r"exec\s*\(",
    ],
    "loop_sem_controle": [
        r"while\s+True\s*:", r"while\s+1\s*:",
    ],
    "io_em_callback": [
        r"print\s*\(", r"logger\.(info|debug|warning|error)\s*\(",
        r"open\s*\(", r"write\s*\(",
    ],
    "app_externo_perigoso": [
        r"notepad", r"regedit", r"cmd\.exe", r"powershell",
    ],
    "exec_dinamico": [
        r"\beval\s*\(", r"\bexec\s*\(", r"__import__\s*\(",
        r"importlib\.import_module\s*\(",
    ],
    "acesso_rede": [
        r"requests\.", r"urllib\.", r"http\.client", r"socket\.",
        r"aiohttp\.", r"httpx\.",
    ],
}

# Dependências que requerem instalação (não stdlib)
THIRD_PARTY_DEPS = {
    "numpy", "pandas", "requests", "aiohttp", "httpx",
    "pydantic", "sqlalchemy", "celery", "redis", "boto3",
    "sounddevice", "pyaudio", "pycaw", "comtypes",
    "screen_brightness_control", "pyautogui", "keyboard",
    "openai", "anthropic", "litellm",
}

# Stdlib do Python (subconjunto relevante)
STDLIB_MODULES = {
    "os", "sys", "re", "json", "time", "math", "random", "copy",
    "threading", "asyncio", "concurrent", "functools", "itertools",
    "collections", "pathlib", "logging", "datetime", "typing",
    "subprocess", "shutil", "tempfile", "hashlib", "base64",
    "dataclasses", "enum", "abc", "contextlib", "importlib",
    "inspect", "ast", "io", "struct", "traceback",
}


@dataclass
class RiskItem:
    categoria: str
    descricao: str
    linha: Optional[int] = None
    severidade: str = "MEDIUM"   # LOW | MEDIUM | HIGH | CRITICAL


@dataclass
class AnalysisReport:
    """Resultado completo da análise de uma skill externa."""
    skill_name:      str
    source_path:     Optional[str]
    classificacao:   str            # "compativel" | "parcial" | "incompativel"
    score_inicial:   float          # 0.0 → 1.0 (compatibilidade)
    riscos:          list[RiskItem] = field(default_factory=list)
    dependencias:    list[str]      = field(default_factory=list)
    deps_externas:   list[str]      = field(default_factory=list)
    deps_stdlib:     list[str]      = field(default_factory=list)
    tem_meta:        bool           = False
    tem_docstring:   bool           = False
    tem_type_hints:  bool           = False
    linhas_codigo:   int            = 0
    funcoes:         list[str]      = field(default_factory=list)
    classes:         list[str]      = field(default_factory=list)
    problemas:       list[str]      = field(default_factory=list)
    aprovada:        bool           = False
    motivo_rejeicao: Optional[str]  = None

    def resumo(self) -> str:
        blocos = [
            f"Skill       : {self.skill_name}",
            f"Classificação: {self.classificacao.upper()}",
            f"Score inicial: {self.score_inicial:.2f}",
            f"Riscos       : {len(self.riscos)} ({sum(1 for r in self.riscos if r.severidade in ('HIGH','CRITICAL'))} críticos)",
            f"Deps externas: {', '.join(self.deps_externas) or 'nenhuma'}",
            f"Funções      : {', '.join(self.funcoes) or 'nenhuma'}",
            f"Aprovada     : {'✅ SIM' if self.aprovada else '❌ NÃO'}",
        ]
        if self.motivo_rejeicao:
            blocos.append(f"Rejeição     : {self.motivo_rejeicao}")
        return "\n".join(blocos)


class SkillAnalyzer:
    """
    Fase 1 do Skill Import Protocol: Inspeção e Classificação.

    Analisa código-fonte Python de uma skill candidata e produz
    um AnalysisReport com classificação, riscos e dependências.
    """

    def analisar_codigo(self, codigo: str, nome: str = "skill_desconhecida",
                        path: str = None) -> AnalysisReport:
        """
        Analisa o código-fonte de uma skill e retorna relatório completo.

        Args:
            codigo: Código Python como string
            nome:   Identificador da skill
            path:   Caminho original (para referência)

        Returns:
            AnalysisReport com classificação e riscos
        """
        report = AnalysisReport(skill_name=nome, source_path=path,
                                classificacao="compativel", score_inicial=1.0)

        # ─── Parse AST ────────────────────────────────────────────────────────
        try:
            tree = ast.parse(codigo)
        except SyntaxError as e:
            report.classificacao = "incompativel"
            report.score_inicial = 0.0
            report.aprovada = False
            report.motivo_rejeicao = f"SyntaxError: {e}"
            report.problemas.append(f"Erro de sintaxe: {e}")
            return report

        report.linhas_codigo = len(codigo.splitlines())

        # ─── Funções e Classes ────────────────────────────────────────────────
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                report.funcoes.append(node.name)
            elif isinstance(node, ast.ClassDef):
                report.classes.append(node.name)

        # ─── Docstring ────────────────────────────────────────────────────────
        report.tem_docstring = (
            isinstance(tree.body[0], ast.Expr) and
            isinstance(tree.body[0].value, ast.Constant) and
            isinstance(tree.body[0].value.value, str)
        ) if tree.body else False

        # ─── SKILL_META ───────────────────────────────────────────────────────
        report.tem_meta = "SKILL_META" in codigo

        # ─── Type hints ───────────────────────────────────────────────────────
        report.tem_type_hints = "->" in codigo or ": " in codigo

        # ─── Dependências (imports) ───────────────────────────────────────────
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    modulo = alias.name.split(".")[0]
                    report.dependencias.append(modulo)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    modulo = node.module.split(".")[0]
                    report.dependencias.append(modulo)

        report.dependencias = sorted(set(report.dependencias))
        report.deps_externas = [d for d in report.dependencias if d in THIRD_PARTY_DEPS]
        report.deps_stdlib = [d for d in report.dependencias if d in STDLIB_MODULES]

        # ─── Varredura de Riscos (regex no código-fonte) ──────────────────────
        linhas = codigo.splitlines()
        for categoria, padroes in RISK_PATTERNS.items():
            for padrao in padroes:
                for i, linha in enumerate(linhas, 1):
                    if re.search(padrao, linha):
                        sev = self._severidade(categoria, linha)
                        report.riscos.append(RiskItem(
                            categoria=categoria,
                            descricao=f"{padrao} → linha {i}: {linha.strip()[:60]}",
                            linha=i,
                            severidade=sev,
                        ))

        # ─── Classificação Final ──────────────────────────────────────────────
        criticos = [r for r in report.riscos if r.severidade == "CRITICAL"]
        altos    = [r for r in report.riscos if r.severidade == "HIGH"]
        penalidade = len(criticos) * 0.3 + len(altos) * 0.15 + len(report.deps_externas) * 0.05

        report.score_inicial = max(0.0, round(1.0 - penalidade, 2))

        if criticos:
            report.classificacao = "incompativel"
            report.aprovada = False
            report.motivo_rejeicao = f"{len(criticos)} risco(s) CRÍTICO(s) detectados"
        elif report.score_inicial >= 0.7:
            report.classificacao = "compativel"
            report.aprovada = True
        elif report.score_inicial >= 0.4:
            report.classificacao = "parcial"
            report.aprovada = True   # aprovada com ressalvas → passa para sanitização
        else:
            report.classificacao = "incompativel"
            report.aprovada = False
            report.motivo_rejeicao = f"Score muito baixo: {report.score_inicial}"

        # Alertas de qualidade (não bloqueantes)
        if not report.tem_meta:
            report.problemas.append("SKILL_META ausente — será gerado automaticamente")
        if not report.tem_docstring:
            report.problemas.append("Docstring ausente — recomendado para documentação")
        if not report.tem_type_hints:
            report.problemas.append("Type hints ausentes — recomendado para clareza")

        logger.info(
            f"[ANALYZER] '{nome}' → {report.classificacao.upper()} "
            f"(score={report.score_inicial:.2f}, riscos={len(report.riscos)})"
        )
        return report

    def analisar_arquivo(self, path: Path) -> AnalysisReport:
        """Analisa um arquivo .py diretamente."""
        path = Path(path)
        if not path.exists():
            r = AnalysisReport(skill_name=path.stem, source_path=str(path),
                               classificacao="incompativel", score_inicial=0.0)
            r.motivo_rejeicao = f"Arquivo não encontrado: {path}"
            return r
        return self.analisar_codigo(
            path.read_text(encoding="utf-8"),
            nome=path.stem,
            path=str(path),
        )

    @staticmethod
    def _severidade(categoria: str, linha: str) -> str:
        if categoria == "exec_dinamico":
            return "CRITICAL"
        if categoria == "app_externo_perigoso":
            return "CRITICAL"
        if categoria == "loop_sem_controle":
            # Loop sem sleep ou Event.wait → HIGH. Com sleep → LOW
            if "sleep" in linha or "wait" in linha or "Event" in linha:
                return "LOW"
            return "HIGH"
        if categoria == "spawn_externo":
            return "HIGH"
        if categoria == "io_em_callback":
            return "LOW"
        if categoria == "acesso_rede":
            return "MEDIUM"
        return "MEDIUM"
