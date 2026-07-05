# Agent Orchestrator Platform

This repository contains an experimental agentic web-processing pipeline. The pipeline takes a URL and a task, plans the next action, executes scraping or extraction tools, validates progress through a critic, and returns a final summarized result.

The project also contains a separate `LLM Guardrail Engine`, which was built as an independent service for schema validation, retries, repair prompts, confidence scoring, escalation, and run observability around LLM calls.

## Current Agentic Pipeline

The main pipeline is coordinated by `orchestrator/manager.py`.

At a high level, the flow is:

```text
User payload
  -> WorkflowManager
  -> PlannerAgent
  -> ExecutorAgent
  -> ToolRegistry
  -> pipeline tools
  -> CriticAgent
  -> retry, fallback, or finish
  -> final result
```

The input payload is expected to contain:

```json
{
  "url": "https://example.com",
  "task": "Extract top headlines and summarize",
  "task_id": "optional-id"
}
```

The main state object is `AgentState` in `state.py`. It carries the pipeline context across steps:

- `goal`
- `url`
- `html`
- `headlines`
- `summary`
- `scrape_strategy`
- `extract_strategy`
- `last_action`
- `last_critic_feedback`
- `attempts`
- `errors`

The pipeline uses a planner-executor-critic loop:

1. `PlannerAgent` decides the next action from the current state.
2. `ExecutorAgent` runs the selected tool from `ToolRegistry`.
3. The selected tool mutates `AgentState`.
4. `CriticAgent` validates whether the state is good enough to continue.
5. If the critic rejects the result, the manager applies fallback logic or lets the planner try another action.
6. The loop stops when the planner returns `finish` or the maximum step count is reached.

## Registered Tools

The current tool registry registers:

- `fetch_static`: fetches page HTML using a static request.
- `fetch_selenium`: fetches rendered HTML when static scraping is blocked or insufficient.
- `extract_rule`: extracts headlines with rule-based parsing.
- `extract_llm`: extracts headlines using an LLM call.
- `summarize`: summarizes the extracted content.

The pipeline currently follows a practical fallback pattern:

- Try static fetching first.
- Fall back to Selenium when static fetching appears blocked or JavaScript-rendered.
- Try rule-based extraction first.
- Fall back to LLM extraction when rule extraction fails.
- Summarize extracted headlines or available HTML.

## Critic and Recovery Behavior

`CriticAgent` acts as the quality-control layer for the agentic loop. It checks for conditions such as:

- rule extraction failure
- static scraping blocks
- repeated LLM extraction failure
- invalid LLM output
- low-quality static extraction
- non-recoverable LLM failures

The critic does not directly execute tools. It gives feedback to the workflow manager, and the manager decides whether to continue, retry, fallback, or finish.

This separation is useful because it keeps execution and validation independent:

```text
Planner decides intent
Executor performs action
Critic validates result
Manager controls loop and recovery
```

## MCP Implementation Attempt

The repository includes an MCP experiment in `mcp_runtime/`.

The intended MCP architecture was:

```text
MCP Client
  -> MCP Server
  -> fetch_static(state)
  -> fetch_selenium(state)
  -> extract_rule(state)
  -> extract_llm(state)
  -> summarize(state)
  -> updated AgentState
```

The implementation wrapped the existing pipeline tools with `FastMCP` in `mcp_runtime/app.py`. Each MCP tool accepted a serialized `state` dictionary, converted it into `AgentState`, executed the corresponding local tool, then returned the updated state as a dictionary.

Example MCP-style tool boundary:

```text
dict state
  -> dict_to_state()
  -> local tool.run(agent_state)
  -> state_to_dict()
  -> dict state
```

## Why MCP Did Not Fit This Pipeline

The MCP implementation was technically possible for exposing individual tools, but it did not fit the current agentic pipeline cleanly.

The main issue was that this pipeline is stateful and loop-driven, while MCP tool calls are better suited to independent, externally callable tool boundaries.

The current manager depends on:

- in-memory `AgentState` mutation
- repeated planner-executor-critic cycles
- direct fallback logic inside the workflow manager
- local exception handling
- shared attempt counters
- critic feedback from previous steps
- final normalization of errors and status

Moving each tool call behind MCP introduced friction because the core orchestration still needed local control over state, retries, critic feedback, and fallback behavior. Instead of simplifying the architecture, MCP created an extra serialization boundary around tools that were already tightly coupled to the pipeline state.

The MCP approach also made the failure model harder to manage. In the local pipeline, an exception from `extract_rule` can immediately trigger `extract_llm`, and a failed static fetch can fall back to Selenium. Through MCP, those failures would need to be serialized, returned, interpreted, and re-applied to the local workflow manager without losing context.

In short:

```text
MCP worked as a tool wrapper,
but it did not work well as the backbone of this stateful agentic loop.
```

## LLM Guardrail Engine

The `LLM Guardrail Engine` is a separate project inside this repository. It is designed to treat LLMs as unreliable components and enforce deterministic behavior around them.

Its current capabilities include:

- input prechecks
- schema-first output validation with Pydantic
- invalid JSON detection
- schema violation handling
- retry and repair prompts
- confidence scoring
- FAST to STRONG model escalation
- semantic validation
- batch-safe execution
- JSON run artifacts
- FastAPI endpoints

The current guardrail engine is focused on summary generation, with endpoints such as:

- `POST /generate-summary`
- `POST /generate-summary/batch`

Internally, `guardrails/engine.py` runs:

```text
input text
  -> precheck
  -> prompt construction
  -> FAST model call
  -> validation
  -> confidence scoring
  -> optional STRONG model escalation
  -> artifact writing
  -> normalized response
```

