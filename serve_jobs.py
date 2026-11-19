# Long tasks of the Studio server (compile, install) run in the background so the page does not wait.
# start(key, argv, message) runs a command; status(key) -> {"state": idle|running|ok|error, "message"} (its last line).
import subprocess
import threading

_jobs: dict = {}
_lock = threading.Lock()


def _run(key: str, argv: list) -> None:
    try:
        done = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace")
        last = (done.stdout.strip().splitlines() or ["E_JOB: sin salida"])[-1]
        state = "ok" if done.returncode == 0 else "error"
    except OSError as err:
        last, state = f"E_JOB: no se pudo ejecutar ({err})", "error"
    with _lock:
        _jobs[key] = {"state": state, "message": last}


def start(key: str, argv: list, message: str) -> bool:
    """False if that job is already running."""
    with _lock:
        if _jobs.get(key, {}).get("state") == "running":
            return False
        _jobs[key] = {"state": "running", "message": message}
    threading.Thread(target=_run, args=(key, argv), daemon=True).start()
    return True


def status(key: str) -> dict:
    with _lock:
        return dict(_jobs.get(key, {"state": "idle", "message": ""}))
