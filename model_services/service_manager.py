# model_services/service_manager.py
import os
import sys
import time
import subprocess
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = BASE_DIR / ".venv" / "Scripts" / "python.exe"
if not (PYTHON_EXE.exists() and (BASE_DIR / ".venv" / "Lib" / "site-packages" / "torch").exists()):
    PYTHON_EXE = Path(sys.executable)

def check_service_health(port: int, service_name: str) -> bool:
    import urllib.request
    import json
    url = f"http://127.0.0.1:{port}/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HealthChecker"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                print(f"[{service_name}] Status: {data.get('status')} | Device: {data.get('device')} | GPU: {data.get('gpu_device', 'N/A')}")
                return True
    except Exception as e:
        print(f"[{service_name}] Not reachable at {url}: {e}")
    return False

def start_changestar():
    print("Starting ChangeStar microservice on port 8001...")
    cmd = [
        str(PYTHON_EXE), "-m", "uvicorn",
        "model_services.changestar_server:app",
        "--host", "127.0.0.1",
        "--port", "8001"
    ]
    return subprocess.Popen(cmd, cwd=str(BASE_DIR))

def start_croma():
    print("Starting CROMA microservice on port 8002...")
    cmd = [
        str(PYTHON_EXE), "-m", "uvicorn",
        "model_services.croma_server:app",
        "--host", "127.0.0.1",
        "--port", "8002"
    ]
    return subprocess.Popen(cmd, cwd=str(BASE_DIR))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SatQuery AI Model Services Manager")
    parser.add_argument("--action", choices=["start_all", "start_changestar", "start_croma", "status"], default="status")
    args = parser.parse_args()

    if args.action == "status":
        print("--- Checking Model Services Status ---")
        cs_ok = check_service_health(8001, "ChangeStar")
        cr_ok = check_service_health(8002, "CROMA")
        if cs_ok and cr_ok:
            print("All SatQuery AI model services are ONLINE and HEALTHY.")
        else:
            print("One or more services offline.")
    elif args.action == "start_changestar":
        p = start_changestar()
        p.wait()
    elif args.action == "start_croma":
        p = start_croma()
        p.wait()
    elif args.action == "start_all":
        p1 = start_changestar()
        p2 = start_croma()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            p1.terminate()
            p2.terminate()
