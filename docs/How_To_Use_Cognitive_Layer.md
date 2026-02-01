# How to Use the Cognitive Layer

The Jarvis system now has a **Cognitive Layer** enabled. This works automatically in the background.

## 1. Wait for Installation
The system is currently installing new dependencies (`chromadb`, `networkx`). Please wait for the terminal to finish the installation process.

## 2. Restart the Server
Once the installation is complete, you must restart the Jarvis server to load the new modules.
Run:
```bat
run_jarvis_310.bat
```

## 3. Verify It Works
You don't need to learn new commands. The agent now plans automatically.

**Try asking complex questions:**
- **Reflexive (Old way)**: "Open Calculator" (Still works fast)
- **Cognitive (New way)**: "I need to analyze some numbers, please open the calculator for me." (Agent will Parse -> Plan -> Execute)

**Try Memory:**
1. "My project code is 1234."
2. "What is my project code?"

**Try Safety Checks:**
- "Delete all files in C:/" -> The **Reflector** should reject this plan.
