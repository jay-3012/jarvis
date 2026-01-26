# Quick Start Guide - Testing Phase 1

## 1. Start All Services

```bash
# Start Docker services
docker-compose up -d

# Wait for all services to be healthy (30-60 seconds)
docker-compose ps
```

## 2. Verify Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status":"healthy","checks":{"database":true,"redis":true,"ollama":true}}
```

## 3. Register a Device

```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "windows-laptop",
    "device_type": "desktop",
    "device_name": "My Windows Laptop"
  }'
```

Save the `pairing_code` from the response.

## 4. Generate Access Token

```bash
curl -X POST http://localhost:8000/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "windows-laptop",
    "pairing_code": "YOUR_PAIRING_CODE_HERE"
  }'
```

## 5. Test Desktop Agent

```bash
# Install dependencies first (if not done)
.\install_dependencies.bat

# Run the agent
.\run_agent.bat
```

The agent will:
- Connect to Central Server via WebSocket
- Send heartbeat pings every 30 seconds
- Listen for commands from server

## 6. Test Command Execution

In another terminal:

```bash
curl -X POST http://localhost:8000/v1/commands/execute \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "windows-laptop",
    "action": "test_command",
    "params": {"message": "Hello from server!"}
  }'
```

Check the agent terminal - you should see the command received and executed.

## 7. Test Conversations

```bash
# Create a conversation
curl -X POST http://localhost:8000/v1/conversations \
  -H "Content-Type: application/json"

# Save the conversation_id from response

# Add a message
curl -X POST http://localhost:8000/v1/conversations/CONVERSATION_ID/messages \
  -H "Content-Type: application/json" \
  -d '{
    "speaker": "user",
    "content": "Hello, Jarvis!"
  }'

# Get messages
curl http://localhost:8000/v1/conversations/CONVERSATION_ID/messages
```

## 8. View API Documentation

Open in browser: `http://localhost:8000/docs`

This provides an interactive Swagger UI for testing all endpoints.

## 9. Test LLM (Ollama)

```bash
# Direct Ollama test
curl http://localhost:11434/api/generate \
  -d '{
    "model": "llama3.2:1b",
    "prompt": "What is 2+2?",
    "stream": false
  }'
```

Note: First request may take 30-60 seconds as the model loads into memory.

## Troubleshooting

### Agent won't connect
- Check if Docker services are running: `docker-compose ps`
- Check if API is healthy: `curl http://localhost:8000/health`
- Verify device is registered: `curl http://localhost:8000/v1/auth/devices`

### Ollama not responding
- Check Ollama logs: `docker-compose logs ollama`
- Model may still be loading (wait 60 seconds)
- Verify model is pulled: `docker exec -it jarvis-ollama ollama list`

### Database errors
- Check PostgreSQL logs: `docker-compose logs db`
- Restart services: `docker-compose restart`

## Next Steps

Once everything is working:
1. Integrate voice loop with Desktop Agent
2. Add command execution logic
3. Build file watcher for indexing
4. Create tests
