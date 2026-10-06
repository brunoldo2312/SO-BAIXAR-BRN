"""
watchdog.py — Mantém o nó BRN vivo e conectado.
=====================================================
- Monitora /health a cada 15s
- Se o nó parar de responder por 3 verificações seguidas,
  mata o processo e reinicia main.py
- Se peers caírem para 0, também força reconexão
- Sobrevive a Ctrl+C e SIGTERM
"""
import os
import sys
import time
import signal
import subprocess
import threading

try:
    import requests
except ImportError:
    print("Instale: python -m pip install requests")
    sys.exit(1)

# ============================================================
# CONFIG
# ============================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PY = os.path.join(BASE_DIR, "main.py")
API_URL = "http://127.0.0.1:5000"
HEALTH_URL = f"{API_URL}/health"
STATUS_URL = f"{API_URL}/api/status"

CHECK_INTERVAL   = 15     # segundos entre cada checagem
MAX_FAILS        = 3      # 3 falhas seguidas → reinicia
RESTART_DELAY    = 10     # espera antes de reiniciar
MIN_PEERS        = 1      # se ficar < isso por N checks, força reconexão

# ============================================================
# ESTADO
# ============================================================
process = None
_running = True
_fail_count = 0
_peer_fail_count = 0


def log(msg):
    print(f"[vigia {time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ============================================================
# CONTROLE DE PROCESSO
# ============================================================
def start_node():
    global process
    log(f"Iniciando: python {MAIN_PY}")
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    process = subprocess.Popen(
        [sys.executable, MAIN_PY],
        cwd=BASE_DIR,
        env=env,
    )
    log(f"Nó iniciado com PID={process.pid}")


def stop_node():
    global process
    if process and process.poll() is None:
        log(f"Encerrando PID={process.pid}...")
        try:
            process.terminate()
            for _ in range(10):
                if process.poll() is not None:
                    break
                time.sleep(0.5)
            if process.poll() is None:
                log("Forçando kill...")
                process.kill()
        except Exception as e:
            log(f"Erro ao encerrar: {e}")
    process = None


def is_process_alive():
    return process is not None and process.poll() is None


# ============================================================
# CHECAGENS
# ============================================================
def check_health() -> bool:
    try:
        r = requests.get(HEALTH_URL, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def check_peers() -> int:
    """Retorna nº de peers ativos ou -1 em caso de erro."""
    try:
        r = requests.get(STATUS_URL, timeout=5)
        if r.status_code != 200:
            return -1
        return int(r.json().get("peers", 0))
    except Exception:
        return -1


# ============================================================
# LOOP PRINCIPAL
# ============================================================
def watchdog_loop():
    global _fail_count, _peer_fail_count

    while _running:
        time.sleep(CHECK_INTERVAL)

        # 1) Processo morreu?
        if not is_process_alive():
            log("⚠️  Processo morreu. Reiniciando...")
            time.sleep(RESTART_DELAY)
            start_node()
            _fail_count = 0
            _peer_fail_count = 0
            continue

        # 2) /health responde?
        if check_health():
            _fail_count = 0
        else:
            _fail_count += 1
            log(f"⚠️  /health falhou ({_fail_count}/{MAX_FAILS})")
            if _fail_count >= MAX_FAILS:
                log("🔴 Nó travado. Reiniciando...")
                stop_node()
                time.sleep(RESTART_DELAY)
                start_node()
                _fail_count = 0
                _peer_fail_count = 0
                continue

        # 3) Peers ativos?
        peers = check_peers()
        if peers == 0:
            _peer_fail_count += 1
            log(f"⚠️  Peers=0 ({_peer_fail_count}/6)")
            if _peer_fail_count >= 6:  # ~90s sem peers
                log("🔴 Sem peers há 90s. Reiniciando para reconectar...")
                stop_node()
                time.sleep(RESTART_DELAY)
                start_node()
                _fail_count = 0
                _peer_fail_count = 0
                continue
        else:
            _peer_fail_count = 0


# ============================================================
# SHUTDOWN
# ============================================================
def _handle_signal(signum, frame):
    global _running
    log("Sinal recebido. Encerrando...")
    _running = False


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 60)
    print("  BRN Watchdog — mantém o nó vivo e conectado")
    print("=" * 60)
    print(f"  Check a cada : {CHECK_INTERVAL}s")
    print(f"  Reinicia após: {MAX_FAILS} falhas de /health")
    print(f"  Sem peers por: 90s → reinicia")
    print(f"  Ctrl+C       : encerra o watchdog e o nó")
    print("=" * 60)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    start_node()

    t = threading.Thread(target=watchdog_loop, daemon=True)
    t.start()

    try:
        while _running:
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    stop_node()
    print("Watchdog encerrado.")


if __name__ == "__main__":
    main()
