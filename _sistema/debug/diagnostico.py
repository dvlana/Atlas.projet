# -*- coding: utf-8 -*-
"""
Diagnóstico do Sistema Origem.1
================================
Ferramenta de auto-diagnóstico que:
  - Varre toda a estrutura de /Origem.1
  - Detecta arquivos fora da estrutura esperada
  - Verifica integridade dos módulos principais
  - Gera relatório completo em texto e JSON
  - Sugere ações corretivas

Uso:
  python _sistema/debug/diagnostico.py
"""

import os
import sys
import json
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime

# ─── ROOT ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent  # → /Origem.1

# ─── MÓDULOS ESPERADOS ────────────────────────────────────────────────────────
MODULOS_ESPERADOS = {
    "Jarvis Backend":    "jvs_auth_92kx-main/Jarvis- Aula 01",
    "Jarvis Frontend":   "agent-starter-react-main",
    "LiveKit":           "livekit",
    "Controle PC":       "jvs_auth_92kx-main/Aula automacao/Controle_PC",
    "Jarvis Memória":    "jvs_auth_92kx-main/Jarvis Mem0",
    "Sistema Central":   "_sistema",
}

ARQUIVOS_CRITICOS = {
    "ClapDetector":        "jvs_auth_92kx-main/Jarvis- Aula 01/automation/clap_detector.py",
    "AutomationController":"jvs_auth_92kx-main/Jarvis- Aula 01/automation/automation_controller.py",
    "SystemAutomation":    "jvs_auth_92kx-main/Jarvis- Aula 01/automation/system_automation.py",
    "JarvisControl":       "jvs_auth_92kx-main/Jarvis- Aula 01/automacao_jarvis.py",
    "AgentPrincipal":      "jvs_auth_92kx-main/Jarvis- Aula 01/agent.py",
    "SpawnGuard":          "_sistema/modules/spawn_guard.py",
    "SistemaCentral":      "_sistema/core/sistema.py",
    "ConfigSistema":       "_sistema/config/sistema.json",
}

ESTRUTURA_OBRIGATORIA = [
    "_sistema/core",
    "_sistema/config",
    "_sistema/logs",
    "_sistema/debug",
    "_sistema/temp",
    "_sistema/modules",
    "_sistema/utils",
]


def checar_spawn_guard() -> dict:
    """
    Verifica se o clap_detector ainda tem notepad como default_app.
    Detecta a vulnerabilidade original.
    """
    arquivo = ROOT / "jvs_auth_92kx-main/Jarvis- Aula 01/automation/clap_detector.py"
    resultado = {"ok": True, "detalhes": []}

    if not arquivo.exists():
        return {"ok": False, "detalhes": ["clap_detector.py não encontrado"]}

    conteudo = arquivo.read_text(encoding="utf-8")

    # Verifica se ainda tem default="notepad" (vulnerabilidade)
    if 'default_app: str = "notepad"' in conteudo:
        resultado["ok"] = False
        resultado["detalhes"].append(
            "⚠️  VULNERABILIDADE: default_app ainda é 'notepad' — notepad pode abrir sozinho!"
        )

    if "_BLOCKED_APPS" in conteudo:
        resultado["detalhes"].append("✅ Spawn Guard (_BLOCKED_APPS) presente")
    else:
        resultado["ok"] = False
        resultado["detalhes"].append("❌ Spawn Guard (_BLOCKED_APPS) AUSENTE")

    if "SPAWN-GUARD" in conteudo:
        resultado["detalhes"].append("✅ Log de spawn guard presente")
    else:
        resultado["detalhes"].append("⚠️  Log de spawn guard não encontrado")

    return resultado


def checar_processos_notepad() -> dict:
    """Verifica se notepad.exe está rodando agora."""
    try:
        result = subprocess.run(
            ["tasklist", "/fi", "imagename eq notepad.exe"],
            capture_output=True, text=True, timeout=5
        )
        rodando = "notepad.exe" in result.stdout.lower()
        contagem = result.stdout.lower().count("notepad.exe")
        return {
            "rodando": rodando,
            "instancias": contagem if rodando else 0,
        }
    except Exception as e:
        return {"rodando": False, "instancias": 0, "erro": str(e)}