## How the Guardrail Engine Can Integrate with the Main Pipeline

The guardrail engine is a better fit than MCP for improving the current pipeline because the main risk is not tool discovery. The main risk is unreliable LLM behavior.

The guardrail engine should be integrated at LLM boundaries, not around every pipeline tool.

Recommended integration points:

1. `PlannerAgent`
2. `ExtractLLMTool`
3. `SummarizeTool`

These are the places where the system depends on model output and therefore needs validation, repair, escalation, and observability.

## Integration Option 1: Local Python Adapter

The simplest integration is to import the guardrail engine as a local Python module and wrap LLM calls inside a small adapter.

Recommended adapter:

```text
main pipeline
  -> GuardrailClient
  -> guardrails.run_engine()
  -> validated response
  -> AgentState mutation
```

For summarization, `SummarizeTool` can call the guardrail engine instead of calling an LLM directly.

Example target behavior:

```text
headlines/html
  -> SummarizeTool
  -> GuardrailClient.generate_summary(text)
  -> validated title + summary
  -> state.summary
```

Benefits:

- no HTTP server required
- simpler debugging
- direct Python exceptions
- easier access to run artifacts
- lower latency than HTTP

Tradeoff:

- the guardrail engine becomes a local dependency of the main pipeline
- path and import structure must be cleaned up

## Integration Option 2: FastAPI Service Boundary

The guardrail engine can also remain a separate service.

Recommended service flow:

```text
main pipeline
  -> HTTP request
  -> LLM Guardrail Engine FastAPI
  -> validated response
  -> main pipeline updates AgentState
```

This keeps the guardrail engine independently deployable.

Benefits:

- clear service boundary
- independent scaling
- language-agnostic access
- easier future deployment as a shared guardrail service

Tradeoff:

- network overhead
- service availability must be handled
- request and response contracts must stay versioned

## Recommended Integration Design

The recommended design is to keep the agentic workflow local and integrate guardrails only at LLM call boundaries.

```text
WorkflowManager
  -> PlannerAgent
       -> Guardrail-protected structured decision
  -> ExecutorAgent
       -> fetch_static
       -> fetch_selenium
       -> extract_rule
       -> extract_llm
            -> Guardrail-protected headline extraction
       -> summarize
            -> Guardrail-protected summary generation
  -> CriticAgent
  -> final result
```

This keeps the strongest parts of both systems:

- the main pipeline owns state, planning, fallback, and tool execution
- the guardrail engine owns LLM reliability, schema validation, retries, escalation, and observability

## Proposed Guardrail Contracts

The guardrail engine should expose task-specific contracts instead of only a generic summary contract.

Suggested contracts:

### Planner Decision Contract

```json
{
  "action": "fetch_static | fetch_selenium | extract_rule | extract_llm | summarize | finish",
  "reason": "short explanation"
}
```

### Headline Extraction Contract

```json
{
  "headlines": [
    "headline one",
    "headline two"
  ]
}
```

### Summary Contract

```json
{
  "title": "short title",
  "summary": "two sentence summary"
}
```

Each contract should have:

- a Pydantic schema
- a prompt template
- retry rules
- confidence scoring
- escalation policy
- artifact logging

## Suggested Implementation Steps

1. Create a `GuardrailClient` in the main pipeline.
2. Add methods for `generate_summary`, `extract_headlines`, and `decide_next_action`.
3. Start with `SummarizeTool`, because summary generation is already supported by the guardrail engine.
4. Add a headline extraction schema to the guardrail engine.
5. Replace direct LLM parsing in `ExtractLLMTool` with guardrail-protected extraction.
6. Add a planner decision schema and route `PlannerAgent` LLM decisions through guardrails.
7. Keep `CriticAgent` as a pipeline-level validator, not a replacement for guardrails.
8. Normalize guardrail failures into `state.errors` using the existing recoverable/non-recoverable error format.

## Failure Handling Strategy

Guardrail failures should map into the pipeline's existing error model.

Example mapping:

```text
INVALID_JSON
  -> recoverable=True
  -> retry or repair inside guardrail engine

SCHEMA_VIOLATION
  -> recoverable=True
  -> repair or escalate

REPAIR_EXHAUSTED
  -> recoverable=True or False depending on task
  -> pipeline fallback if available

LLM_AUTH_FAILURE
  -> recoverable=False
  -> stop LLM-dependent path

LLM_QUOTA_EXCEEDED
  -> recoverable=False
  -> stop or defer
```

For example, if guardrailed headline extraction fails after repair and escalation, the pipeline can still return `completed_with_errors` if it has enough content for a fallback summary. If the planner LLM fails, the pipeline can use the deterministic `_fallback_decide` logic already present in `PlannerAgent`.

## Final Architecture Direction

MCP should not be the primary runtime mechanism for this pipeline right now. The current system needs tight local control over mutable state, retries, fallbacks, and critic feedback.

The LLM Guardrail Engine should be integrated as a reliability layer around LLM calls.

The target architecture is:

```text
Agentic pipeline stays stateful and local.
MCP remains optional for future external tool exposure.
Guardrails protect every LLM boundary.
Critic validates pipeline-level progress.
WorkflowManager remains the source of orchestration truth.
```

This gives the project a cleaner separation of responsibilities:

- MCP: optional external tool interface
- WorkflowManager: orchestration and recovery
- ToolRegistry: local tool execution
- CriticAgent: pipeline validation
- LLM Guardrail Engine: safe, validated, observable LLM output

