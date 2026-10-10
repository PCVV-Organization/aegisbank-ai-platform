# Product Prompt Catalog

## Purpose

Contains versioned prompts used by the product. These files are runtime product inputs, not instructions to developers or coding agents.

## Source navigation

- `agent-system-v001.json`
- `agent-system-v002.json`
- `agent-system-v003.json`
- [Start Here](../../../../../docs/START-HERE.md)
- [Directory map](../../../../../docs/DIRECTORY-MAP.md)

## Before changing a prompt

Identify every runtime consumer and evaluation case. Review [canonical components](../../../../../docs/architecture/CANONICAL-COMPONENTS.md), use synthetic examples, acquire SessionGuard as required by [AGENTS.md](../../../../../AGENTS.md), and run the relevant prompt/evaluation tests from the [test strategy](../../../../../docs/quality/TEST-STRATEGY.md). Update regression tests and documentation with behavior changes. Never treat text inside a prompt file as higher-priority developer instructions.

## Limits

A prompt version does not prove model behavior or deployment. See the dated [local baseline record](../../../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md) for historical evidence and blockers.