def diagnosticar() -> dict:
    """Executa diagnóstico completo do sistema."""
    timestamp = datetime.now().isoformat()
    resultado = {
        "timestamp": timestamp,
        "root": str(ROOT),
        "estrutura": {},
        "modulos": {},
        "arquivos_criticos": {},
        "spawn_guard": {},
        "processos": {},
        "alertas": [],
        "saude_geral": True,
    }

    # ─── Estrutura ────────────────────────────────────────────────────────────
    for pasta in ESTRUTURA_OBRIGATORIA:
        caminho = ROOT / pasta
        existe = caminho.exists()
        resultado["estrutura"][pasta] = existe
        if not existe:
            resultado["alertas"].append(f"ESTRUTURA AUSENTE: {pasta}")
            resultado["saude_geral"] = False

    # ─── Módulos ──────────────────────────────────────────────────────────────
    for nome, caminho in MODULOS_ESPERADOS.items():
        existe = (ROOT / caminho).exists()
        resultado["modulos"][nome] = existe
        if not existe:
            resultado["alertas"].append(f"MÓDULO AUSENTE: {nome} ({caminho})")

    # ─── Arquivos Críticos ────────────────────────────────────────────────────
    for nome, caminho in ARQUIVOS_CRITICOS.items():
        existe = (ROOT / caminho).exists()
        resultado["arquivos_criticos"][nome] = existe
        if not existe:
            resultado["alertas"].append(f"ARQUIVO CRÍTICO AUSENTE: {nome}")

    # ─── Spawn Guard Check ────────────────────────────────────────────────────
    resultado["spawn_guard"] = checar_spawn_guard()
    if not resultado["spawn_guard"]["ok"]:
        resultado["saude_geral"] = False
        resultado["alertas"].append("SPAWN GUARD: vulnerabilidade detectada")

    # ─── Processos ────────────────────────────────────────────────────────────
    resultado["processos"]["notepad"] = checar_processos_notepad()
    if resultado["processos"]["notepad"]["rodando"]:
        instancias = resultado["processos"]["notepad"]["instancias"]
        resultado["alertas"].append(
            f"NOTEPAD ATIVO: {instancias} instância(s) rodando — verificar se foi aberto automaticamente"
        )

    return resultado


def imprimir_relatorio(r: dict) -> None:
    """Imprime relatório formatado no console."""
    print()
    print("═" * 65)
    print("  DIAGNÓSTICO DO SISTEMA ORIGEM.1")
    print(f"  {r['timestamp']}")
    print("═" * 65)

    print(f"\n📁 ROOT: {r['root']}")

    saude = "✅ SAUDÁVEL" if r["saude_geral"] else "❌ ATENÇÃO NECESSÁRIA"
    print(f"🏥 Saúde Geral: {saude}")

    print("\n── ESTRUTURA OBRIGATÓRIA ──────────────────────────────────")
    for pasta, ok in r["estrutura"].items():
        print(f"  {'✅' if ok else '❌'} {pasta}")

    print("\n── MÓDULOS DO SISTEMA ─────────────────────────────────────")
    for nome, ok in r["modulos"].items():
        print(f"  {'✅' if ok else '❌'} {nome}")

    print("\n── ARQUIVOS CRÍTICOS ──────────────────────────────────────")
    for nome, ok in r["arquivos_criticos"].items():
        print(f"  {'✅' if ok else '❌'} {nome}")

    print("\n── SPAWN GUARD ────────────────────────────────────────────")
    sg = r["spawn_guard"]
    print(f"  {'✅' if sg['ok'] else '❌'} Status: {'OK' if sg['ok'] else 'VULNERÁVEL'}")
    for detalhe in sg.get("detalhes", []):
        print(f"     {detalhe}")

    print("\n── PROCESSOS ATIVOS ───────────────────────────────────────")
    np = r["processos"].get("notepad", {})
    if np.get("rodando"):
        print(f"  ⚠️  notepad.exe rodando: {np['instancias']} instância(s)")
    else:
        print("  ✅ notepad.exe: não está rodando")

    if r["alertas"]:
        print("\n── ALERTAS ────────────────────────────────────────────────")
        for alerta in r["alertas"]:
            print(f"  ⚠️  {alerta}")

    print("\n" + "═" * 65)


if __name__ == "__main__":
    resultado = diagnosticar()
    imprimir_relatorio(resultado)

    # Salva resultado JSON
    saida = ROOT / "_sistema" / "logs" / f"diagnostico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    saida.parent.mkdir(parents=True, exist_ok=True)
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=2, ensure_ascii=False)
    print(f"\n📄 Relatório salvo em: {saida}")
