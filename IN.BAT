============================================================
  BRN Node - Windows (modo CLIENTE)
============================================================

[ok] Pasta correta
[ok] Python 3.12.10

[i] Configuracao atual:
    BOOTSTRAP_PEERS = 192.168.0.19:6001
    NODE_PASSWORD   = senha-no-cliente-2026
    WEB_PASS        = senha-carteira-2026
    NETWORK_SECRET  = (vazio - modo legado, sem HMAC)

[i] Removendo node_identity.enc antigo...
[ok] Removido

[i] Atualizando bootstrap_peers.json...
[ok] bootstrap_peers.json = ["192.168.0.19:6001"]
[i] Atualizando brn_network.env...
[ok] brn_network.env atualizado

[i] Testando conexao com 192.168.0.19:6001...
[ok] Maquina A acessivel em 192.168.0.19:6001

============================================================
  Iniciando BRN Node em modo CLIENTE
============================================================
  Ctrl+C para encerrar

[INFO ] Auth de blocos: INATIVO
[INFO ] Identidade nova criada: ...
[INFO ] Cliente: DB vazio. Aguardando genesis da rede...
[Bootstrap] Conectado: 192.168.0.19:6001
[Sync] 192.168.0.19:6001: 0 -> 6364
[Sync] lote 1-51: +50 blocos (altura 50)
[Sync] lote 51-101: +50 blocos (altura 100)
...
[Sync] 192.168.0.19:6001: OK — +6364 blocos em 2341ms