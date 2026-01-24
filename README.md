# Jarvis - Agentic AI System

Jarvis is a bidirectional conversational AI platform designed to execute complex tasks through natural voice interaction.

## Architecture

This project follows a strict layered architecture:

- **Layers**:
  - `layers/conversational`: STT, TTS, Wake Word.
  - `layers/dialogue`: Context management, Response strategy.
  - `layers/cognitive`: Intent parsing, Planning, Multi-agent orchestration.
  - `layers/execution`: OS manipulation, App control.
  
- **Core**:
  - `core/event_bus.py`: Event-driven communication.
  - `core/config.py`: Configuration management.
  
## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure environment:
   Create a `.env` file based on configuration needs.

3. Run:
   ```bash
   python main.py
   ```

## Development Rules

Refer to `.agent/rules/DEVELOPMENT_GUIDELINES.md` for coding standards.
