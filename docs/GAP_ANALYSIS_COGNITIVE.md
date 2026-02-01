# Gap Analysis: Cognitive Layer

## 1. Current Scenario (As-Is)

The system currently possesses a **"reflexive"** intelligence rather than a **"cognitive"** one. It reacts to immediate commands but cannot plan or remember context.

### Architecture
- **Location**: Core logic resides in `server/services/llm_service.py` and `conversation_manager.py`.
- **Status**: The dedicated `layers/cognitive` directory is currently a placeholder (empty).
- **Flow**: User Input -> API -> Intent Parser (LLM) -> Immediate Action.

### Capabilities
| Feature | Current Implementation | Limitation |
| :--- | :--- | :--- |
| **Intent Parsing** | `LLMService.parse_intent` uses a hardcoded prompt to classify into 3 buckets: `get_online_devices`, `file_search`, `command_execution`. | Rigid schema. Fails on complex or ambiguous requests that don't fit these 3 buckets. |
| **Context** | Pass-through. The API saves messages to SQL, but the LLM service constructs prompts by concatenating raw strings. | limited context window. No semantic search (RAG) or long-term memory. |
| **Planning** | None. 1 User Request = 1 LLM Action. | Cannot handle multi-step tasks like "Find all PDF files and move them to a generic folder". |
| **Tools** | Hardcoded mapping in `conversation_manager.py`. | LLM doesn't "know" tools; it just outputs JSON, and code tries to match it. |

---

## 2. Target State (To-Be)

The goal is to move to an **"Agentic"** architecture where the system plans, executes, and potentially self-corrects.

### Architecture
- **Location**: Logic moves to `layers/cognitive`.
- **Components**:
    - `Planner`: Decomposes high-level goals into a Directed Acyclic Graph (DAG) of steps.
    - `MemoryUnit`: Interface for Short-term (Redis) and Long-term (ChromaDB) memory.
    - `Reflector`: A critique loop that validates plans before execution.

### Capabilities (Phase 2 Goals)
| Feature | Implementation Goal | Benefit |
| :--- | :--- | :--- |
| **Dynamic Planning** | Implement a "Thinking" step that creates a plan: `Goal -> [Step 1, Step 2, Step 3]`. | Enables complex workflows (e.g., "Summarize the last 3 emails and send them to Slack"). |
| **Context Awareness** | RAG (Retrieval Augmented Generation) pipeline. | Agent remembers "My projects are in D:/Work" across sessions. |
| **Native Tool Use** | Use LLM Function Calling APIs (or structured JSON mode) to discover tools dynamically. | scalable. Adding a new tool doesn't require rewriting the main prompt. |
| **Reflection** | "Pre-flight check" for destructive actions. | Safety. Prevents accidental mass deletions or incorrect commands. |
