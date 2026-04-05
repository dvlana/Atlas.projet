# -*- coding: utf-8 -*-
"""
SkillEngine — Motor Central do Sistema de Skills
================================================
Ponto único de orquestração para criação, busca, uso e evolução de skills.

Responsabilidades:
  - Buscar skills existentes antes de criar qualquer nova lógica
  - Registrar uso de skills no memory.json
  - Detectar padrões repetidos e sugerir criação de nova skill
  - Versionar skills quando atualizadas
  - Arquivar skills obsoletas

Uso:
  from skills.core.engine import SkillEngine
  engine = SkillEngine()

  # Buscar skill por nome ou tag
  skill = engine.buscar("spawn_guard")

  # Registrar uso
  engine.usar("skill_spawn_guard")

  # Registrar nova skill
  engine.registrar({...})

  # Relatório completo
  engine.relatorio()
"""

import json
import time
import shutil
import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger("Origem.SkillEngine")

# ─── CAMINHOS ─────────────────────────────────────────────────────────────────
ROOT        = Path(__file__).resolve().parent.parent.parent   # → /Origem.1
SKILLS_DIR  = ROOT / "skills"
ACTIVE_DIR  = SKILLS_DIR / "active"
ARCHIVED_DIR= SKILLS_DIR / "archived"
CORE_DIR    = SKILLS_DIR / "core"
REGISTRY    = SKILLS_DIR / "registry.json"
MEMORY      = SKILLS_DIR / "memory.json"


