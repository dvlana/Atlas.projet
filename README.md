# Origem.1 — Sistema Central de Desenvolvimento e Automação

> **Cérebro digital estruturado** — tudo vive aqui, tudo parte daqui.

---

## Estrutura do Sistema

```
/Origem.1
│
├── _sistema/                    ← NÚCLEO DO SISTEMA (criado automaticamente)
│   ├── core/
│   │   └── sistema.py           ← Boot central, health check, logging
│   ├── config/
│   │   └── sistema.json         ← Configuração global
│   ├── modules/
│   │   └── spawn_guard.py       ← Controle de spawn de processos externos
│   ├── utils/
│   │   └── utils.py             ← Singleton guard, debounce, safe_run
│   ├── debug/
│   │   └── diagnostico.py       ← Auto-diagnóstico do sistema
│   ├── logs/                    ← Logs rotativos (auto-gerados)
│   └── temp/                    ← Arquivos temporários (auto-limpos 24h)
│
├── jvs_auth_92kx-main/          ← BACKEND JARVIS
│   ├── Jarvis- Aula 01/         ← Agente principal
│   │   ├── agent.py
│   │   ├── automacao_jarvis.py  ← JarvisControl (orquestrador)
│   │   ├── automation/
│   │   │   ├── clap_detector.py         ← Bio-Claps (spawn guard ativo)
│   │   │   ├── automation_controller.py ← Dispatcher de automações
│   │   │   ├── system_automation.py     ← Controle do sistema (audit log)
│   │   │   ├── file_automation.py
│   │   │   ├── web_automation.py
│   │   │   └── ui_automation.py
│   │   └── prompts.py
│   ├── Aula automacao/Controle_PC/      ← Módulo legado de controle de PC
│   ├── Jarvis Mem0/                     ← Sistema de memória
│   └── Layout Jarvis/                   ← Referências de layout
│
├── agent-starter-react-main/    ← FRONTEND (Next.js / Atlas UI)
│
└── livekit/                     ← SERVIDOR LIVEKIT (binário)
```

---

## Comandos Principais

```bash
# Inicializar o sistema e ver status
python _sistema/core/sistema.py

# Rodar diagnóstico completo
python _sistema/debug/diagnostico.py

# Iniciar backend Jarvis
cd "jvs_auth_92kx-main/Jarvis- Aula 01"
python agent.py

# Iniciar frontend
cd agent-starter-react-main
pnpm dev
```

---

## Regras Fundamentais

| Regra | Descrição |
|-------|-----------|
| 🏠 **Raiz única** | Tudo dentro de `/Origem.1` — nada fora |
| 🛡️ **Spawn Guard** | Nenhum app abre automaticamente sem `set_action()` explícito |
| 📋 **Audit Log** | Todo spawn externo é registrado em `_sistema/logs/spawn_audit.log` |
| 🔄 **Debounce** | Processos repetitivos têm proteção de re-trigger |
| 🔍 **Auto-diagnóstico** | `diagnostico.py` detecta vulnerabilidades e missing modules |

---

## Proteções Ativas

### Bio-Claps (clap_detector.py)
- `default_app = ""` → nenhum app abre por padrão
- `_BLOCKED_APPS = {"notepad", "notepad.exe", ""}` → lista de bloqueio permanente
- **Spawn Guard** no `monitor_loop()` → verifica antes de qualquer spawn

### SpawnGuard (_sistema/modules/spawn_guard.py)
- Lista `BLOCKED` com apps proibidos
- Debounce de 1.5s entre spawns do mesmo app
- Log auditável em `_sistema/logs/spawn_audit.log`

---

## Como Ativar Bio-Claps

```python
from automacao_jarvis import JarvisControl
import asyncio

jarvis = JarvisControl()
jarvis.set_clap_action("calculadora")   # ← configuração EXPLÍCITA obrigatória
loop = asyncio.get_event_loop()
jarvis.start_bio_claps(loop)
```

---

## Logs

| Arquivo | Conteúdo |
|---------|----------|
| `_sistema/logs/origem_YYYY-MM-DD.log` | Log geral do sistema (rotativo) |
| `_sistema/logs/spawn_audit.log` | Auditoria de todos os spawns |
| `_sistema/logs/diagnostico_*.json` | Resultado dos diagnósticos |
