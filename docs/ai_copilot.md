# AI Security Copilot Architecture

AegisOne incorporates a dedicated **AI Security Copilot** designed to translate complex, low-level behavioral feature sets, database metrics, and alert logs into clear, actionable incident response investigations.

---

## 1. System Architecture

```
         +-------------------------------------------+
         |               React UI                    |
         +-------------------------------------------+
               |                               ^
               | (alert_id)                    | (Structured Report JSON)
               v                               |
         +-------------------------------------------+
         |             CopilotEngine                 |
         +-------------------------------------------+
               |                               |
               | (Assemble Context)            | (Binds Provider)
               v                               v
    +-----------------------+       +---------------------+
    |  PostgreSQL Database  |       |     LLMProvider     |
    +-----------------------+       +---------------------+
                                               |
                                     +---------+---------+
                                     |                   |
                                     v                   v
                            +-----------------+ +-----------------+
                            | OpenAIProvider  | |FallbackProvider |
                            +-----------------+ +-----------------+
```

---

## 2. Abstraction Layer & Interfaces

The system implements the **Provider Design Pattern**, isolating the core FastAPI service layers from specific LLM vendors through a strict abstract base class `LLMProvider`:

1. **`LLMProvider` (Abstract Contract)**: Defines standard methods (`explain`, `recommend`, `explain_timeline`, `executive_summary`, `generate_report`).
2. **`OpenAIProvider` (OpenAI Completion client)**: Connects to configurable OpenAI-compatible HTTP endpoints.
3. **`FallbackProvider` (Expert Rule-based Engine)**: Provides expert, deterministic security triaging based on alert patterns and logged timelines. This guarantees out-of-the-box system operation in local demo scopes without external billing keys.

---

## 3. Context Assembly Pipeline

Before querying the LLM provider, the `CopilotEngine` aggregates context:
- **Alert Details**: Extracting severity, database targets, timestamps, and trigger details.
- **Affected Node Profile**: Querying metadata parameters (IPs, location, vendor, role details).
- **Incident Progress Timeline**: Fetching logs from the Threat Simulation engine to build chronological sequences of activities.

---

## 4. Prompt Engineering & System Prompts

For OpenAI-compatible providers, the engine binds specialized system prompts:

- **System Persona**:
  > You are an experienced industrial Security Operations Center (SOC) incident responder analyst.
- **Investigation Prompt**:
  > Analyze the following security alert ... Provide a concise, professional explanation covering: What happened, Why it is suspicious, Which behaviors deviated, Affected assets/users, and Confidence level.
- **Timeline Narrator**:
  > Translate the following raw event timeline into a concise human-readable narrative summary. Focus on explaining the flow of actions logically.
