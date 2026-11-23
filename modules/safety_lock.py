import json
from pathlib import Path

LOCK_FILE = Path("omnix_safety_lock.json")

DEFAULT_CONFIG = {
    "ativa": True,
    "max_arquivos_lote": 8,
    "max_mb_arquivo": 25,
    "max_dimensao_px": 2560,
    "max_qualidade_video": "720"
}

def obter_config_trava() -> dict:
    if LOCK_FILE.exists():
        try:
            data = json.loads(LOCK_FILE.read_text(encoding="utf-8"))
            cfg = DEFAULT_CONFIG.copy()
            cfg.update(data)
            return cfg
        except Exception:
            pass
    salvar_config_trava(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()

def salvar_config_trava(cfg: dict):
    LOCK_FILE.write_text(json.dumps(cfg, indent=2), encoding="utf-8")

def alternar_trava_seguranca() -> bool:
    cfg = obter_config_trava()
    cfg["ativa"] = not cfg.get("ativa", True)
    salvar_config_trava(cfg)
    return cfg["ativa"]
