# Jarvis Project Development Guidelines & Rules

This document establishes the engineering standards, architectural rules, and coding practices for the Jarvis Agentic AI System. These rules must be followed throughout the development lifecycle to ensure code quality, reusability, and robust state management.

---

## 1. Code Quality & Standards

### 1.1 Technology Stack
*   **Language**: Python 3.11+
*   **Asynchronous Core**: All I/O-bound operations (Network, File Ops) must use `asyncio` and `aiohttp`. Blocking calls in the main event loop are strictly forbidden.
*   **Type Strategy**: Strict static typing is required.
    *   Use `typing` module (`List`, `Dict`, `Optional`, `Protocol`).
    *   Function signatures must have type hints. `def my_func(x: int) -> str:`
*   **Documentation**:
    *   All classes and public methods must have docstrings (Google or NumPy style).
    *   Complex logic must include inline comments explaining the *why*, not just the *how*.

### 1.2 Testing & Verification
*   **Unit Tests**: Core components (Dialogue Manager, Parsers) must have unit tests.
*   **Integration Tests**: Major flows (e.g., "Voice -> Intent -> Action") require integration tests.
*   **Verification Agents**: Use the `Verifier Agent` pattern to validate the outcome of execution tasks programmatically.

---

## 2. Architectural Rules & Modularity

### 2.1 Layer Boundaries
Respect the system architecture layers. Dependencies should flow downwards:
1.  **User Interaction Layer** (STT/TTS)
2.  **Conversational Interface**
3.  **Dialogue Management**
4.  **Cognitive Orchestration** (LLM/Planning)
5.  **Multi-Agent Ecosystem**
6.  **Execution Layer** (OS/Apps)

*Do not import Execution Layer classes directly into the User Interaction Layer.*

### 2.2 Code Reusability
*   **Protocols over Concretions**: Define agents as Protocols (Interfaces). E.g., `ExecutorAgent` interface allows different implementations (FileExecutor, NetworkExecutor).
*   **Shared Utilities**: Place common logic (logging validation, date handling) in a `utils/` generic package.
*   **Component Isolation**: Agents should be self-contained modules that communicate via the Event Bus or well-defined method calls, minimizing shared global state.

---

## 3. State & Context Management

### 3.1 Conversation Context (`ConversationContext`)
*   **One Truth**: The `ConversationContext` object is the single source of truth for the active session.
*   **Content**: Must track:
    *   `history`: Multi-turn dialogue history.
    *   `active_goal`: The current objective.
    *   `pending_confirmations`: Actions waiting for user approval.
    *   `user_preferences`: Learned or configured settings.
*   **Persistence**: Context changes must be checkpointed to the persistent store (SQLite/PostgreSQL) to survive system restarts.

### 3.2 Global State & Event Bus
*   **Decoupling**: Use Redis Pub/Sub (or internal Event Bus) for cross-component communication.
    *   *Example*: The `Executor` publishes a `task_completed` event; the `DialogueManager` subscribes to it to notify the user.
*   **Stateless Execution**: Executors should not hold state between tasks unless necessary. They should receive all context needed in the `task` payload.

---

## 4. Agentic Behavior & Orchestration

### 4.1 Planning & Execution Loop
1.  **Understand**: Parse Intent.
2.  **Plan**: Decompose into a `TaskGraph`.
3.  **Execute**: Run tasks (Sequential or Parallel).
4.  **Verify**: Validate results.
5.  **Report**: Speak status to user.

### 4.2 Failure Handling (Mandatory)
Every execution component must implement the **Failure Recovery Protocol**:
1.  **Detect**: Catch exceptions and verify states.
2.  **Classify**: Identify `FailureType` (Network, Permission, State).
3.  **Recover**:
    *   *Transient*: Retry with exponential backoff.
    *   *Permission*: Ask user for elevation.
    *   *Ambiguity*: Ask user for clarification.
    *   *Fatal*: Fail gracefully and inform user.

---

## 5. Security & Safety

### 5.1 Permission Tiers
All actions must be checked against the `PermissionManager`:
*   **Tier 1 (Forbidden)**: Never execute (e.g., broad system formatting).
*   **Tier 2 (Sensitive)**: **Require Verbal Confirmation** (e.g., deleting files, sending emails, payments).
*   **Tier 3 (Standard)**: Auto-allow (e.g., reading files, searching web).

### 5.2 Confirmation Loops
*   If an action is Tier 2, the system *must* pause, explain the action to the user ("I am about to delete 5 files..."), and wait for a clear "Yes" confirmation.

