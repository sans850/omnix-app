import streamlit as st
import json
from pathlib import Path
from datetime import datetime
import shutil

OPT_CONFIG = Path("optimizer_config.json")

DEFAULT_OPT = {
    "auto_limpar_horas": 24,
    "limite_disco_mb": 500,
    "modo_eco_chat_seg": 5
}

def carregar_opt_config() -> dict:
    if not OPT_CONFIG.exists():
        salvar_opt_config(DEFAULT_OPT)
        return DEFAULT_OPT.copy()
    try:
        dados = json.loads(OPT_CONFIG.read_text(encoding="utf-8"))
        for k, v in DEFAULT_OPT.items():
            dados.setdefault(k, v)
        return dados
    except Exception:
        return DEFAULT_OPT.copy()

def salvar_opt_config(cfg: dict):
    OPT_CONFIG.write_text(json.dumps(cfg, indent=4), encoding="utf-8")

def executar_faxina_automatica(storage_dir: Path) -> int:
    cfg = carregar_opt_config()
    horas_max = cfg.get("auto_limpar_horas", 24)
    if horas_max <= 0:
        return 0
        
    agora = datetime.now().timestamp()
    segundos_max = horas_max * 3600
    removidos = 0
    
    for arq in storage_dir.rglob("*"):
        if arq.is_file():
            idade = agora - arq.stat().st_mtime
            if idade > segundos_max:
                arq.unlink(missing_ok=True)
                removidos += 1
    return removidos

def obter_status_sistema(storage_dir: Path) -> dict:
    arquivos = [f for f in storage_dir.rglob("*") if f.is_file()]
    tamanho_mb = sum(f.stat().st_size for f in arquivos) / (1024 * 1024)
    total, usado, livre = shutil.disk_usage(storage_dir.resolve())
    return {
        "qtd_arquivos": len(arquivos),
        "uso_omnix_mb": round(tamanho_mb, 2),
        "disco_livre_gb": round(livre / (1024 ** 3), 1)
    }

def render_painel_otimizacao(storage_dir: Path):
    st.subheader("⚡ Otimização & Alívio de Carga do Servidor")
    st.caption("Configure limites automáticos para o OMNIX não pesar no notebook ou na nuvem.")
    
    cfg = carregar_opt_config()
    stats = obter_status_sistema(storage_dir)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Uso do OMNIX Drive", f"{stats['uso_omnix_mb']} MB", f"Limite: {cfg['limite_disco_mb']} MB")
    c2.metric("Arquivos Temporários", stats["qtd_arquivos"])
    c3.metric("Espaço Livre no Disco", f"{stats['disco_livre_gb']} GB")
    
    with st.container(border=True):
        horas = st.slider(
            "🕒 Apagar downloads/conversões do Drive automaticamente após (horas):",
            min_value=1, max_value=168, value=int(cfg["auto_limpar_horas"]),
            help="Posts do feed, avatares e chats NÃO são apagados por esta regra."
        )
        limite_mb = st.number_input(
            "📦 Alerta de limite máximo do Drive (MB):",
            min_value=100, max_value=10000, value=int(cfg["limite_disco_mb"]), step=100
        )
        
        col_b1, col_b2 = st.columns(2)
        if col_b1.button("💾 Salvar Regras de Economia", type="primary", width="stretch"):
            cfg["auto_limpar_horas"] = horas
            cfg["limite_disco_mb"] = limite_mb
            salvar_opt_config(cfg)
            st.success("Regras de otimização salvas!")
            st.rerun()
            
        if col_b2.button("🧹 Rodar Faxina Agora", width="stretch"):
            qtd = executar_faxina_automatica(storage_dir)
            st.info(f"Faxina concluída! {qtd} arquivo(s) antigo(s) removido(s).")

