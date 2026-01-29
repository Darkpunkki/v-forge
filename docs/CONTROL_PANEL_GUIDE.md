# VibeForge Control Panel - Usage Guide (Windows)

**Control real Claude Code agents running across multiple machines from a single web interface.**

---

## Table of Contents

- [Overview](#overview)
- [Important Concepts](#important-concepts)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Complete Setup Workflow](#complete-setup-workflow)
- [Using the Control Panel](#using-the-control-panel)
- [Running Multiple Agents](#running-multiple-agents)
- [Making Agents Persistent](#making-agents-persistent)
- [TLS / WSS (Self-Signed for Dev)](#tls--wss-self-signed-for-dev)
- [Troubleshooting](#troubleshooting)
- [Remote Agents](#remote-agents)
- [API Reference](#api-reference)

---

## Overview

The VibeForge Control Panel (`/control`) allows you to:

- **Control multiple Claude Code instances** running on different machines
- **Dispatch tasks** to agents working in specific directories
- **Monitor execution** in real-time via Server-Sent Events (SSE)
- **Manage conversations** with follow-up messages
- **Track costs and usage** across all agents

### Key Features

✅ **Multi-agent management** - Run agents in different directories simultaneously
✅ **Real-time updates** - See responses as they happen via SSE streaming
✅ **Conversation style** - Send follow-up messages to active tasks
✅ **Cost tracking** - Monitor API usage and spending
✅ **Remote agents** - Control agents on other machines

---

## Important Concepts

### **The UI Registration Form is Optional**

**You do NOT need to use the "Register Agent" form in the UI.** This form only pre-registers metadata - it doesn't actually start agents.

### **How Agents Actually Work**

1. **You run the bridge script** in a terminal on the machine where you want the agent
2. **The bridge auto-registers** when it connects via WebSocket
3. **The agent appears in the UI** automatically with "connected" status
4. **You use the UI to dispatch tasks** to connected agents

**The bridge MUST run where your code lives** because:
- It needs filesystem access to your project
- It executes Claude Code CLI locally
- It reads/writes files in the workdir

---

## Prerequisites

### On Your VibeForge Server Machine

1. **Python 3.11+** with virtual environment
2. **Node.js 18+**
3. **Git** (to clone the repository)

### On Each Agent Machine (Can Be the Same Machine)

1. **Python 3.11+**
2. **Claude Code CLI installed and configured**
   ```powershell
   # Verify Claude is installed
   claude --version

   # Verify API key is configured
   claude /config
   ```
3. **Network access** to the VibeForge server (localhost or remote)

---

## Quick Start

### 1. Generate an Auth Token

**Using the Token Setup Script (Recommended):**

```powershell
# First time on any machine - generate and save token
cd C:\path\to\v-forge
. .\set-token.ps1 -Generate
```

This generates a secure token and saves it to `.vibeforge-token` (not committed to git). **Copy the displayed token** - you'll need it for other machines!

**On subsequent machines (or sessions), just load the token:**

```powershell
# First time on a new machine - use token from first machine
. .\set-token.ps1 -Token "paste-token-from-first-machine"

# Every new terminal session after that
. .\set-token.ps1
```

**Manual approach (if script doesn't work):**

```powershell
$env:VIBEFORGE_AUTH_TOKEN = (python -c "import secrets; print(secrets.token_hex(32))")
$env:VITE_CONTROL_TOKEN = $env:VIBEFORGE_AUTH_TOKEN
```

> **Important:** The token must be **identical on all machines** (API server, UI, and all agents) for them to communicate!

### 2. Start VibeForge Services

**Terminal 1 (API Server):**
```powershell
cd C:\path\to\v-forge\apps\api
.venv\Scripts\activate
uvicorn vibeforge_api.main:app --reload --port 8000
```

**Terminal 2 (UI):**
```powershell
cd C:\path\to\v-forge\apps\ui
npm run dev
```

The UI will be available at `http://localhost:5173`

### 3. Start an Agent

**Terminal 3 (Agent Bridge):**
```powershell
cd C:\path\to\v-forge

python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id my-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\your\project `
  --heartbeat 15
```

**What each parameter means:**
- `--url ws://localhost:8000/ws/agent-bridge` - **Always this for local setup** (WebSocket endpoint)
- `--agent-id my-agent` - **Any name you want** (shows up in the UI)
- `--token $env:VIBEFORGE_AUTH_TOKEN` - **Authentication token** (must match server config)
- `--workdir C:\path\to\your\project` - **Where you want Claude to work**
- `--heartbeat 15` - **Send heartbeat every 15 seconds** (prevents timeout)

### 4. Use the Control Panel

1. Open `http://localhost:5173/control`
2. You'll see `my-agent` in the **Agent Connection Dashboard** (left sidebar)
3. Click the agent to select it
4. Type a task: `"List all files in the current directory"`
5. Click **Send**
6. Watch the **Streaming Output View** for the response

---

## Multi-Machine Setup (PC + Laptop)

**Common Scenario:** Run API/UI on PC, control agents on laptop (or vice versa).

### Prerequisites

- Both machines on same network (Ethernet or WiFi)
- Git repository cloned on both machines
- Python and Node.js installed on both

### Setup: API on PC, Agents on Laptop

This is the recommended setup if your PC is always on and has better resources.

#### Step 1: Generate Token (On Either Machine First)

**On Laptop (or PC, doesn't matter):**
```powershell
cd C:\path\to\v-forge
. .\set-token.ps1 -Generate
```

**Copy the displayed token** - you'll need it for the other machine!

Example output:
```
Token: a1b2c3d4e5f6789....(64 characters total)
```

Save this somewhere safe (text file, password manager, etc.).

#### Step 2: Set Up PC (API + UI Server)

**Get your PC's IP address:**
```powershell
ipconfig
# Look for "IPv4 Address" - usually 192.168.1.XXX
```

**Configure firewall (if needed):**
```powershell
# Allow incoming connections on port 8000
New-NetFirewallRule -DisplayName "VibeForge API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**Terminal 1 - API Server:**
```powershell
cd C:\path\to\v-forge

# Set the token (first time: use -Token "paste-token", after: just load it)
. .\set-token.ps1

cd apps\api
.venv\Scripts\activate
uvicorn vibeforge_api.main:app --reload --host 0.0.0.0 --port 8000
```

> **Note:** `--host 0.0.0.0` makes the API accessible from other machines on the network. Without it, only localhost works.

**Terminal 2 - UI Server:**
```powershell
cd C:\path\to\v-forge

# Load token
. .\set-token.ps1

cd apps\ui
npm run dev
```

**Verify it's working:**
- On PC browser: Open `http://localhost:5173/control`
- On laptop browser: Open `http://192.168.1.XXX:5173/control` (use PC's IP)

#### Step 3: Set Up Laptop (Agent)

**On Laptop:**
```powershell
cd C:\path\to\v-forge

# First time: Set the token from PC
. .\set-token.ps1 -Token "paste-token-from-pc"

# After first time: Just load it
# . .\set-token.ps1

# Start agent (replace 192.168.1.XXX with your PC's IP)
python tools/agent_bridge/bridge.py `
  --url ws://192.168.1.XXX:8000/ws/agent-bridge `
  --agent-id laptop-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\your\project `
  --heartbeat 15
```

**Expected output:**
```
[2026-01-30 12:00:00] INFO Connecting to ws://192.168.1.XXX:8000/ws/agent-bridge
[2026-01-30 12:00:01] INFO Registered as laptop-agent (session abc-123)
```

#### Step 4: Verify Connection

1. **On PC or laptop browser:** Open `http://192.168.1.XXX:5173/control` (PC's IP)
2. **Check left sidebar:** You should see `laptop-agent` with status **connected** (green)
3. **Dispatch a test task:**
   - Click `laptop-agent`
   - Type: `"What is the current directory?"`
   - Click Send
   - Watch for response in Streaming Output View

#### Daily Workflow

**On PC (every day):**
```powershell
# Terminal 1
cd C:\path\to\v-forge
. .\set-token.ps1
cd apps\api && .venv\Scripts\activate
uvicorn vibeforge_api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2
cd C:\path\to\v-forge
. .\set-token.ps1
cd apps\ui && npm run dev
```

**On Laptop (every day):**
```powershell
cd C:\path\to\v-forge
. .\set-token.ps1

# Replace IP with your PC's actual IP
python tools/agent_bridge/bridge.py `
  --url ws://192.168.1.XXX:8000/ws/agent-bridge `
  --agent-id laptop-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\your\project `
  --heartbeat 15
```

### Alternative: API on Laptop, Agents on PC

If you prefer to run the API/UI on your laptop:

**On Laptop:**
```powershell
# Get IP address
ipconfig

# Terminal 1 - API
. .\set-token.ps1
cd apps\api && uvicorn vibeforge_api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - UI
. .\set-token.ps1
cd apps\ui && npm run dev
```

**On PC (agent):**
```powershell
. .\set-token.ps1

python tools/agent_bridge/bridge.py `
  --url ws://192.168.1.YYY:8000/ws/agent-bridge `
  --agent-id pc-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\your\project `
  --heartbeat 15
```

### Running Multiple Agents

You can run agents on **both** machines simultaneously:

**Laptop agent:**
```powershell
python tools/agent_bridge/bridge.py `
  --url ws://192.168.1.XXX:8000/ws/agent-bridge `
  --agent-id laptop-frontend `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\projects\my-app\frontend `
  --heartbeat 15
```

**PC agent (in separate terminal):**
```powershell
python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id pc-backend `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\projects\my-app\backend `
  --heartbeat 15
```

Both agents will appear in the UI, and you can dispatch tasks to either one!

### Troubleshooting Multi-Machine Setup

#### "Connection refused" on agent

**Problem:** Agent can't connect to API server

**Solutions:**
1. **Check PC's firewall:**
   ```powershell
   # On PC
   New-NetFirewallRule -DisplayName "VibeForge API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   ```

2. **Verify API is listening on 0.0.0.0:**
   - Must use `--host 0.0.0.0` flag with uvicorn
   - Without it, only localhost connections work

3. **Check IP address is correct:**
   ```powershell
   # On PC
   ipconfig
   # Use the IPv4 address shown
   ```

4. **Test connectivity:**
   ```powershell
   # On laptop
   curl http://192.168.1.XXX:8000/health
   # Should return: {"status":"ok","service":"vibeforge-api"}
   ```

#### "401 Unauthorized" errors

**Problem:** Token mismatch between machines

**Solution:**
```powershell
# On both machines, verify tokens match
echo $env:VIBEFORGE_AUTH_TOKEN

# Should be identical! If not:
# On laptop/PC with wrong token:
. .\set-token.ps1 -Token "correct-token-here"
```

#### Can't access UI from other machine

**Problem:** UI only accessible from localhost

**Solution:**
The Vite dev server binds to `localhost` by default. To make it accessible:

```powershell
# Option 1: Use PC's browser (simplest)
# Just open browser on the PC running the API/UI

# Option 2: Set VITE_API_BASE on laptop browser
# On laptop, before opening browser:
$env:VITE_API_BASE = "http://192.168.1.XXX:8000"
# Then open: http://192.168.1.XXX:5173/control
```

#### Agent shows as "disconnected"

**Problem:** Agent registered but shows red status

**Solutions:**
1. **Add `--heartbeat 15` flag** to bridge command
2. **Check API server logs** for errors
3. **Restart both API and agent**

---

## Complete Setup Workflow

### Architecture Overview

```
┌─────────────────────────────────────┐
│  Browser                            │
│  http://localhost:5173/control      │
└────────────┬────────────────────────┘
             │ REST API + SSE
             ▼
┌─────────────────────────────────────┐
│  VibeForge API Server               │
│  http://localhost:8000              │
│  Terminal 1: uvicorn ...            │
└────────────┬────────────────────────┘
             │ WebSocket
             ▼
┌─────────────────────────────────────┐
│  Agent Bridge Service               │
│  Terminal 3: python bridge.py       │
│  Runs in your project directory     │
└────────────┬────────────────────────┘
             │ subprocess
             ▼
┌─────────────────────────────────────┐
│  Claude Code CLI                    │
│  Executes in --workdir              │
│  Reads/writes your project files    │
└─────────────────────────────────────┘
```

### Step-by-Step Setup

#### **Step 1: Verify Claude Code CLI Works**

Before starting anything, test Claude:

```powershell
# Test basic invocation
echo "Say hello" | claude --print --output-format json
```

You should see JSON output with a `"result"` field containing Claude's response.

**If this fails:**
- Install Claude Code: Visit https://claude.ai/download
- Configure API key: Run `claude /config`
- Check PATH: Run `where.exe claude`

#### **Step 2: Start the API Server**

```powershell
# Terminal 1
cd C:\path\to\v-forge\apps\api
.venv\Scripts\activate
uvicorn vibeforge_api.main:app --reload --port 8000
```

**Verify it's running:**
```powershell
# In a new terminal
Invoke-RestMethod http://localhost:8000/health
```

Should return: `{"status":"ok","service":"vibeforge-api"}`

#### **Step 3: Start the UI**

```powershell
# Terminal 2
cd C:\path\to\v-forge\apps\ui
npm run dev
```

The UI will open at `http://localhost:5173` (or similar - check the terminal output).

#### **Step 4: Choose Your Workdir**

The `--workdir` is **critical** - it's where Claude Code will execute:

**Examples:**
- Specific project: `C:\Users\YourName\projects\my-app`
- Monorepo workspace: `C:\projects\monorepo\packages\api`
- Testing: `C:\temp\test-workspace`

**Important:** The agent will have **full read/write access** to this directory!

#### **Step 5: Start the Agent Bridge**

```powershell
# Terminal 3
cd C:\path\to\v-forge

python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id my-first-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\your\chosen\directory `
  --heartbeat 15
```

**What you should see:**
```
[2026-01-29 12:00:00] INFO Connecting to ws://localhost:8000/ws/agent-bridge
[2026-01-29 12:00:01] INFO Registered as my-first-agent (session abc-123)
```

**If you see reconnection loops:**
- Check the API server is running
- Verify the URL is correct
- Look for error messages in the bridge terminal

#### **Step 6: Verify in the UI**

1. Refresh `http://localhost:5173/control`
2. Look at the left sidebar **Agent Connection Dashboard**
3. You should see: `my-first-agent` with status **"connected"** (green)
4. Workdir should show your chosen path
5. **Ignore "Endpoint: not provided"** - this is normal

#### **Step 7: Dispatch Your First Task**

**Option A: Via UI (Recommended)**
1. Click `my-first-agent` in the left sidebar to select it
2. In the **Task Dispatch Panel**, type: `List all files in the current directory`
3. Click **Send**
4. Watch the **Streaming Output View** for the response

**Option B: Via PowerShell**
```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/control/agents/my-first-agent/dispatch `
  -ContentType "application/json" `
  -Body '{"content":"List all files in the current directory"}'
```

#### **Step 8: Verify You See Output**

**In the bridge terminal (Terminal 3), you should see:**
```
[2026-01-29 12:00:15] INFO Received dispatch message
[2026-01-29 12:00:20] INFO Sent response for task ...
```

**In the UI Streaming Output View, you should see:**
- Event type: `AGENT RESPONSE`
- Badge: `idle` (green)
- Content: List of files from your workdir

**If you don't see output:**
- Check the bridge terminal for errors
- See [Troubleshooting](#troubleshooting) section below

---

## Using the Control Panel

### UI Overview

The control panel has several sections:

#### **Left Sidebar: Agent Connection Dashboard**
- Shows all connected agents
- Click an agent to select it
- Shows agent status: connected (green), disconnected (red), busy (blue)
- Shows workdir and last heartbeat

#### **Left Sidebar: Agent Registration Panel**
- **You can ignore this** - agents auto-register when they connect
- Only needed if you want to pre-register metadata

#### **Main Area: Task Dispatch Panel**
- Send tasks to the selected agent
- Type your task and press Enter or click Send
- Shows conversation history with the agent
- Can send follow-up messages while a task is active

#### **Main Area: Streaming Output View**
- Real-time events from the selected agent
- Shows task dispatches, progress updates, and responses
- Auto-scrolls (can pause with the Pause button)
- Click "Metadata" to see full event details

#### **Bottom: Event Stream (Collapsible)**
- Shows all events from all agents
- Can filter by event type
- Has a Clear button

#### **Bottom: Cost Analytics (Collapsible)**
- Token usage across all agents
- API costs in USD
- Model usage breakdown

### Common Tasks

#### **Dispatching a Task**

**In the UI:**
1. Select the agent in the left sidebar
2. Type your task in the input field
3. Press Enter or click Send

**Example tasks:**
- `"Create a README.md file for this project"`
- `"Run the test suite and show me any failures"`
- `"Find all TODO comments in the codebase"`
- `"Refactor the database module to use async/await"`

#### **Sending a Follow-up**

While a task is active (status shows "busy"):
1. Type your follow-up message
2. Press Enter or click Send

**Example follow-ups:**
- `"Add installation instructions to that README"`
- `"Fix those failing tests"`
- `"Also update the documentation for those changes"`

**Note:** You can only send follow-ups when an agent has an active task.

#### **Monitoring Multiple Agents**

If you have multiple agents running:
1. Each appears in the left sidebar
2. Click an agent to switch between them
3. Each agent has independent task history
4. The Event Stream shows activity from all agents

#### **Checking Task Status**

**Via UI:**
- Look at the agent's status in the left sidebar
- `idle` = no active task
- `busy` = task in progress
- `connected` = agent is connected and ready

**Via PowerShell:**
```powershell
Invoke-RestMethod http://localhost:8000/control/agents/my-agent/task
```

Response shows: `status`, `message_id`, and any `error`.

#### **Viewing Real-time Events**

**Via UI:**
- The Streaming Output View shows events automatically
- Expand the Event Stream panel for all events

**Via PowerShell (SSE stream):**
```powershell
curl.exe -N http://localhost:8000/control/agents/my-agent/events
```

Leave this running to see events in real-time.

---

## Running Multiple Agents

You can run multiple agents simultaneously, each working in a different directory.

### Example: 3 Agents for Different Parts of a Project

**Terminal 3: Frontend Agent**
```powershell
python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id frontend-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\projects\my-app\frontend `
  --heartbeat 15
```

**Terminal 4: Backend Agent**
```powershell
python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id backend-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\projects\my-app\backend `
  --heartbeat 15
```

**Terminal 5: Testing Agent**
```powershell
python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id test-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\projects\my-app `
  --heartbeat 15
```

Now you'll see **3 connected agents** in the UI!

### Using Capabilities (Optional)

Tag agents with capabilities to organize them:

```powershell
python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id python-specialist `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\projects\python-app `
  --heartbeat 15 `
  --capability python `
  --capability pytest `
  --capability flask
```

The capabilities appear in the UI and can help you remember what each agent is for.

---

## Making Agents Persistent

By default, agents run in terminal windows. If you close the terminal, the agent stops.

### Option 1: Background Process (Simple)

Run the bridge in the background:

```powershell
Start-Process python -ArgumentList "tools/agent_bridge/bridge.py --url ws://localhost:8000/ws/agent-bridge --agent-id my-agent --token $env:VIBEFORGE_AUTH_TOKEN --workdir C:\path --heartbeat 15" -WindowStyle Hidden
```

**To stop it:**
- Open Task Manager
- Find the `python.exe` process
- End task

### Option 2: Batch Script with Auto-Restart

Create `start-agent.bat`:

```batch
@echo off
:loop
python tools/agent_bridge/bridge.py --url ws://localhost:8000/ws/agent-bridge --agent-id my-agent --token $env:VIBEFORGE_AUTH_TOKEN --workdir C:\your\path --heartbeat 15
echo Agent disconnected, restarting in 5 seconds...
timeout /t 5
goto loop
```

Run it:
```powershell
.\start-agent.bat
```

This restarts the agent if it crashes or disconnects.

### Option 3: Windows Task Scheduler (Production)

For production use:

1. Open **Task Scheduler**
2. Create a new task
3. **Trigger**: At startup or at specific time
4. **Action**: Start a program
   - Program: `C:\path\to\python.exe`
   - Arguments: `tools/agent_bridge/bridge.py --url ws://your-server:8000/ws/agent-bridge --agent-id my-agent --token $env:VIBEFORGE_AUTH_TOKEN --workdir C:\path --heartbeat 15`
   - Start in: `C:\path\to\v-forge`
5. **Settings**:
   - Run whether user is logged on or not
   - Restart on failure

### Option 4: NSSM (Windows Service)

For professional deployments, use [NSSM](https://nssm.cc/) to run the bridge as a Windows service.

---

## TLS / WSS (Self-Signed for Dev)

Use this when you want encrypted HTTPS/WSS connections for local or remote testing.

1. **Generate certificates:**
   ```powershell
   powershell -File tools/generate_certs.ps1
   ```

2. **Start the API with TLS:**
   ```powershell
   uvicorn vibeforge_api.main:app --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem
   ```

3. **Connect the agent bridge over WSS:**
   ```powershell
   python tools/agent_bridge/bridge.py `
     --url wss://localhost:8000/ws/agent-bridge `
     --agent-id my-agent `
     --token $env:VIBEFORGE_AUTH_TOKEN `
     --workdir C:\path\to\your\project `
     --heartbeat 15 `
     --insecure
   ```

4. **Point the UI at HTTPS (optional):**
   ```powershell
   $env:VITE_API_BASE = "https://localhost:8000"
   npm run dev
   ```

> `--insecure` disables certificate verification and should only be used for self-signed certs in development.

## Troubleshooting

### Agent Shows "Disconnected"

**Symptoms:**
- Agent appears in UI with red "disconnected" status
- Or agent keeps reconnecting in the bridge terminal

**Solutions:**

1. **Check the bridge terminal for errors:**
   - `Connection refused` → API server not running
   - `Heartbeat timeout` → Add `--heartbeat 15` parameter
   - `Claude CLI not found` → Install Claude Code CLI

2. **Verify API server is running:**
   ```powershell
   Invoke-RestMethod http://localhost:8000/health
   ```

3. **Restart the bridge:**
   - Press `Ctrl+C` in the bridge terminal
   - Run the command again with `--heartbeat 15`

4. **Check firewall:**
   - Ensure port 8000 is not blocked
   - Try adding firewall exception for Python

### Task Status Shows "Idle" After Dispatch

**Symptoms:**
- You dispatch a task
- Status remains "idle" instead of "running"
- No output appears

**Solutions:**

1. **Check the bridge terminal** - Look for errors like:
   - `Claude CLI returned non-zero exit code`
   - `Claude CLI timed out`
   - Python exceptions or stack traces

2. **Verify Claude CLI works:**
   ```powershell
   echo "test" | claude --print --output-format json
   ```
   Should return JSON with a `result` field.

3. **Check Claude API key:**
   ```powershell
   claude /config
   ```
   Ensure your API key is configured.

4. **Restart the bridge** to pick up any code fixes.

### No Output in Streaming View

**Symptoms:**
- Task shows "completed"
- But no output visible in the UI

**Solutions:**

1. **Ensure the bug fixes are applied:**

   **File: `tools/agent_bridge/cli_wrapper.py` (line 77)**
   ```python
   content = payload.get("content")
   if content is None:
       content = payload.get("result") or payload.get("completion") or payload.get("response") or ""
   ```
   Should include `payload.get("result")` ✅

   **File: `apps/api/vibeforge_api/routers/agent_bridge.py` (line 190)**
   ```python
   metadata={
       "message_id": msg.message_id,
       "content": msg.content,  # ← This line is critical
       "content_length": len(msg.content),
       "usage": msg.usage,
   },
   ```
   Should include `"content": msg.content` ✅

2. **Restart the API server** after applying fixes:
   ```powershell
   # Terminal 1 (API)
   # Press Ctrl+C, then:
   uvicorn vibeforge_api.main:app --reload --port 8000
   ```

3. **Restart the bridge** after applying fixes:
   ```powershell
   # Terminal 3 (Bridge)
   # Press Ctrl+C, then run the bridge command again
   ```

4. **Check the SSE stream directly:**
   ```powershell
   curl.exe -N http://localhost:8000/control/agents/my-agent/events
   ```
   Dispatch a task and see if `agent_response` events contain actual content.

### Heartbeat Timeout / Keeps Reconnecting

**Symptoms:**
- Bridge terminal shows: `WARNING Connection error: received 4003 (private use) Heartbeat timeout`
- Agent reconnects every ~45 seconds

**Solution:**

**Always use `--heartbeat 15`** when starting the bridge:

```powershell
python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id my-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path `
  --heartbeat 15  # ← Critical!
```

This sends heartbeats every 15 seconds instead of 30, preventing timeouts.

### Claude API Errors

**Symptoms:**
- Task fails with errors mentioning Claude API
- Rate limit errors
- Authentication errors

**Solutions:**

1. **Check API key:**
   ```powershell
   claude /config
   ```

2. **Check quotas:**
   - You may have hit rate limits
   - Check your Claude.ai account usage

3. **Check costs:**
   - Expand the Cost Analytics panel in the UI
   - Verify you haven't exceeded your budget

4. **Wait and retry:**
   - Rate limits are temporary
   - Wait a few minutes and try again

### Permission Errors in Workdir

**Symptoms:**
- Task fails with "Permission denied"
- Can't read or write files

**Solutions:**

1. **Verify workdir exists:**
   ```powershell
   Test-Path C:\your\workdir
   ```

2. **Check permissions:**
   - Ensure you have read/write access to the directory
   - Try running PowerShell as Administrator

3. **Try a different workdir:**
   - Use a directory you own: `C:\Users\YourName\test-workspace`

4. **Check for locked files:**
   - Another program might have files open
   - Close IDEs, editors, etc.

### UI Shows "Endpoint: not provided"

**This is normal!**

Agents that register via WebSocket (the standard way) will show "Endpoint: not provided". This is expected and doesn't indicate a problem.

The important field is **Status** - it should show **"connected"** (green).

---

## Remote Agents

You can control agents running on other machines!

### Setup for Remote Agents

#### **On the VibeForge Server Machine:**

1. **Note your IP address:**
   ```powershell
   ipconfig
   # Look for IPv4 Address
   ```

2. **Ensure port 8000 is accessible:**
   - Configure Windows Firewall to allow incoming connections on port 8000
   - Or temporarily disable firewall for testing

#### **On the Remote Agent Machine:**

1. **Install Python 3.11+ and Claude Code CLI**

2. **Copy the bridge script:**
   - Transfer the entire `tools/agent_bridge/` folder
   - Or clone the v-forge repository

3. **Run the bridge with the server's IP:**
   ```powershell
   python tools/agent_bridge/bridge.py `
     --url ws://192.168.1.100:8000/ws/agent-bridge `
     --agent-id remote-agent `
     --token $env:VIBEFORGE_AUTH_TOKEN `
     --workdir C:\path\on\remote\machine `
     --heartbeat 15
   ```

4. **The agent appears in the UI automatically!**

### Use Cases for Remote Agents

- **Development laptop + Cloud VM:** Run frontend agent locally, backend agent on cloud server
- **Multiple team members:** Each person runs agents on their own machine
- **Different environments:** Windows agent, Linux agent (via WSL or separate machine)
- **GPU machine:** Run ML/AI tasks on a machine with GPU access

---

## API Reference

All endpoints use base URL: `http://localhost:8000`

### Agent Management

#### `GET /control/agents`
List all agents (registered and connected).

**Example:**
```powershell
Invoke-RestMethod http://localhost:8000/control/agents
```

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "my-agent",
      "name": "my-agent",
      "status": "connected",
      "workdir": "C:\\path\\to\\project",
      "connected_at": "2026-01-29T12:00:00Z",
      "last_heartbeat": "2026-01-29T12:05:30Z",
      "capabilities": []
    }
  ],
  "total": 1
}
```

#### `GET /control/agents/{agent_id}`
Get details for a specific agent.

**Example:**
```powershell
Invoke-RestMethod http://localhost:8000/control/agents/my-agent
```

### Task Dispatch

#### `POST /control/agents/{agent_id}/dispatch`
Dispatch a task to an agent.

**Body:**
```json
{
  "content": "Your task description here",
  "context": {}  // Optional
}
```

**Example:**
```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/control/agents/my-agent/dispatch `
  -ContentType "application/json" `
  -Body '{"content":"List all Python files"}'
```

**Response:**
```json
{
  "agent_id": "my-agent",
  "message_id": "uuid-here",
  "status": "dispatched",
  "message": "Task dispatched"
}
```

#### `POST /control/agents/{agent_id}/followup`
Send a follow-up message to an active task.

**Body:**
```json
{
  "content": "Your follow-up message"
}
```

**Example:**
```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/control/agents/my-agent/followup `
  -ContentType "application/json" `
  -Body '{"content":"Add type hints to those files"}'
```

**Note:** Only works when the agent has an active task (status: "running").

### Task Status

#### `GET /control/agents/{agent_id}/task`
Get current task status for an agent.

**Example:**
```powershell
Invoke-RestMethod http://localhost:8000/control/agents/my-agent/task
```

**Response:**
```json
{
  "agent_id": "my-agent",
  "status": "completed",
  "message_id": "uuid-here",
  "error": null
}
```

**Status values:**
- `idle` - No active task
- `dispatched` - Task sent, not started
- `running` - Task in progress
- `completed` - Task finished successfully
- `error` - Task failed

### Event Streaming

#### `GET /control/agents/{agent_id}/events`
Stream agent events via Server-Sent Events (SSE).

**Example:**
```powershell
curl.exe -N http://localhost:8000/control/agents/my-agent/events
```

**Output (SSE format):**
```
event: agent_event
data: {"event_type": "task_dispatched", "timestamp": "...", ...}

event: agent_event
data: {"event_type": "agent_progress", "metadata": {"status": "running"}, ...}

event: agent_event
data: {"event_type": "agent_response", "metadata": {"content": "..."}, ...}
```

Leave this running to see real-time events.

### Context

#### `GET /control/context`
Get the control session context (used internally by the UI).

**Example:**
```powershell
Invoke-RestMethod http://localhost:8000/control/context
```

**Response:**
```json
{
  "control_session_id": "session-uuid"
}
```

---

## Summary

### What You Need Running

**Always running (keep these terminals open):**
1. **Terminal 1:** API Server - `uvicorn vibeforge_api.main:app --reload --port 8000`
2. **Terminal 2:** UI - `npm run dev`

**For each agent (one terminal per agent):**
3. **Terminal 3+:** Agent Bridge - `python tools/agent_bridge/bridge.py --url ws://localhost:8000/ws/agent-bridge --agent-id NAME --token $env:VIBEFORGE_AUTH_TOKEN --workdir PATH --heartbeat 15`

### Key Commands

**Set Up Token (First Time Only):**
```powershell
cd C:\path\to\v-forge

# On first machine (generates and saves token)
. .\set-token.ps1 -Generate

# On other machines (uses same token)
. .\set-token.ps1 -Token "paste-token-here"

# Every subsequent session (loads saved token)
. .\set-token.ps1
```

**Start API:**
```powershell
cd C:\path\to\v-forge\apps\api
. ..\..\..\set-token.ps1
.venv\Scripts\activate
uvicorn vibeforge_api.main:app --reload --port 8000
```

**Start API (Multi-Machine - Listen on Network):**
```powershell
cd C:\path\to\v-forge\apps\api
. ..\..\..\set-token.ps1
.venv\Scripts\activate
uvicorn vibeforge_api.main:app --reload --host 0.0.0.0 --port 8000
```

**Start UI:**
```powershell
cd C:\path\to\v-forge\apps\ui
. ..\..\..\set-token.ps1
npm run dev
```

**Start Agent (Local):**
```powershell
cd C:\path\to\v-forge
. .\set-token.ps1
python tools/agent_bridge/bridge.py `
  --url ws://localhost:8000/ws/agent-bridge `
  --agent-id YOUR-NAME `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\YOUR\PATH `
  --heartbeat 15
```

**Start Agent (Remote - Connect to Another Machine):**
```powershell
cd C:\path\to\v-forge
. .\set-token.ps1
python tools/agent_bridge/bridge.py `
  --url ws://192.168.1.XXX:8000/ws/agent-bridge `
  --agent-id YOUR-NAME `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\YOUR\PATH `
  --heartbeat 15
```

**Dispatch Task:**
```powershell
Invoke-RestMethod -Method Post `
  -Uri http://localhost:8000/control/agents/YOUR-NAME/dispatch `
  -ContentType "application/json" `
  -Body '{"content":"YOUR TASK HERE"}'
```

**Stream Events:**
```powershell
curl.exe -N http://localhost:8000/control/agents/YOUR-NAME/events
```

### Quick Reference: PC (API) + Laptop (Agent) Setup

**One-Time Setup:**

1. **On Laptop (or PC first):** Generate token
   ```powershell
   cd C:\path\to\v-forge
   . .\set-token.ps1 -Generate
   # Copy the displayed token!
   ```

2. **On PC:** Get IP address and configure firewall
   ```powershell
   ipconfig  # Note the IPv4 address (e.g., 192.168.1.100)
   New-NetFirewallRule -DisplayName "VibeForge API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow

   # Set the token
   cd C:\path\to\v-forge
   . .\set-token.ps1 -Token "paste-token-from-laptop"
   ```

**Daily Usage:**

**On PC (API Server):**
```powershell
# Terminal 1 - API
cd C:\path\to\v-forge
. .\set-token.ps1
cd apps\api && .venv\Scripts\activate
uvicorn vibeforge_api.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 - UI
cd C:\path\to\v-forge
. .\set-token.ps1
cd apps\ui && npm run dev
```

**On Laptop (Agent):**
```powershell
cd C:\path\to\v-forge
. .\set-token.ps1

# Replace 192.168.1.XXX with your PC's IP
python tools/agent_bridge/bridge.py `
  --url ws://192.168.1.XXX:8000/ws/agent-bridge `
  --agent-id laptop-agent `
  --token $env:VIBEFORGE_AUTH_TOKEN `
  --workdir C:\path\to\your\project `
  --heartbeat 15
```

**Access UI:** Open `http://192.168.1.XXX:5173/control` (PC's IP) in browser on either machine

### Next Steps

1. ✅ **Get the basic setup working** - One local agent
2. ✅ **Try dispatching different tasks** - Explore what Claude can do
3. ✅ **Add more agents** - Multiple directories or projects
4. ✅ **Set up multi-machine agents** - See "Multi-Machine Setup" section above
5. ✅ **Make agents persistent** - Background processes or scheduled tasks
6. ✅ **Build automation** - Scripts to automate common workflows

### Getting Help

- Check the **Troubleshooting** section above
- Look at the **bridge terminal** for error messages
- Use the **SSE stream** to see raw events
- Check the **browser console** (F12) for UI errors

---

**Happy agent controlling! 🤖**

**See the "Multi-Machine Setup" section** for detailed instructions on running the API on one machine and agents on another!
