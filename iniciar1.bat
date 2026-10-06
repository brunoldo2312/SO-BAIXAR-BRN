@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion
cd /d "%~dp0"

REM ============================================================
REM   BRN Node - CLIENTE (SINCRONIZA DA MAQUINA A)
REM ============================================================
REM   Este .bat foi ajustado para rodar como CLIENTE:
REM     - NAO cria genesis
REM     - Espera receber o bloco 0 de um peer (Maquina A)
REM     - Baixa toda a cadeia automaticamente
REM ============================================================

echo ============================================================
echo   BRN Node - CLIENTE (sincroniza da Maquina A)
echo ============================================================
echo.

REM ============================================================
REM  1) CARREGA SEGREDO DO ARQUIVO brn_network.env (se existir)
REM ============================================================
set "BRN_NETWORK_SECRET="
set "BRN_TRACKER="
set "BRN_BOOTSTRAP_PEERS="

if exist "brn_network.env" (
    echo [*] Carregando brn_network.env...
    for /f "usebackq tokens=1,* delims==" %%a in ("brn_network.env") do (
        if not "%%a"=="" (
            set "%%a=%%b"
        )
    )
    echo [ok] brn_network.env carregado
) else (
    echo [!] brn_network.env NAO existe. Usando valores padrao.
    set "BRN_NETWORK_SECRET=9226edea8ba62bc1c6ae36883c0536c95b4c85642195465d6c4d9456abef20f9"
    set "BRN_TRACKER=https://brn-tracker.onrender.com"
    set "BRN_BOOTSTRAP_PEERS=177.82.132.98:6001"
)
echo.

REM ============================================================
REM  2) SENHAS LOCAIS (nao afetam a rede)
REM ============================================================
if not defined BRN_NODE_PASSWORD set "BRN_NODE_PASSWORD=senha-do-no-deste-pc-2026"
if not defined BRN_WEB_PASS set "BRN_WEB_PASS=senha-da-carteira-2026"

set "BRN_NODE_AUTORESET=1"

REM ============================================================
REM  3) PARAMETROS DE REDE / MINERACAO
REM ============================================================
set "BRN_MINER_AUTO=0"
set "BRN_MINER_INTERVAL=30"
set "BRN_ALLOW_SOLO_MINING=0"
set "BRN_MIN_PEER_STABLE=1"
set "BRN_UPNP=1"
set "BRN_P2P_AUTH=optional"
set "BRN_WEB_PORT=5000"
set "BRN_EXPLORER_PORT=8080"
set "BRN_P2P_PORT=6001"
set "BRN_SYNC_BATCH=500"
set "BRN_SYNC_PARALELO_MIN=500"
set "BRN_SYNC_PARALELO_WORKERS=4"
set "BRN_SYNC_RETRY_MAX=5"
set "BRN_TCP_TIMEOUT=30.0"
set "BRN_LOG_LEVEL=INFO"
set "PYTHONUNBUFFERED=1"

REM ============================================================
REM  4) VERIFICA PYTHON
REM ============================================================
where python >nul 2>nul
if errorlevel 1 (
    echo [X] Python nao encontrado no PATH.
    echo     Instale em https://python.org ^(marque "Add to PATH"^)
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set "PYVER=%%i"
echo [ok] Python !PYVER!
echo.

REM ============================================================
REM  5) INSTALA DEPENDENCIAS (rapido se ja instaladas)
REM ============================================================
if exist requirements.txt (
    python -m pip install --quiet --disable-pip-version-check -r requirements.txt >nul 2>nul
) else (
    python -m pip install --quiet flask flask-cors requests orjson cryptography argon2-cffi mnemonic pywebview >nul 2>nul
)
echo [ok] Dependencias verificadas
echo.

REM ============================================================
REM  6) VERIFICA ARQUIVOS ESSENCIAIS
REM ============================================================
set "FALTA="
for %%f in (main.py server.py blockchain.py wallet.py db.py p2p_unified.py) do (
    if not exist "%%f" set "FALTA=!FALTA! %%f"
)
if not "!FALTA!"=="" (
    echo [X] Arquivos faltando:!FALTA!
    pause
    exit /b 1
)
echo [ok] Arquivos essenciais presentes
echo.

REM ============================================================
REM  7) MARCA PAPEL COMO CLIENTE
REM ============================================================
echo cliente > brn_role.txt
echo [ok] Papel: cliente ^(nao origina genesis^)
echo.

REM ============================================================
REM  8) BOOTSTRAP PEERS
REM ============================================================
if not exist bootstrap_peers.json (
    echo ["177.82.132.98:6001"] > bootstrap_peers.json
    echo [ok] bootstrap_peers.json criado
) else (
    echo [ok] bootstrap_peers.json ja existe
)
echo.

REM ============================================================
REM  9) TESTA TRACKER
REM ============================================================
echo [*] Testando tracker !BRN_TRACKER!...
python -c "import urllib.request; r=urllib.request.urlopen('!BRN_TRACKER!/', timeout=15); print('[ok]', r.read().decode().strip())" 2>nul
if errorlevel 1 (
    echo [!] Tracker nao respondeu ^(pode estar dormindo - free tier^)
)
echo.

REM ============================================================
REM 10) PYWEBVIEW
REM ============================================================
set "HEADLESS_FLAG="
python -c "import webview" 2>nul
if errorlevel 1 (
    set "HEADLESS_FLAG=--headless"
    echo [!] pywebview ausente - modo HEADLESS
) else (
    echo [ok] pywebview OK - carteira desktop vai abrir
)
echo.

REM ============================================================
REM 11) FINGERPRINT DO SEGREDO
REM ============================================================
for /f "delims=" %%i in ('python -c "import hashlib;print(hashlib.sha256('!BRN_NETWORK_SECRET!'.encode()).hexdigest()[:16])" 2^>nul') do set "SEC_FP=%%i"

REM ============================================================
REM 12) RESUMO
REM ============================================================
echo ============================================================
echo   CONFIGURACAO ATUAL (CLIENTE)
echo ============================================================
echo   Modo       : CLIENTE ^(sincroniza da rede^)
echo   Auth FP    : !SEC_FP!... ^<- deve ser IGUAL ao da Maquina A
echo   Tracker    : !BRN_TRACKER!
echo   Bootstrap  : !BRN_BOOTSTRAP_PEERS!
echo   Mineracao  : !BRN_MINER_AUTO! ^(pode ativar na carteira^)
echo   Sync batch : !BRN_SYNC_BATCH! ^(workers !BRN_SYNC_PARALELO_WORKERS!^)
echo   P2P porta  : !BRN_P2P_PORT!
echo   HTTP       : http://127.0.0.1:!BRN_WEB_PORT!
echo   Explorer   : http://127.0.0.1:!BRN_EXPLORER_PORT!
echo ============================================================
echo.
echo   ATENCAO: deixe esta janela ABERTA enquanto o cliente roda.
echo.

REM ============================================================
REM 13) INICIA O NO EM MODO CLIENTE
REM ============================================================
echo [*] Iniciando CLIENTE BRN... ^(Ctrl+C para encerrar^)
echo.
python main.py --client-mode !HEADLESS_FLAG!

set "EXITCODE=!ERRORLEVEL!"
echo.
if !EXITCODE! neq 0 (
    echo [X] O no saiu com codigo !EXITCODE!
    echo.
    echo Se o erro foi "Falha ao decifrar node_identity.enc":
    echo   1. Rode: ren node_identity.enc node_identity.enc.antiga
    echo   2. Rode este .bat de novo
    echo.
) else (
    echo [ok] No encerrado normalmente.
)
pause
endlocal