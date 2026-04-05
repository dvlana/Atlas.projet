# -*- coding: utf-8 -*-
"""
Skill: spawn_guard
==================
Controla abertura de processos externos com debounce, blocklist e auditoria.

Skill ID  : skill_spawn_guard
Categoria : security
Versão    : 1
Extraída de: _sistema/modules/spawn_guard.py + system_automation.py
"""

import os
import subprocess
import time
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("Origem.Skills.SpawnGuard")

# ─── CONFIGURAÇÃO DA SKILL ────────────────────────────────────────────────────
SKILL_META = {
    "id": "skill_spawn_guard",
    "name": "spawn_guard",
    "version": 1,
    "category": "security",
}

# Apps permanentemente bloqueados para abertura automática
BLOCKED_APPS: frozenset = frozenset({
    "notepad", "notepad.exe",
    "regedit", "regedit.exe",
})

# Mapa de nomes amigáveis → executáveis reais
APP_MAP: dict = {
    "calculadora":  "calc.exe",
    "paint":        "mspaint.exe",
    "explorador":   "explorer.exe",
    "terminal":     "wt",
    "vscode":       "code",
    "spotify":      "spotify",
    "chrome":       "chrome",
    "edge":         "msedge",
    "firefox":      "firefox",
    "discord":      "discord",
    "vlc":          "vlc",
}

_last_spawn: dict[str, float] = {}


def spawn_guard(
    app: str,
    debounce_seconds: float = 1.5,
    force: bool = False,
    caller: str = "unknown",
    audit_log: Path = None,
) -> str:
    """
    Abre um app com proteção completa.

    Args:
        app:              Nome amigável ou executável
        debounce_seconds: Janela de tempo mínima entre spawns do mesmo app
        force:            True = contorna debounce (NÃO contorna BLOCKED)
        caller:           Identificador de quem chamou (para auditoria)
        audit_log:        Path para arquivo de log de auditoria (opcional)

    Returns:
        str descrevendo resultado
    """
    global _last_spawn
    app_norm = app.strip().lower()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _audit(status: str, motivo: str) -> None:
        linha = f"{timestamp} | {status:18s} | app={app!r:<20s} | {motivo}\n"
        if audit_log:
            try:
                audit_log.parent.mkdir(parents=True, exist_ok=True)
                with open(audit_log, "a", encoding="utf-8") as f:
                    f.write(linha)
            except Exception:
                pass
        lvl = logger.warning if status == "BLOCKED" else logger.info
        lvl(f"[SPAWN-GUARD] {status}: app={app!r} | {motivo}")

    # 1. Blocklist
    if app_norm in BLOCKED_APPS:
        _audit("BLOCKED", f"app na blocklist | caller={caller}")
        return f"[SPAWN-GUARD] '{app}' bloqueado permanentemente."

    # 2. Debounce
    if not force:
        ultimo = _last_spawn.get(app_norm, 0.0)
        elapsed = time.monotonic() - ultimo
        if elapsed < debounce_seconds:
            _audit("DEBOUNCE", f"elapsed={elapsed:.2f}s < {debounce_seconds}s | caller={caller}")
            return f"[SPAWN-GUARD] '{app}' ignorado (debounce {elapsed:.1f}s)."

    # 3. Resolve executável
    executavel = APP_MAP.get(app_norm, app)

    # 4. Spawn
    try:
        os.startfile(executavel)
        _last_spawn[app_norm] = time.monotonic()
        _audit("OPENED", f"caller={caller} | exe={executavel!r}")
        return f"Abrindo '{app}'."
    except Exception:
        try:
            subprocess.Popen(["cmd", "/c", "start", "", executavel], shell=True)
            _last_spawn[app_norm] = time.monotonic()
            _audit("OPENED_FALLBACK", f"caller={caller} | exe={executavel!r}")
            return f"Abrindo '{app}' (fallback)."
        except Exception as e:
            _audit("ERROR", f"{e} | caller={caller}")
            return f"Erro ao abrir '{app}': {e}"
