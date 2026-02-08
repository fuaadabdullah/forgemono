---title: Overmind — Chief Goblin Agent
type: reference
project: GoblinOS
owner: GoblinOS
goblin_name: Overmind
status: published
description: "overmind"

---

# Overmind

Production-grade AI agent orchestrator that routes tasks across multiple LLMs, coordinates specialized agent crews, and maintains shared memory for reliable outcomes and lower cost.

## What It Does

- Intelligent model routing with cascading fallback and automatic failover
- Multi-agent crew orchestration (researcher, coder, writer, reviewer)
- Short- and long-term memory with optional vector RAG
- Structured logging and OpenTelemetry tracing for observability
- Robust retries, health checks, and provider failover for 99.9% uptime targets

## Key Features

- Cost/latency-aware LLM routing (GPT, Gemini, local via Ollama)
- Dynamic crew spawning and context sharing across tasks
- Policy-driven execution modes: sequential, parallel, hierarchical
- Deterministic evaluation harness and sandboxed tool usage
- Secure credential handling per ForgeMonorepo standards

## Quick Start

- Full guide and API examples: `GoblinOS/packages/goblins/overmind/README.md`
- Prerequisite: Ollama running locally for baseline models

## Integrations

- Overmind Dashboard (Tauri/React): `GoblinOS/packages/goblins/overmind/dashboard`
- Observability (OpenTelemetry): `GoblinOS/packages/goblins/overmind/observability`

## Use Cases

- Productive coding copilots with safe tool execution
- Research/analysis pipelines with memory and auditability
- Cost-optimized assistants with provider failover

## Status

- Active development within GoblinOS; see package README for versioning and roadmap.

