# Jarvis Hybrid Ecosystem - Phase 1 Setup Guide

## Quick Start

### Prerequisites
- **Docker Desktop** installed and running
- **Python 3.10+** installed
- **Git** (for version control)
- At least **5GB free RAM**

### Step 1: Clone and Setup

```bash
# Navigate to project directory
cd c:\Users\vishw\jarvis

# Copy environment template
copy .env.example .env

# (Optional) Edit .env file to customize settings
```

### Step 2: Start Docker Services

```bash
# Start all services in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

**Expected Output:**
```
NAME                COMMAND                  SERVICE      STATUS        PORTS
jarvis-api          "python -m uvicorn..."   jarvis-api   running       0.0.0.0:8000->8000/tcp
jarvis-db           "docker-entrypoint..."   db           running       0.0.0.0:5432->5432/tcp
jarvis-redis        "redis-server..."        redis        running       0.0.0.0:6379->6379/tcp
jarvis-ollama       "/bin/ollama serve"      ollama       running       0.0.0.0:11434->11434/tcp
jarvis-chromadb     "uvicorn chromadb..."    chromadb     running       0.0.0.0:8002->8000/tcp
```

### Step 3: Verify Services

```bash
# Check API health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","checks":{"database":true,"redis":true,"ollama":false}}

# Check database
docker exec -it jarvis-db psql -U jarvis -d jarvis -c "\dt"

# Check Redis
docker exec -it jarvis-redis redis-cli ping
# Expected: PONG
```

### Step 4: Pull LLM Model

```bash
# Pull Llama 3.2 1B model (smallest, fastest)
docker exec -it jarvis-ollama ollama pull llama3.2:1b

# Test model
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:1b",
  "prompt": "What is 2+2?",
  "stream": false
}'
```

### Step 5: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   FastAPI    │  │  PostgreSQL  │  │    Redis     │  │
│  │   :8000      │◄─┤   :5432      │  │   :6379      │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                                     ▲          │
│         │                                     │          │
│         ▼                                     │          │
│  ┌──────────────┐                    ┌───────┴──────┐  │
│  │   Ollama     │                    │  ChromaDB    │  │
│  │   :11434     │                    │   :8002      │  │
│  └──────────────┘                    └──────────────┘  │
│                                                          │
└─────────────────────────────────────────────────────────┘
                          ▲
                          │
                    WebSocket/HTTP
                          │
                ┌─────────┴─────────┐
                │  Desktop Agent    │
                │  (main.py)        │
                └───────────────────┘
```

---

## Service Details

### FastAPI Server (Port 8000)
- **Health Check**: `http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs`
- **WebSocket**: `ws://localhost:8000/ws`

### PostgreSQL (Port 5432)
- **Database**: `jarvis`
- **User**: `jarvis`
- **Password**: `jarvis_password` (change in production!)
- **Connection**: `postgresql://jarvis:jarvis_password@localhost:5432/jarvis`

### Redis (Port 6379)
- **URL**: `redis://localhost:6379`
- **Max Memory**: 256MB
- **Eviction**: allkeys-lru

### Ollama (Port 11434)
- **API**: `http://localhost:11434`
- **Models**: Llama 3.2 1B/3B
- **Memory Limit**: 3GB

### ChromaDB (Port 8002)
- **API**: `http://localhost:8002`
- **Persistent**: Yes
- **Usage**: Semantic file search (Phase 2)

---

## Common Commands

### Docker Management

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Restart a specific service
docker-compose restart jarvis-api

# View logs for specific service
docker-compose logs -f jarvis-api

# Execute command in container
docker exec -it jarvis-db psql -U jarvis -d jarvis
```

### Database Operations

```bash
# Connect to database
docker exec -it jarvis-db psql -U jarvis -d jarvis

# Backup database
docker exec jarvis-db pg_dump -U jarvis jarvis > backup.sql

# Restore database
docker exec -i jarvis-db psql -U jarvis jarvis < backup.sql

# View tables
docker exec -it jarvis-db psql -U jarvis -d jarvis -c "\dt"

# Query users
docker exec -it jarvis-db psql -U jarvis -d jarvis -c "SELECT * FROM users;"
```

### Ollama Model Management

```bash
# List installed models
docker exec -it jarvis-ollama ollama list

# Pull a model
docker exec -it jarvis-ollama ollama pull llama3.2:3b

# Remove a model
docker exec -it jarvis-ollama ollama rm llama3.2:1b

# Test model
docker exec -it jarvis-ollama ollama run llama3.2:1b "Hello!"
```

---

## Troubleshooting

### Issue: Containers won't start
```bash
# Check Docker is running
docker ps

# Check logs for errors
docker-compose logs

# Restart Docker Desktop
```

### Issue: Port already in use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
```

### Issue: Database connection failed
```bash
# Check if PostgreSQL is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Verify connection
docker exec -it jarvis-db psql -U jarvis -d jarvis -c "SELECT 1;"
```

### Issue: Out of memory
```bash
# Check Docker resource usage
docker stats

# Reduce Ollama memory limit in docker-compose.yml
# deploy:
#   resources:
#     limits:
#       memory: 2G  # Reduce from 3G
```

---

## Next Steps

After infrastructure is running:

1. **Test API Endpoints** - Use Postman or curl to test `/health`, `/ready`
2. **Implement WebSocket Gateway** - Build connection manager and protocol
3. **Create API Routes** - Device registration, authentication
4. **Build Desktop Agent** - Connect to Central Server via WebSocket
5. **Integrate LLM** - Connect Ollama for intent parsing

See `implementation_plan.md` for detailed roadmap.

---

## Development Workflow

```bash
# 1. Start services
docker-compose up -d

# 2. Activate virtual environment
venv\Scripts\activate

# 3. Run development server (auto-reload)
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000

# 4. Make changes to code

# 5. Test changes
curl http://localhost:8000/health

# 6. Stop services when done
docker-compose down
```

---

## Resources

- **Architecture Document**: `.agent/rules/jarvis_hybrid_ecosystem.md`
- **Implementation Plan**: `implementation_plan.md`
- **Task Tracker**: `task.md`
- **API Documentation**: `http://localhost:8000/docs` (when running)

---

## Support

For issues or questions:
1. Check logs: `docker-compose logs -f`
2. Review architecture document
3. Check implementation plan for context
