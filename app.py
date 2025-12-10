# app.py
import os
import shutil
import uuid
import tempfile
import subprocess
from flask import Flask, request, jsonify, render_template_string


app = Flask(__name__)

# Config
MAX_CODE_CHARS = 5000
TIMEOUT_SECONDS = 10
MEMORY_LIMIT = "128m"               # container memory cap
PYTHON_RUNNER_IMAGE = "safe-python-runner:latest"  # use local image that runs non-root

INDEX_HTML = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Safe Code Executor</title></head>
<body>
  <h2>Safe Code Executor</h2>
  <textarea id="code" rows="12" cols="80" placeholder='print("Hello World")'></textarea><br/>
  <button onclick="run()">Run</button>
  <pre id="output" style="white-space:pre-wrap; background:#f6f6f6; padding:10px; border:1px solid #ddd;"></pre>
  <script>
    async function run(){
      const code = document.getElementById('code').value;
      const res = await fetch('/run', {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({code})
      });
      const data = await res.json();
      document.getElementById('output').textContent = JSON.stringify(data, null, 2);
    }
  </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(INDEX_HTML)

@app.route("/run", methods=["POST"])
def run_code():
    body = request.get_json(force=True)
    code = body.get("code")
    if not isinstance(code, str):
        return jsonify({"error": "code must be a string"}), 400
    if len(code) > MAX_CODE_CHARS:
        return jsonify({"error": f"code too long (max {MAX_CODE_CHARS})"}), 400

    run_id = str(uuid.uuid4())
    tempdir = os.path.join(tempfile.gettempdir(), f"safeexec-{run_id}")
    os.makedirs(tempdir, exist_ok=True)
    script_path = os.path.join(tempdir, "script.py")
    with open(script_path, "w", encoding="utf-8") as f:
        f.write(code)

    docker_cmd = [
        "docker", "run", "--rm",
        "--network", "none",
        "--memory", MEMORY_LIMIT,
        "--pids-limit", "64",
        "--read-only",
        "--security-opt", "no-new-privileges:true",
        "--cap-drop=ALL",
        "--volume", f"{tempdir}:/app:ro",   # mount script read-only
        PYTHON_RUNNER_IMAGE,
        "python", "/app/script.py"
    ]
    # host-level timeout
    exec_cmd = ["timeout", f"{TIMEOUT_SECONDS}s"] + docker_cmd

    try:
        completed = subprocess.run(exec_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except FileNotFoundError as e:
        shutil.rmtree(tempdir, ignore_errors=True)
        missing = "docker" if "docker" in str(e).lower() else "timeout"
        return jsonify({"error": f"Required tool not found: {missing}"}), 500

    shutil.rmtree(tempdir, ignore_errors=True)

    # 124 = timeout (GNU timeout)
    if completed.returncode == 124:
        return jsonify({"error": f"Execution timed out after {TIMEOUT_SECONDS} seconds"}), 400

    if completed.returncode != 0:
        return jsonify({
            "output": completed.stdout.strip(),
            "error": (completed.stderr.strip() or f"container exited with code {completed.returncode}")
        }), 400

    return jsonify({"output": completed.stdout.rstrip("\n")})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
