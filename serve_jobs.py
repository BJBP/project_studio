# Long tasks of the Studio server (compile, install, cable bridge) run in the background so the page does not wait.
# start(key, argv, message, live) runs a command; status(key) -> {"state": idle|running|ok|error|stopped, "message"}
# (its last line; with live=True also while it runs); stop(key) ends it.
import atexit
import subprocess
import threading

_jobs: dict = {}
_procs: dict = {}
_lock = threading.Lock()


def _set(key: str, **fields) -> None:
    with _lock:
        _jobs[key] = {**_jobs.get(key, {}), **fields}


def _run(key: str, argv: list, live: bool) -> None:
    try:
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                encoding="utf-8", errors="replace")
    except OSError as err:
        return _set(key, state="error", message=f"E_JOB: no se pudo ejecutar ({err})")
    with _lock:
        _procs[key] = proc
    last = "E_JOB: sin salida"
    for line in proc.stdout:
        if line.strip():
            last = line.strip()
            if live:
                _set(key, message=last)
    proc.wait()
    with _lock:
        stopped = _procs.pop(key, None) is None
    _set(key, state="stopped" if stopped else "ok" if proc.returncode == 0 else "error", message=last)


def start(key: str, argv: list, message: str, live: bool = False) -> bool:
    """False if that job is already running."""
    with _lock:
        if _jobs.get(key, {}).get("state") == "running":
            return False
        _jobs[key] = {"state": "running", "message": message}
    threading.Thread(target=_run, args=(key, argv, live), daemon=True).start()
    return True


def stop(key: str) -> bool:
    """True if it was running (it is then ended and waited for)."""
    with _lock:
        proc = _procs.pop(key, None)
    if not proc:
        return False
    proc.terminate()
    proc.wait(timeout=10)
    _set(key, state="stopped")
    return True


@atexit.register
def _stop_all() -> None:
    """The cable bridge holds the board's port: it must not outlive the Studio."""
    for proc in list(_procs.values()):
        proc.terminate()


def status(key: str) -> dict:
    with _lock:
        return dict(_jobs.get(key, {"state": "idle", "message": ""}))
