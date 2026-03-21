# Theia Guard — Approval Gate Extension

## Purpose
Intercepts high-risk tool calls and requires explicit user approval before execution.
Safety lives in architecture, not in prompts.

## How it works
- LOW risk: auto-execute
- MEDIUM risk: single approval via Telegram/phone
- HIGH risk: double approval required
- CRITICAL risk: blocked entirely

## Trigger
Any destructive operation: rm, sudo, DELETE, DROP, dd, mkfs

## Reference
https://github.com/ismailkarabulut-lang/theia-guard
