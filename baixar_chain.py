"""
baixar_chain.py v4 — Compatível com p2p_unified v6.3
  - Usa get_blocks_range (nao existe get_block no P2PClient)
  - Sleep entre lotes (evita rate limit)
  - Retry 3x por lote
  - Continua de onde parou
"""
import sys
import os
import time
from pathlib import Path

if len(sys.argv) < 3:
    print("Uso: python baixar_chain.py <IP> <PORTA>")
    print("Ex:  python baixar_chain.py 192.168.0.3 6001")
    sys.exit(1)

PEER_IP = sys.argv[1]
PEER_PORT = int(sys.argv[2])

print("=" * 60)
print(f"  BAIXAR CHAIN v4 — peer {PEER_IP}:{PEER_PORT}")
print("=" * 60)

# ============================================================
# 1. AUTH
# ============================================================
os.environ.setdefault("BRN_NODE_PASSWORD", "senha-da-carteira-2026")
SENHA = os.environ["BRN_NODE_PASSWORD"]

try:
    from crypto import Ed25519PrivateKey
    from secure_store import load_wallet
    from p2p_auth import set_node_id_priv

    if Path("node_identity.enc").exists():
        data = load_wallet("node_identity.enc", SENHA)
        sk = Ed25519PrivateKey.from_private_bytes(bytes.fromhex(data["sk"]))
        set_node_id_priv(sk)
        print(f"[Auth] Identidade carregada: {data['pub'][:16]}...")
except Exception as e:
    print(f"[Auth] AVISO: {e}")

# ============================================================
# 2. ABRE BLOCKCHAIN
# ============================================================
from p2p_unified import P2PClient
from blockchain import Blockchain

bc = Blockchain("brn_v2_chain.db", auto_genesis=False)
altura_local = bc.db.height()
print(f"Altura local: {altura_local}")

# ============================================================
# 3. VERIFICA GENESIS DO PEER (usa get_blocks_range)
# ============================================================
print("\n[Verificando genesis do peer]...")
r_gen, _ = P2PClient.get_blocks_range(PEER_IP, PEER_PORT, 0, 1)
if not r_gen or "blocks" not in r_gen or not r_gen["blocks"]:
    print("ERRO: nao consegui obter genesis do peer")
    sys.exit(1)

genesis_remoto = r_gen["blocks"][0]
print(f"  Peer genesis: {genesis_remoto['hash'][:32]}...")

genesis_local = bc.db.get_block(0)

if genesis_local:
    print(f"  Local genesis: {genesis_local['hash'][:32]}...")
    if genesis_local["hash"] != genesis_remoto["hash"]:
        print("\n⚠️  GENESIS DIFERENTE!")
        print(f"   Rode: python reset_e_sync.py {PEER_IP} {PEER_PORT}")
        sys.exit(1)
    print("  ✅ Genesis IGUAL")
    inicio = max(0, altura_local - 5) if altura_local > 5 else 0
    print(f"  Baixando a partir do bloco {inicio} (ancora)")
else:
    print("  Genesis local vazio — baixando tudo desde 0")
    inicio = 0

# ============================================================
# 4. ALTURA DO PEER
# ============================================================
resp, _ = P2PClient.get_chain_height(PEER_IP, PEER_PORT)
if not resp:
    print("ERRO: peer nao respondeu")
    sys.exit(1)

altura_remota = resp.get("height", -1)
print(f"\nAltura remota: {altura_remota}")

if altura_remota <= altura_local:
    print("Nada a baixar")
    sys.exit(0)

# ============================================================
# 5. BAIXA COM SLEEP E RETRY
# ============================================================
print(f"\nBaixando blocos {inicio} a {altura_remota}...")
todos = []
cursor = inicio
t0 = time.time()

while cursor <= altura_remota:
    fim = min(cursor + 50, altura_remota + 1)
    print(f"  {cursor} a {fim-1}...", end=" ")

    lote_ok = False
    for tentativa in range(3):
        try:
            r, _ = P2PClient.get_blocks_range(PEER_IP, PEER_PORT, cursor, fim)
            if r and "blocks" in r and r["blocks"]:
                todos.extend(r["blocks"])
                print(f"OK ({len(r['blocks'])})")
                lote_ok = True
                break
            else:
                print(f"vazio (tent {tentativa+1}/3)")
                time.sleep(0.5)
        except Exception as e:
            print(f"erro (tent {tentativa+1}/3): {e}")
            time.sleep(0.5)

    if not lote_ok:
        print(f"  ❌ Lote {cursor}-{fim-1} falhou 3x — parando")
        break

    cursor = fim
    time.sleep(0.15)

dt = time.time() - t0
print(f"\nBaixados {len(todos)} blocos em {dt:.1f}s")

if not todos:
    print("Nada recebido")
    sys.exit(0)

# ============================================================
# 6. APLICA
# ============================================================
print(f"\nAplicando via reorg_to...")
ok, msg = bc.reorg_to(todos)
print(f"  reorg_to: ok={ok}, msg={msg}")

# ============================================================
# 7. RESULTADO
# ============================================================
altura_final = bc.db.height()
print(f"\nAltura final: {altura_final} (era {altura_local})")

if altura_final > altura_local:
    print(f"\n✅ SUCESSO! +{altura_final - altura_local} blocos")
    if altura_final < altura_remota:
        print(f"\n⚠️  Ainda falta: {altura_remota - altura_final} blocos")
        print(f"   Rode novamente para continuar:")
        print(f"   python baixar_chain.py {PEER_IP} {PEER_PORT}")
else:
    print(f"\n⚠️  Nao sincronizou.")