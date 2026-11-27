import os
import sys
import time
import subprocess
import requests

PYTHON_EXE = sys.executable
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

backend_script = os.path.join(PROJECT_DIR, "backend", "main.py")
backend_cwd = os.path.join(PROJECT_DIR, "backend") if os.path.exists(backend_script) else PROJECT_DIR
main_file = "main.py" if os.path.exists(backend_script) else "main.py"

print(f"[Runner] Using Python: {PYTHON_EXE}")
print(f"[Runner] Starting FastAPI from {backend_cwd} in background...")

server_proc = subprocess.Popen(
    [PYTHON_EXE, "main.py"],
    cwd=backend_cwd,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

try:
    print("[Runner] Waiting for server on http://127.0.0.1:8000/ ...")
    online = False
    for i in range(25):
        time.sleep(1)
        try:
            r = requests.get("http://127.0.0.1:8000/", timeout=2)
            if r.status_code == 200:
                print(f"[Runner] Server is ready after {i+1}s! Health: {r.json()}")
                online = True
                break
        except Exception:
            pass

    if not online:
        print("[Runner] ERROR: Server did not come online in time.")
        sys.exit(1)

    print("\n[Runner] Executing evals/test_suite.py against live server...")
    test_result = subprocess.run(
        [PYTHON_EXE, "evals/test_suite.py"],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True
    )
    print(test_result.stdout)
    if test_result.stderr:
        print("STDERR:\n", test_result.stderr)

finally:
    print("[Runner] Shutting down FastAPI server...")
    server_proc.terminate()
    try:
        server_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_proc.kill()
    print("[Runner] Server stopped.")
