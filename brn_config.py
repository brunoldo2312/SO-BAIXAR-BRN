"""brn_config.py — Configuracao do no BRN (v2)."""
import os
import json
from pathlib import Path


class Config:
    DEFAULTS = {
        "web_port": 5000,
        "explorer_port": 8080,
        "p2p_port": 6001,
        "db_path": "brn_v2_chain.db",
        "read_only": False,
        "headless": False,
        "miner_enabled": True,
        "upnp": True,
        "log_level": "INFO",
        "log_file": "",
        "tracker_url": "https://brn-tracker.onrender.com",
        "github": {"user": "", "repo": "", "token": ""},
        "bootstrap_peers": [],
    }

    def __init__(self, path="config.json"):
        self.source = path
        self.data = dict(self.DEFAULTS)
        self.data["github"] = dict(self.DEFAULTS["github"])
        self.data["bootstrap_peers"] = []

        p = Path(path)
        if p.exists():
            try:
                with open(p, "r", encoding="utf-8") as f:
                    user = json.load(f)
                for k, v in user.items():
                    if k == "github" and isinstance(v, dict):
                        self.data["github"].update(v)
                    elif k == "bootstrap_peers" and isinstance(v, list):
                        self.data["bootstrap_peers"] = v
                    else:
                        self.data[k] = v
                self.source = f"{path} + env"
            except Exception as e:
                print(f"[config] aviso: nao consegui ler {path}: {e}")

    def __getitem__(self, key):
        return self.data.get(key)

    def get(self, key, default=None):
        return self.data.get(key, default)

    def apply_to_env(self):
        mapping = {
            "web_port": "BRN_WEB_PORT",
            "explorer_port": "BRN_EXPLORER_PORT",
            "p2p_port": "BRN_P2P_PORT",
            "db_path": "BRN_DB_PATH",
            "tracker_url": "BRN_TRACKER",
        }
        for k, env in mapping.items():
            v = self.data.get(k)
            if v is not None and env not in os.environ:
                os.environ[env] = str(v)