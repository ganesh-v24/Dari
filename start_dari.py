import subprocess
import threading
import sys
import os
import time

def stream_output(process, label):
    """Stream output from a process with a label."""
    for line in iter(process.stdout.readline, ''):
        if line:
            print(f"[{label}] {line.strip()}")
    process.stdout.close()

def start_backend():
    print("[System] Starting Backend...")
    backend_dir = os.path.join(os.getcwd(), "backend")
    # Using python -m uvicorn to ensure it uses the current environment
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--port", "8000"],
        cwd=backend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process

def start_frontend():
    print("[System] Starting Frontend...")
    frontend_dir = os.path.join(os.getcwd(), "web")
    # Using npm.cmd for Windows compatibility
    process = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=frontend_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    return process

if __name__ == "__main__":
    try:
        backend_proc = start_backend()
        frontend_proc = start_frontend()

        # Create threads to stream output
        t1 = threading.Thread(target=stream_output, args=(backend_proc, "BACKEND"))
        t2 = threading.Thread(target=stream_output, args=(frontend_proc, "FRONTEND"))

        t1.start()
        t2.start()

        print("\n🚀 Dari is now starting up!")
        print("📍 Backend: http://localhost:8000")
        print("📍 Frontend: http://localhost:5173")
        print("Press Ctrl+C to stop everything.\n")

        # Keep the main thread alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[System] Shutting down...")
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(0)
