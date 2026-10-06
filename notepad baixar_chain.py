"""
baixar_chain.py — Baixa a blockchain completa de um peer.
Uso: python baixar_chain.py <IP> <PORTA>
Ex:  python baixar_chain.py 192.168.0.10 6001
"""
import sys
import time
from pathlib import Path

if len(sys.argv) < 3:
    print("Uso: python baixar_chain.py <IP> <PORTA>")
    print("Ex:  python baixar_chain.py 192.168.0.10 6001")
    sys.exit(1)

PEER_IP = sys.argv[1]
PEER_PORT = int(sys.argv[2])

print(f"=" * 60)
print(f"  BAIXAR CHAIN — peer {PEER_IP}:{PEER_PORT}")
print(f"=" * 60)

from p2p_unified import P2PClient
from blockchain import Blockchain

bc = Blockchain("brn_v2_chain.db", auto_genesis=False)
altura_local = bc.db.height()
print(f"Altura local: {altura_local}")

# 1) Pega altura do peer
resp, lat = P2PClient.get_chain_height(PEER_IP, PEER_PORT)
if not resp:
    print(f"ERRO: peer {PEER_IP}:{PEER_PORT} nao respondeu")
    sys.exit(1)

altura_remota = resp.get("height", -1)
work_remoto = resp.get("work", 0)
print(f"Altura remota: {altura_remota}")
print(f"Work remoto: {work_remoto}")

if altura_remota <= altura_local:
    print("Nada a baixar (ja estamos sincronizados)")
    sys.exit(0)

# 2) Baixa em lotes de 50
inicio = altura_local + 1
todos_blocos = []
cursor = inicio
t0 = time.time()

while cursor <= altura_remota:
    fim = min(cursor + 50, altura_remota + 1)
    print(f"  Baixando blocos {cursor} a {fim-1}...")
    r, _ = P2PClient.get_blocks_range(PEER_IP, PEER_PORT, cursor, fim)
    if not r or "blocks" not in r:
        print(f"  ERRO no lote {cursor}-{fim}")
        break
    lote = r["blocks"]
    if not lote:
        print(f"  Lote vazio — parando")
        break
    todos_blocos.extend(lote)
    cursor = fim

dt = time.time() - t0
print(f"\nBaixados {len(todos_blocos)} blocos em {dt:.1f}s")

if not todos_blocos:
    print("Nada recebido")
    sys.exit(0)

# 3) Aplica com reorg
print(f"\nAplicando {len(todos_blocos)} blocos...")
ok, msg = bc.reorg_to(todos_blocos)
print(f"reorg_to: ok={ok}, msg={msg}")

# 4) Verifica altura final
altura_final = bc.db.height()
print(f"\nAltura final: {altura_final} (era {altura_local})")

if altura_final > altura_local:
    print(f"✅ Sincronizado! +{altura_final - altura_local} blocos")
else:
    print(f"⚠️ Nao sincronizou. Verifique os logs.")