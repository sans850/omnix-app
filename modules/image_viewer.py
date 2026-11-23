import streamlit as st
from pathlib import Path

@st.dialog("🖼️ Visualizador OMNIX HD", width="large")
def _render_dialog_imagem(caminho_str: str, legenda: str = ""):
    p = Path(caminho_str)
    if not p.exists():
        st.error("Imagem não encontrada.")
        return

    st.image(str(p), caption=legenda or p.name, width="stretch")

    c_info, c_share, c_dl, c_close = st.columns([2.0, 1.3, 1.4, 0.8])
    c_info.caption(f"📄 `{p.name}` • `{p.stat().st_size / (1024*1024):.2f} MB`")

    with c_share.popover("📤 Compartilhar", width="stretch"):
        st.caption("Escolha onde compartilhar:")
        if st.button("🌐 Publicar no Feed", key=f"sh_feed_{p.name}", width="stretch"):
            from modules.social import criar_post_permanente
            uid = st.session_state.get("usuario_id", "admin")
            criar_post_permanente(uid, "Membro", f"Compartilhado: {legenda or p.name}", p.open("rb"))
            st.success("✅ Publicado no Feed!")
        st.download_button(
            label="📲 Salvar Arquivo",
            data=p.read_bytes(),
            file_name=p.name,
            key=f"sh_dl_{p.name}",
            width="stretch"
        )

    c_dl.download_button(
        label="⬇️ Baixar HD",
        data=p.read_bytes(),
        file_name=p.name,
        type="primary",
        key=f"dl_modal_{p.name}",
        width="stretch"
    )

    if c_close.button("✕", key=f"cls_modal_{p.name}", width="stretch", help="Fechar"):
        st.session_state.pop("imagem_modal_alvo", None)
        st.rerun()

def verificar_e_abrir_modal_global():
    alvo = st.session_state.get("imagem_modal_alvo")
    if alvo and Path(alvo["caminho"]).exists():
        _render_dialog_imagem(alvo["caminho"], alvo.get("legenda", ""))

def abrir_modal_imagem(caminho_str: str, legenda: str = ""):
    st.session_state["imagem_modal_alvo"] = {"caminho": str(caminho_str), "legenda": legenda}
    st.rerun()

def ativar_lightbox_global():
    pass

def exibir_imagem_interativa(caminho_str: str, key_prefix: str, largura_thumb: int = 340, legenda: str = "", usar_largura_total: bool = False):
    p = Path(caminho_str)
    if not p.exists():
        return

    if usar_largura_total:
        st.image(str(p), caption=legenda if legenda else None, width="stretch")
    else:
        st.image(str(p), caption=legenda if legenda else None, width=largura_thumb)

    b_zoom, b_dl, _ = st.columns([1.45, 0.75, 3.8])
    if b_zoom.button("⛶ Tela Cheia", key=f"zm_{key_prefix}", type="primary", width="stretch", help="Abrir imagem em alta definição"):
        abrir_modal_imagem(str(p), legenda)
    b_dl.download_button(
        label="⬇️",
        data=p.read_bytes(),
        file_name=p.name,
        key=f"dl_dir_{key_prefix}",
        width="stretch",
        help="Baixar arquivo original"
    )