class SkillEngine:
    """
    Motor central do sistema de skills do Origem.1.

    Princípios:
      1. Toda lógica reutilizável é uma skill
      2. Nunca criar lógica duplicada — sempre buscar primeiro
      3. Todo uso é registrado na memória evolutiva
      4. Skills muito usadas evoluem automaticamente (v2, v3...)
      5. Skills obsoletas são arquivadas, nunca deletadas
    """

    # Threshold para sugerir criação automática de skill
    PATTERN_THRESHOLD = 2   # uso repetido >= 2x → vira skill
    EVOLUTION_THRESHOLD = 10  # uses >= 10 → sugerir refatoração

    def __init__(self):
        self._lock = threading.Lock()
        self._garantir_estrutura()
        self._registry: dict = self._carregar_registry()
        self._memory: dict = self._carregar_memory()
        logger.info(f"[SKILL-ENGINE] Inicializado | {len(self._registry.get('skills', []))} skills carregadas")

    # ─── ESTRUTURA ────────────────────────────────────────────────────────────

    def _garantir_estrutura(self) -> None:
        """Garante que todas as pastas obrigatórias existem."""
        for pasta in [SKILLS_DIR, ACTIVE_DIR, ARCHIVED_DIR, CORE_DIR]:
            pasta.mkdir(parents=True, exist_ok=True)

    # ─── I/O JSON ─────────────────────────────────────────────────────────────

    def _carregar_registry(self) -> dict:
        if REGISTRY.exists():
            with open(REGISTRY, encoding="utf-8") as f:
                return json.load(f)
        return {"version": "1.0.0", "skills": []}

    def _salvar_registry(self) -> None:
        with open(REGISTRY, "w", encoding="utf-8") as f:
            json.dump(self._registry, f, indent=2, ensure_ascii=False)

    def _carregar_memory(self) -> dict:
        if MEMORY.exists():
            with open(MEMORY, encoding="utf-8") as f:
                return json.load(f)
        return {"version": "1.0.0", "skill_stats": {}, "evolution_log": [], "pattern_log": []}

    def _salvar_memory(self) -> None:
        with open(MEMORY, "w", encoding="utf-8") as f:
            json.dump(self._memory, f, indent=2, ensure_ascii=False)

    # ─── BUSCA ────────────────────────────────────────────────────────────────

    def buscar(self, query: str) -> Optional[dict]:
        """
        Busca skill por nome, id ou tag.
        Retorna a skill mais relevante ou None se não encontrada.

        Sempre chamar ANTES de criar nova lógica.
        """
        query_norm = query.lower().strip()
        skills = self._registry.get("skills", [])

        # Busca exata por id ou nome
        for skill in skills:
            if skill.get("status") != "active":
                continue
            if query_norm in (skill.get("id", ""), skill.get("name", "")):
                logger.info(f"[SKILL-ENGINE] Skill encontrada (exata): {skill['id']}")
                return skill

        # Busca por tags
        for skill in skills:
            if skill.get("status") != "active":
                continue
            tags = [t.lower() for t in skill.get("tags", [])]
            if query_norm in tags or any(query_norm in t for t in tags):
                logger.info(f"[SKILL-ENGINE] Skill encontrada (tag): {skill['id']}")
                return skill

        # Busca parcial por purpose ou name
        for skill in skills:
            if skill.get("status") != "active":
                continue
            if query_norm in skill.get("purpose", "").lower() or \
               query_norm in skill.get("name", "").lower():
                logger.info(f"[SKILL-ENGINE] Skill encontrada (parcial): {skill['id']}")
                return skill

        logger.warning(f"[SKILL-ENGINE] Nenhuma skill encontrada para: '{query}'")
        return None

    def buscar_por_categoria(self, categoria: str) -> list[dict]:
        """Retorna todas as skills ativas de uma categoria."""
        return [
            s for s in self._registry.get("skills", [])
            if s.get("status") == "active" and s.get("category", "").lower() == categoria.lower()
        ]

    def listar_todas(self, apenas_ativas: bool = True) -> list[dict]:
        """Lista todas as skills registradas."""
        skills = self._registry.get("skills", [])
        if apenas_ativas:
            return [s for s in skills if s.get("status") == "active"]
        return skills

    # ─── REGISTRO ─────────────────────────────────────────────────────────────

    def registrar(self, skill_def: dict, sobrescrever: bool = False) -> bool:
        """
        Registra uma nova skill no sistema.

        Verifica duplicatas antes de registrar.
        Se skill já existe e sobrescrever=False, retorna False.

        Args:
            skill_def: Dicionário com definição da skill (ver formato no registry.json)
            sobrescrever: Se True, atualiza skill existente com versionamento

        Returns:
            True se registrada com sucesso, False se duplicata ignorada
        """
        skill_id = skill_def.get("id") or f"skill_{skill_def.get('name', 'unnamed')}"
        skill_def["id"] = skill_id

        with self._lock:
            # Verificar duplicata
            existente = self._encontrar_por_id(skill_id)

            if existente and not sobrescrever:
                logger.warning(f"[SKILL-ENGINE] Skill '{skill_id}' já existe. Use sobrescrever=True para atualizar.")
                return False

            if existente and sobrescrever:
                return self._versionar_e_atualizar(existente, skill_def)

            # Nova skill
            skill_def.setdefault("status", "active")
            skill_def.setdefault("version", 1)
            skill_def.setdefault("created_at", datetime.now().isoformat())
            skill_def.setdefault("usage_count", 0)

            self._registry["skills"].append(skill_def)
            self._salvar_registry()

            # Inicializa stats na memória
            self._memory["skill_stats"][skill_id] = {
                "uses": 0, "errors": 0, "last_used": None, "improvements": []
            }
            self._registrar_evolucao("SKILL_CREATED", f"Nova skill registrada: {skill_id}")
            self._salvar_memory()

            logger.info(f"[SKILL-ENGINE] ✅ Skill registrada: {skill_id}")
            return True

    def _encontrar_por_id(self, skill_id: str) -> Optional[dict]:
        for s in self._registry.get("skills", []):
            if s.get("id") == skill_id:
                return s
        return None

    def _versionar_e_atualizar(self, existente: dict, nova: dict) -> bool:
        """Arquiva versão atual e registra nova versão com número incrementado."""
        versao_atual = existente.get("version", 1)
        nova_versao = versao_atual + 1

        # Arquiva versão antiga
        existente_copia = dict(existente)
        existente_copia["status"] = "archived"
        existente_copia["archived_at"] = datetime.now().isoformat()
        existente_copia["id"] = f"{existente['id']}_v{versao_atual}"

        # Remove original e adiciona arquivo + nova versão
        self._registry["skills"] = [
            s for s in self._registry["skills"] if s.get("id") != existente["id"]
        ]
        self._registry["skills"].append(existente_copia)

        nova["version"] = nova_versao
        nova["updated_at"] = datetime.now().isoformat()
        nova["status"] = "active"
        nova["usage_count"] = existente.get("usage_count", 0)
        self._registry["skills"].append(nova)
        self._salvar_registry()

        self._registrar_evolucao(
            "SKILL_EVOLVED",
            f"Skill {existente['id']} atualizada: v{versao_atual} → v{nova_versao}"
        )
        self._salvar_memory()

        logger.info(f"[SKILL-ENGINE] 🔄 Skill evoluída: {existente['id']} v{versao_atual} → v{nova_versao}")
        return True

    # ─── USO ──────────────────────────────────────────────────────────────────

    def usar(self, skill_id: str, erro: Exception = None) -> None:
        """
        Registra uso de uma skill na memória evolutiva.
        Chamar sempre que uma skill for executada.

        Se uso acumulado atingir EVOLUTION_THRESHOLD → loga sugestão de evolução.
        """
        with self._lock:
            stats = self._memory["skill_stats"]
            if skill_id not in stats:
                stats[skill_id] = {"uses": 0, "errors": 0, "last_used": None, "improvements": []}

            stats[skill_id]["uses"] += 1
            stats[skill_id]["last_used"] = datetime.now().isoformat()

            if erro:
                stats[skill_id]["errors"] += 1
                logger.warning(f"[SKILL-ENGINE] Erro registrado em '{skill_id}': {erro}")

            # Atualiza contador no registry também
            skill = self._encontrar_por_id(skill_id)
            if skill:
                skill["usage_count"] = stats[skill_id]["uses"]

            uses = stats[skill_id]["uses"]

            # Sugestão de evolução
            if uses == self.EVOLUTION_THRESHOLD:
                logger.info(
                    f"[SKILL-ENGINE] 💡 Skill '{skill_id}' usada {uses}x — "
                    f"considerar refatoração/otimização (v{(skill or {}).get('version', 1) + 1})."
                )
                self._registrar_evolucao(
                    "EVOLUTION_SUGGESTED",
                    f"Skill '{skill_id}' atingiu {uses} usos — elegível para evolução"
                )

            self._salvar_registry()
            self._salvar_memory()

    # ─── PADRÕES ──────────────────────────────────────────────────────────────

    def registrar_padrao(self, descricao: str, arquivo: str, linha: int = None) -> None:
        """
        Registra um padrão repetido observado no código.
        Quando o mesmo padrão aparecer PATTERN_THRESHOLD vezes → sugerir skill.
        """
        padrao_key = descricao.lower().strip().replace(" ", "_")[:50]

        pattern_log = self._memory.get("pattern_log", [])

        # Conta ocorrências do mesmo padrão
        ocorrencias = [p for p in pattern_log if p.get("key") == padrao_key]
        count = len(ocorrencias) + 1

        pattern_log.append({
            "key": padrao_key,
            "descricao": descricao,
            "arquivo": arquivo,
            "linha": linha,
            "timestamp": datetime.now().isoformat(),
            "ocorrencia": count,
        })
        self._memory["pattern_log"] = pattern_log

        if count >= self.PATTERN_THRESHOLD:
            logger.warning(
                f"[SKILL-ENGINE] 🔍 PADRÃO DETECTADO ({count}x): '{descricao}' "
                f"— Candidato a nova skill! Arquivo: {arquivo}"
            )
            self._registrar_evolucao(
                "PATTERN_DETECTED",
                f"Padrão '{descricao}' detectado {count}x — criar skill recomendado"
            )

        self._salvar_memory()

    # ─── ARQUIVAMENTO ─────────────────────────────────────────────────────────

    def arquivar(self, skill_id: str, motivo: str = "obsoleta") -> bool:
        """Arquiva uma skill sem deletar — apenas muda status."""
        skill = self._encontrar_por_id(skill_id)
        if not skill:
            logger.warning(f"[SKILL-ENGINE] Skill '{skill_id}' não encontrada para arquivar.")
            return False
        skill["status"] = "archived"
        skill["archived_at"] = datetime.now().isoformat()
        skill["archive_reason"] = motivo
        self._salvar_registry()
        self._registrar_evolucao("SKILL_ARCHIVED", f"Skill '{skill_id}' arquivada: {motivo}")
        self._salvar_memory()
        logger.info(f"[SKILL-ENGINE] 📦 Skill arquivada: {skill_id}")
        return True

    # ─── MEMÓRIA ──────────────────────────────────────────────────────────────

    def _registrar_evolucao(self, evento: str, descricao: str) -> None:
        self._memory["evolution_log"].append({
            "timestamp": datetime.now().isoformat(),
            "event": evento,
            "description": descricao,
        })

    # ─── RELATÓRIO ────────────────────────────────────────────────────────────

    def relatorio(self) -> dict:
        """Gera relatório completo do sistema de skills."""
        skills = self._registry.get("skills", [])
        ativas = [s for s in skills if s.get("status") == "active"]
        arquivadas = [s for s in skills if s.get("status") == "archived"]
        stats = self._memory.get("skill_stats", {})

        mais_usadas = sorted(
            [(sid, s["uses"]) for sid, s in stats.items() if s["uses"] > 0],
            key=lambda x: x[1], reverse=True
        )[:5]

        com_erros = [(sid, s["errors"]) for sid, s in stats.items() if s["errors"] > 0]

        categorias: dict[str, int] = {}
        for s in ativas:
            cat = s.get("category", "uncategorized")
            categorias[cat] = categorias.get(cat, 0) + 1

        return {
            "total_skills": len(skills),
            "ativas": len(ativas),
            "arquivadas": len(arquivadas),
            "categorias": categorias,
            "mais_usadas": mais_usadas,
            "com_erros": com_erros,
            "padroes_detectados": len(self._memory.get("pattern_log", [])),
            "eventos_evolucao": len(self._memory.get("evolution_log", [])),
        }

    def imprimir_relatorio(self) -> None:
        """Imprime relatório formatado no console."""
        r = self.relatorio()
        print()
        print("═" * 60)
        print("  SKILL ENGINE — SISTEMA ORIGEM.1")
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("═" * 60)
        print(f"\n  📦 Skills totais   : {r['total_skills']}")
        print(f"  ✅ Ativas          : {r['ativas']}")
        print(f"  📁 Arquivadas      : {r['arquivadas']}")
        print(f"  🔍 Padrões log     : {r['padroes_detectados']}")
        print(f"  🔄 Eventos evolução: {r['eventos_evolucao']}")

        if r["categorias"]:
            print("\n  ── CATEGORIAS ─────────────────────────────────────")
            for cat, count in sorted(r["categorias"].items()):
                print(f"    {cat:<30s} {count} skill(s)")

        if r["mais_usadas"]:
            print("\n  ── MAIS USADAS ────────────────────────────────────")
            for sid, uses in r["mais_usadas"]:
                print(f"    {sid:<40s} {uses}x")

        if r["com_erros"]:
            print("\n  ── COM ERROS ──────────────────────────────────────")
            for sid, erros in r["com_erros"]:
                print(f"    ⚠️  {sid:<38s} {erros} erro(s)")

        print("\n" + "═" * 60)

    def listar_catalogo(self) -> None:
        """Lista catálogo completo de skills ativas com detalhes."""
        skills = [s for s in self._registry.get("skills", []) if s.get("status") == "active"]
        stats = self._memory.get("skill_stats", {})
        print()
        print(f"  📚 CATÁLOGO DE SKILLS ({len(skills)} ativas)")
        print("─" * 60)
        for s in sorted(skills, key=lambda x: x.get("category", "")):
            sid = s["id"]
            uses = stats.get(sid, {}).get("uses", 0)
            print(f"\n  [{s.get('category', '?'):20s}] v{s.get('version', 1)}  {sid}")
            print(f"   📝 {s.get('purpose', '')}")
            print(f"   🏷️  {', '.join(s.get('tags', []))}")
            print(f"   📊 Usos: {uses} | Arquivo: {s.get('file', 'N/A')}")
        print()


if __name__ == "__main__":
    engine = SkillEngine()
    engine.imprimir_relatorio()
    print()
    engine.listar_catalogo()
