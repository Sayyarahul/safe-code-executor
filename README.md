## Safe Code Executor — Python + Docker Sandbox ##

This project provides a secure API that executes untrusted Python code inside isolated Docker containers.  
Use it as a foundation — it implements a Flask API that writes submitted Python to a temporary file, runs it inside a Docker container with resource limits and network disabled, enforces a 5000-character limit, and returns friendly error messages.

---

### Overview ###

The API accepts Python code, writes it to a temporary file, and runs it inside a restricted Docker container.  
Output and errors are captured and returned in JSON.

The system demonstrates:

- Safe execution of untrusted code
- Docker security features
- Resource limiting (memory, CPU, PIDs)
- Timeout protection
- Network isolation
- Read-only filesystem usage
- Non-root user execution inside containers

---

## Features
- Single HTTP endpoint: `POST /run` accepts JSON `{ "code": "..." }` and returns output or clear error messages.
- Flask server writes submitted code to a temporary file and mounts it into a Docker container (read-only).
- Runs code inside `python:3.11-slim`.
- Basic safety controls:
  - Execution timeout: **10 seconds**
  - Memory cap: **128 MB**
  - Network disabled: `--network none`
  - Read-only container filesystem: `--read-only` (with the script mounted separately)
  - PIDs limit to mitigate fork-bombs
  - Max code length enforced: **5000 characters**
- Minimal browser UI for quick testing.
---

### API reference ###

### `POST /run` ###

### Request ###

- Header: Content-Type: application/json
- Body: { "code": "print(2 + 2)" }

### Success Response ###

- 200 OK
- Body: { "output": "4\n" }

### Common Error Responses ###

- 400 Bad Request — e.g., {"error":"Code too long (5000 chars max)"}
- 408 Request Timeout — {"error":"Execution timed out after 10 seconds"}
- 500 Internal Server Error — e.g., Docker not available
- 400 — runtime errors returned as {"error":"Execution failed", "stdout":"...", "stderr":"..."}

### Behavior notes

- The server writes script.py into a temporary directory and mounts it into the container at /workspace/script.py.
- Container is invoked with --rm to remove it after execution where possible.

### Web UI

- Open http://localhost:5000 to access a minimal UI: a textarea for code, a Run button, and a display area for results (JSON output). It's for manual testing and demo only.

### Error messages & limits

- Code length limit: 5000 characters.
- Execution timeout: 10 seconds — server returns a 408 and a clear message when that limit is reached.
- Memory limit: 128 MB — container will be killed or raise memory errors if exceeded; server attempts to surface this clearly.

### Security Controls ###

| Feature | Description |
|--------|-------------|
| Timeout (10s) | Stops infinite loops |
| Memory limit (128MB) | Blocks memory bombs |
| CPU limit | Prevents heavy CPU abuse |
| No network | Blocks HTTP, DNS, socket operations |
| Read-only filesystem | Prevents file writes |
| Non-root user | Limits privilege inside container |
| Capability dropping | Prevents privileged operations |
| PIDs limit | Protects against fork bombs |

### Web Interface

- A simple HTML interface is included for interactive testing.

---

## Project Structure

``
Safe-Code-Executor/
├── app.py # Flask API + UI
├── requirements.txt # Python dependencies
├── runner_image/
│ └── Dockerfile # Secure container image
├── README.md
└── venv/ # Virtual environment (ignored)
``
---

## Installation and Setup

### 1. Install Required Packages

On Ubuntu/WSL:

1. sudo apt update
```
sudo apt install -y python3-venv python3-pip
```
Install Docker Desktop and enable WSL2 integration.
Verify Docker is working:
docker run --rm hello-world

2. Create and Activate the Python Virtual Environment
```
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

```
3. Build the Secure Runner Image

docker build -t safe-python-runner:latest runner_image

Verify:

docker images | grep safe-python-runner
```
4. Start the API

source venv/bin/activate
python app.py
```
- API runs at:
cpp
http://127.0.0.1:5000/
![alt text](<Screenshot 2025-12-09 234907.png>)
```

Testing the API
```
Test 1 — Basic Code

Create file:

cat > /tmp/test1.json <<'EOF'
{"code":"print('Hello World')"}
EOF
```
Execute:


curl -s -X POST http://127.0.0.1:5000/run \
  -H "Content-Type: application/json" \
  --data @/tmp/test1.json
  ```
Expected:

json
{"output": "Hello World"}
![alt text](<code excuter.png>)
![alt text](<Screenshot 2025-12-11 005246.png>)

```
Test 2 — Multi-line Code

{"code":"print('Hello')\nfor i in range(3): print(i)"}
Expected:

nginx
Hello
0
1
2
```
Test 3 — Infinite Loop (Timeout)

{"code":"while True:\n    pass"}
```
Expected:

{"error": "Execution timed out after 10 seconds"}
c:\users\rahul sayya\OneDrive\Pictures\Screenshots\Screenshot 2025-12-11 005246.png
```
Test 4 — Memory Exhaustion

{"code":"x='a'*1000000000\nprint(len(x))"}
```
Expected:

{"error":"Process killed: out-of-memory (container exceeded memory limit)"}
c:\Users\Rahul Sayya\OneDrive\Pictures\Screenshots\Screenshot 2025-12-09 234808.png

```

Test 5 — Network Access Blocked

{"code":"import socket\nsocket.socket().connect(('example.com',80))"}
```
Expected:

{"error": "Network access is disabled"}
C:\Users\Rahul Sayya\OneDrive\Pictures\Screenshots\Screenshot 2025-12-11 010057.png
C:\users\rahul sayya\OneDrive\Pictures\Screenshots\Screenshot 2025-12-10 011443.png
```

### Security Architecture 

The project uses Docker to isolate execution through:
- Resource limits
- --memory=128m
- --cpus=.5
- --pids-limit=64
- Restricted privileges
- Non-root user
- Dropped capabilities
- Read-only filesystem
- no-new-privileges flag
- Namespace isolation
- --network none
- Isolated filesystem
- Temporary script directory

### Execution Flow Diagram ###

User -> POST /run -> Flask API -> Write script to /tmp
             |
             V
        Docker Container
        -----------------
        - Non-root user
        - No network
        - Memory-limited
        - Timeout applied
             |
             V
        Output returned

Cleaning Up Containers

During testing you may leave containers running.

Check running containers:

docker ps
Stop all:
```
docker ps -q | xargs -r docker stop
Remove unused containers:
```
docker container prune -f
```
- Limitations

This sandbox is not production-grade.

- Limitations include:

- Docker is not a complete security boundary; kernel exploits can escape containers.
- No rate limiting, multi-tenancy, or authentication.
- The host timeout tool may have edge-case issues.
- Network isolation prevents real external request testing.
- Running the API with access to Docker socket is dangerous.

# safe-code-executor
