# How to Connect a Second Device (Mac) to Jarvis Central Server

This guide will help you connect your Mac (this device) to the Central Jarvis Server running on another machine.

## Prerequisites

- Both devices must be on the **same Wi-Fi/Network**.
- Python 3.10+ installed on this Mac.

---

## Step 1: Get Central Server IP Address

**On your Central Device (the one running the server):**

1.  Open a terminal/command prompt.
2.  Run `ipconfig` (Windows) or `ifconfig` (Mac/Linux).
3.  Look for the **IPv4 Address** (usually looks like `192.168.1.x` or `10.0.0.x`).
    - _Note this down._

---

## Step 2: Configure This Device

1.  Open the `.env` file in your `jarvis` folder on this Mac.
2.  Update the following fields:

```properties
# Network Configuration
# REPLACE 0.0.0.0 with the IP you found in Step 1
CENTRAL_SERVER_HOST=192.168.1.X  <-- PUT CENTRAL IP HERE

# Device Identity (Must be unique)
DEVICE_ID=mac-agent-01           <-- Give this device a unique name
DEVICE_NAME=My Mac Agent
IS_CENTRAL_DEVICE=false
```

3.  Save the file.

---

## Step 3: Install Dependencies

If you haven't already installed the required libraries:

```bash
pip install -r requirements.txt
```

---

## Step 4: Run the Agent

To start the connection to the central server:

```bash
python3 -m agent.desktop_agent
```

## Verification

1.  You should see logs saying **"Connected to Central Server"**.
2.  On your Central Server logs, you should see **"Device connected: mac-agent-01"**.

---

## Troubleshooting

- **Connection Refused?**
  - Ensure the Central Server is running (`docker-compose up` or `python main.py`).
  - Check if a Firewall on the Central Device is blocking port `8000` or `8001`.
- **"Env not found"?**
  - Make sure you are running the command from the root `jarvis` folder.

# Open Chrome on your Mac

curl -X POST http://localhost:8000/v1/commands/execute \
 -H "Content-Type: application/json" \
 -d '{
"device_id": "mac-agent-01",
"action": "open_app",
"params": {"app_name": "chrome"}
}'

# Make your Mac speak

curl -X POST http://localhost:8000/v1/commands/execute \
 -H "Content-Type: application/json" \
 -d '{
"device_id": "mac-agent-01",
"action": "run_command",
"params": {"command": "say Hello from Jarvis"}
}'

curl -X POST http://localhost:8000/v1/conversations/chat \
 -H "Content-Type: application/json" \
 -d '{"speaker": "user", "content": "Which devices are online?"}'

---

## Available Features (Second Device)

Since this device is running the **Desktop Agent**, it can perform the following actions commanded by the Central Server:

1.  **Open Applications** (`open_app`)
    - **Mac**: Opens apps like Chrome, Terminal, VS Code.
    - **Windows**: Opens standard executables.
    - _Usage_: "Open Chrome on Mac" (via Voice or Text on Central).

2.  **Execute System Commands** (`run_command`)
    - Runs shell commands (bash/zsh on Mac, cmd on Windows).
    - _Examples_: `say "Hello"`, `ls -la`, `mkdir project`.
    - **Warning**: This gives full shell access, so be careful.

3.  **File System Access** (`file_list`)
    - Allows the Central Server to browse files on this device.
    - Useful for unnecessary file indexing or remote management.

---

## How to Connect Mobile (Android/iOS)

Currently, there is no dedicated native mobile app, but you can control Jarvis via the **Web Interface**.

### 1. Connect to Wi-Fi

Ensure your phone is on the **same Wi-Fi network** as the Central Server.

### 2. Access the Control Panel (API)

1.  Open Chrome/Safari on your phone.
2.  Navigate to: `http://<CENTRAL_IP>:8000/docs`
    - _Replace `<CENTRAL_IP>` with the IP from Step 1 (e.g., `192.168.1.5`)._
3.  You will see the Swagger UI.

### 3. Send Commands from Phone

To send a voice command or text message to Jarvis/Central from your phone:

1.  Scroll to **POST /v1/conversations/messages**.
2.  Click **Try it out**.
3.  Enter your message:
    ```json
    {
      "speaker": "user",
      "content": "Open Chrome on my Mac"
    }
    ```
4.  Click **Execute**.
    - _Jarvis will receive this text and route the command to your Mac Agent._
