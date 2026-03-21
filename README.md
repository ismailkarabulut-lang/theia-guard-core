# Theia Guard Core
### OpenClaw fork — Human-in-the-Loop Execution Layer

> **Safety as architecture, not suggestion.**  
> LLMs forget safety instructions. Systems shouldn't.

![Status](https://img.shields.io/badge/status-early%20prototype-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Fork](https://img.shields.io/badge/fork-openclaw-blue)

---

## What is this?

OpenClaw is a powerful personal AI agent.  
It can execute tasks, automate workflows, and interact with real systems.

But power without control is fragile.

Recently, a Meta AI security researcher, Summer Yue, shared a moment that made this clear.  
She asked her agent to organize her inbox — with a simple instruction:

> *"Ask before deleting anything."*

The agent didn't ignore her.  
It **lost the instruction**.

Under context pressure, the safety constraint disappeared — and the agent started deleting emails without confirmation.  
She had to physically reach her machine and stop it mid-execution.

That moment revealed something deeper:

> AI systems don't break rules.  
> They forget them.

---

## What is Theia Guard Core?

Theia Guard Core is OpenClaw with a fundamental shift:

> The agent remains powerful —  
> but it no longer decides when it is safe to act.

An **external approval layer** sits between intention and execution.

The agent can plan.  
It can reason.  
It can propose actions.

But it cannot execute critical operations  
**without explicit user approval.**

Not by instruction.  
By design.

---

## What changed?

Almost nothing — and that's the point.

- OpenClaw remains fully intact
- All existing tools, channels, and integrations still work
- No prompt engineering required

Only one addition:

```
extensions/theia-guard/
├── gatekeeper.py        # Core approval gate logic
├── telegram_approval.py # Mobile approval channel
└── SKILL.md             # Extension manifest
```

A single layer that changes the control model completely.

---

## How the Gate Works

Every action proposed by the agent passes through a risk pipeline:

| Risk Level | Example Actions | Response |
|---|---|---|
| 🟢 LOW | `ls`, `cat`, read operations | Auto-execute |
| 🟡 MEDIUM | `apt install`, `pip install`, `mv` | Single approval via Telegram |
| 🔴 HIGH | `rm -rf`, `chmod`, `sudo rm` | Double confirmation required |
| ⛔ CRITICAL | `rm -rf /`, `mkfs`, `dd if=/dev/zero` | Blocked entirely |

**Key principle:**

> The agent does not decide when to wait.  
> The system enforces it.

The Approval Gate operates **outside the agent's context window.**  
No compression. No override. Immutable.

---

## Proof of Concept (Live)

The core gating logic is implemented and working:

```bash
# Run the approval gate
python3 extensions/theia-guard/gatekeeper.py

# Test risk classification
> ls                    # LOW  — auto executes
> apt install nginx     # MEDIUM — Telegram approval
> rm -rf /tmp/test      # MEDIUM — Telegram approval  
> rm -rf /              # CRITICAL — blocked
```

Mobile approval via Telegram:

```bash
# Run the Telegram bot in a second terminal
python3 extensions/theia-guard/telegram_approval.py
```

---

## Architecture

```
┌─────────────────────────────────────────┐
│  User / AI Agent                        │
│  Proposes an action                     │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Risk Classifier                        │
│  LOW / MEDIUM / HIGH / CRITICAL         │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Approval Gate  ← operates outside      │
│  • Telegram notification                │   agent context
│  • Waits for explicit confirmation      │
│  • Cannot be bypassed by the agent      │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Sandbox Execution                      │
│  Only approved actions run              │
│  Full audit log maintained              │
└─────────────────────────────────────────┘
```

---

## Philosophy

We've been treating AI safety as a behavioral problem:

> *"Be careful."*  
> *"Ask before acting."*  
> *"Don't make mistakes."*

But behavior lives inside the model —  
and models forget.

Theia Guard takes a different approach:

> Safety should not live in prompts.  
> **Safety should live in architecture.**

A calculator doesn't *remember* not to divide by zero.  
It is **designed** not to.

---

## Status & Roadmap

| Phase | Description | Status |
|---|---|---|
| 0 | Problem definition & architecture | ✅ Complete |
| 1 | Minimal approval gate (gatekeeper.py) | ✅ Working |
| 2 | Telegram mobile approval channel | ✅ Working |
| 3 | Risk classification engine | ✅ Working |
| 4 | Full OpenClaw execution layer integration | 🔄 In progress |
| 5 | Async approval (non-blocking execution) | 📋 Planned |
| 6 | Web UI for approval management | 📋 Planned |

---

## Related

- [Theia Guard](https://github.com/ismailkarabulut-lang/theia-guard) — original concept and architecture
- [OpenClaw](https://github.com/openclaw/openclaw) — the agent runtime this forks
- [OpenClaw Issue #51203](https://github.com/openclaw/openclaw/issues/51203) — the feature request that started this

---

## Contributing

This is an early-stage architectural implementation.  
The problem is real. The approach is validated. The execution layer is being built.

If you've ever panicked watching an agent do something irreversible — this is for you.

Open an issue. Fork it. Build with us.

---

*Theia Guard Core is an independent fork. Not affiliated with the OpenClaw core team.*
