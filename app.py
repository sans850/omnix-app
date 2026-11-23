import streamlit as st
from pathlib import Path
import time
import hashlib
from streamlit_cookies_controller import CookieController

from modules.image_viewer import ativar_lightbox_global, verificar_e_abrir_modal_global
from modules.admin import render_admin, carregar_usuarios, salvar_usuarios, numero_ja_existe
from modules.social import (
    render_navegar,
    render_criar_post,
    render_perfil_avatar,
    render_amigos_hub,
    obter_notificacoes_usuario,
    marcar_todas_como_lidas
)
from modules.messages import render_messages
from modules.media import render_media
from modules.watch import render_watch_party
from modules.files import render_files
from modules.converter import render_converter
from modules.studio_hub import render_studio_hub
from modules.vision import render_vision
from modules.bot_voice import render_bot_hub
from modules.settings import render_configuracoes
from modules.optimizer import executar_faxina_automatica
from modules.friends import listar_pedidos_recebidos

st.set_page_config(
    page_title="OMNIX",
    page_icon="omnix_icon.png" if Path("omnix_icon.png").exists() else "âš¡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""<style>
.stApp { background-color: #090D16; color: #F8FAFC; }
[data-testid="stHeader"], footer, #MainMenu { visibility: hidden; height: 0; }
.block-container { padding-top: 1.2rem !important; max-width: 1180px !important; }
.omnix-logo { font-size: 1.45rem; font-weight: 800; background: linear-gradient(90deg, #A855F7, #38BDF8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
div.stButton > button { border-radius: 10px; font-weight: 600; transition: all 0.2s ease; }
</style>""", unsafe_allow_html=True)

executar_faxina_automatica(Path("omnix_storage"))

# MODO DIRETO MOBILE / APK PARA O ESTÚDIO OMNIX (?modo=estudio)
if st.query_params.get("modo", "") == "estudio":
    st.markdown("""
    <meta name="mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="theme-color" content="#090D16">
    <style>
        .block-container { padding: 0.8rem 0.9rem 2rem 0.9rem !important; max-width: 100% !important; }
        div.stButton > button { min-height: 46px !important; font-size: 15px !important; }
    </style>
    """, unsafe_allow_html=True)
    from modules.studio_hub import render_studio_hub
    render_studio_hub()
    st.stop()

USUARIOS = carregar_usuarios()

if "usuario_id" not in st.session_state:
    q_u = st.query_params.get("u", "")
    q_t = st.query_params.get("t", "")
    if q_u in USUARIOS:
        esperado = hashlib.sha256(f"{q_u}:{USUARIOS[q_u]['senha']}:omnix_secret".encode()).hexdigest()[:16]
        if q_t == esperado:
            st.session_state.usuario_id = q_u

if "usuario_id" not in st.session_state or st.session_state.usuario_id not in USUARIOS:
    st.markdown("<div style='text-align:center; padding: 24px 0 10px 0;'><span class='omnix-logo' style='font-size:2.2rem;'>âš¡ OMNIX</span><p style='color:#94A3B8;'>Conecte-se Ã  sua central social e multimÃ­dia</p></div>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1.2, 1.6, 1.2])
    with col_c:
        tab_entrar, tab_criar = st.tabs(["Entrar", "Criar Conta"])
        with tab_entrar:
            with st.form("form_login_omnix"):
                u_in = st.text_input("UsuÃ¡rio")
                s_in = st.text_input("Senha", type="password")
                if st.form_submit_button("Entrar no OMNIX", type="primary", use_container_width=True):
                    u_clean = u_in.strip().lower()
                    if u_clean in USUARIOS and USUARIOS[u_clean]["senha"] == s_in:
                        st.session_state.usuario_id = u_clean
                        tk = hashlib.sha256(f"{u_clean}:{s_in}:omnix_secret".encode()).hexdigest()[:16]
                        st.query_params["u"] = u_clean
                        st.query_params["t"] = tk
                        time.sleep(0.2)
                        st.rerun()
                    else:
                        st.error("UsuÃ¡rio ou senha invÃ¡lidos.")
        with tab_criar:
            with st.form("form_cadastro_omnix"):
                n_cad = st.text_input("Nome de exibiÃ§Ã£o")
                u_cad = st.text_input("Nome de usuÃ¡rio (sem espaÃ§os)")
                s_cad = st.text_input("Senha", type="password")
                if st.form_submit_button("Criar Conta", use_container_width=True):
                    ok_c, msg_c = registrar_usuario(u_cad.strip().lower(), n_cad.strip(), s_cad)
                    if ok_c:
                        st.success("Conta criada! FaÃ§a login na aba Entrar.")
                    else:
                        st.error(msg_c)
    st.stop()

verificar_e_abrir_modal_global()
usuario_id = st.session_state.usuario_id
user = USUARIOS[usuario_id]
if user.get("cargo") == "admin" and st.session_state.get("qa_step_state"):
    from modules.qa_simulator import exibir_popup_diagnostico_admin
    exibir_popup_diagnostico_admin()
notificacoes, nao_lidas = obter_notificacoes_usuario(usuario_id)
qtd_ped = len(listar_pedidos_recebidos(usuario_id))

# CabeÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§alho Compacto: Identidade + Nome ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  esquerda; Apenas ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­cones ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â  direita
h_left, h_right = st.columns([4.2, 1.8])
with h_left:
    if Path("omnix_icon.png").exists():
        c_ico, c_brand, c_user_info = st.columns([0.45, 1.15, 3.4])
        c_ico.image("omnix_icon.png", width=34)
        c_brand.markdown("<div class='omnix-logo' style='padding-top:3px;'>OMNIX</div>", unsafe_allow_html=True)
    else:
        c_brand, c_user_info = st.columns([1.2, 3.8])
        c_brand.markdown("<div class='omnix-logo'>ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã‚Â¡Ãƒâ€šÃ‚Â¡ OMNIX</div>", unsafe_allow_html=True)
    c_user_info.markdown(
        f"<div style='padding-top:5px; color:#E2E8F0; font-size:0.92rem;'>"
        f"OlÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¡, <b>{user['nome']}</b> <span style='color:#64748B;'>ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ Conectado</span></div>",
        unsafe_allow_html=True
    )

with h_right:
    b_notif, b_cfg, b_prof = st.columns(3)
    with b_notif:
        lbl_n = f"ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â€šÂ¬Ã‚Â {nao_lidas}" if nao_lidas > 0 else "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â€šÂ¬Ã‚Â"
        if st.button(lbl_n, key="hdr_notif", type="primary" if st.session_state.cat_ativa == "NotificaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes" else "secondary", width="stretch", help="NotificaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes"):
            st.session_state.cat_ativa = "NotificaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes"
            st.rerun()
    with b_cfg:
        if st.button("ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã‚Â¡ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â", key="hdr_cfg", type="primary" if st.session_state.cat_ativa == "ConfiguraÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes" else "secondary", width="stretch", help="ConfiguraÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes"):
            st.session_state.cat_ativa = "ConfiguraÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes"
            st.rerun()
    with b_prof:
        with st.popover("ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“Ãƒâ€šÃ‚Â¤", width="stretch"):
            st.markdown(f"**{user['nome']}**")
            st.caption(f"Identificador: `@{usuario_id}`")
            st.caption(f"NÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âºmero OMNIX: `#{user.get('numero', '0000')}`")
            st.caption(f"PermissÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes: `{user['cargo'].upper()}`")
            st.divider()
            if st.button("ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“Ãƒâ€šÃ‚Â¤ Abrir Meu Perfil", key="pop_my_prof", width="stretch"):
                st.session_state["perfil_visitado_rapido"] = usuario_id
                st.session_state["radio_sub_social"] = "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“Ãƒâ€šÃ‚Â¤ Perfil & Membros"
                st.session_state.cat_ativa = "Social"
                st.rerun()
            if user["cargo"] == "admin":
                if st.button("ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂºÃƒâ€šÃ‚Â¡ÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â AdministraÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o", key="pop_admin", width="stretch"):
                    st.session_state.cat_ativa = "AdministraÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o"
                    st.rerun()
            if st.button("ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€¦Ã‚Â¡Ãƒâ€šÃ‚Âª Encerrar SessÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o", key="pop_logout", width="stretch"):
                cookies.remove("omnix_user")
                st.query_params.clear()
                st.session_state.logado = False
                st.session_state.usuario_id = None
                time.sleep(0.25)
                st.rerun()

categorias = [
    ("ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€šÃ‚ÂÃƒâ€šÃ‚Â  InÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­cio", "InÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­cio"), ("ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢Ãƒâ€šÃ‚Â¬ Chat", "Chat"),
    (f"ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“Ãƒâ€šÃ‚Â¥ Social ({qtd_ped})" if qtd_ped > 0 else "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“Ãƒâ€šÃ‚Â¥ Social", "Social"),
    ("ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€¦Ã‚Â½Ãƒâ€šÃ‚Â¬ MÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­dia", "MultimÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­dia"),
    ("ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒâ€šÃ‚Â Arquivos", "Arquivos"),
    ("ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“Ãƒâ€šÃ‚Â¨ IA", "InteligÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªncia Artificial")
]

nav_cols = st.columns(len(categorias))
for idx, (label, nome_cat) in enumerate(categorias):
    ativo = (st.session_state.cat_ativa == nome_cat)
    if nav_cols[idx].button(label, key=f"main_nav_{nome_cat}", type="primary" if ativo else "secondary", width="stretch"):
        st.session_state.cat_ativa = nome_cat
        st.rerun()

st.markdown("<hr style='margin:6px 0 14px 0; border:none; border-top:1px solid rgba(148,163,184,0.12);'>", unsafe_allow_html=True)

cat = st.session_state.cat_ativa

if cat == "InÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­cio":
    render_navegar(usuario_id, user, STORAGE_DIR)

elif cat == "Chat":
    render_messages(usuario_id, user)

elif cat == "Social":
    sub_soc = st.radio(
        "NavegaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o Social:",
        ["ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€¦Ã¢â‚¬â„¢Ãƒâ€šÃ‚Â Navegar", "ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â Postar", "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“Ãƒâ€šÃ‚Â¤ Perfil & Membros"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_social"
    )
    if sub_soc == "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€¦Ã¢â‚¬â„¢Ãƒâ€šÃ‚Â Navegar":
        render_navegar(usuario_id, user, STORAGE_DIR)
    elif sub_soc == "ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â Postar":
        render_criar_post(usuario_id, user)
    elif sub_soc == "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“Ãƒâ€šÃ‚Â¤ Perfil & Membros":
        render_perfil_avatar(usuario_id, user)
    elif sub_soc == "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢Ãƒâ€šÃ‚Â¬ Mensagens & Salas":
        render_messages(usuario_id, user)

elif cat == "MultimÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­dia":
    sub_mid = st.radio(
        "NavegaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o MultimÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­dia:",
        ["ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒâ€šÃ‚Â¥ Central de MÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­dia", "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€šÃ‚ÂÃƒâ€šÃ‚Â¿ Assistir Juntos"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_midia"
    )
    if sub_mid == "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒâ€šÃ‚Â¥ Central de MÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â­dia":
        render_media(STORAGE_DIR)
    else:
        render_watch_party(usuario_id, user, STORAGE_DIR)

elif cat == "Arquivos":
    sub_arq = st.radio(
        "NavegaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o Arquivos:",
        ["ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ OMNIX Drive", "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â€šÂ¬Ã…Â¾ Conversor Universal"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_arquivos"
    )
    if sub_arq == "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã…â€œÃƒÂ¢Ã¢â€šÂ¬Ã…Â¡ OMNIX Drive":
        render_files(STORAGE_DIR, user["cargo"])
    else:
        render_converter(STORAGE_DIR)

elif cat == "InteligÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âªncia Artificial":
    sub_ia = st.radio(
        "NavegaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o IA:",
        ["ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€šÃ‚Â¤ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ OMNIX IA", "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‹Å“Ãƒâ€šÃ‚ÂÃƒÆ’Ã‚Â¯Ãƒâ€šÃ‚Â¸Ãƒâ€šÃ‚Â OMNIX Vision IA"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_ia"
    )
    if sub_ia == "ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€šÃ‚Â¤ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Å“ OMNIX IA":
        render_bot_hub(usuario_id, user)
    else:
        render_vision(user["cargo"])

elif cat == "NotificaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes":
    c1, c2 = st.columns([3.5, 1.5])
    c1.subheader("ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‚ÂÃƒÂ¢Ã¢â€šÂ¬Ã‚Â NotificaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes")
    if nao_lidas > 0 and c2.button("ÃƒÆ’Ã‚Â¢Ãƒâ€¦Ã¢â‚¬Å“ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¦ Marcar todas como lidas", type="primary", width="stretch"):
        marcar_todas_como_lidas(usuario_id)
        st.rerun()
    if not notificacoes:
        st.info("Nenhuma notificaÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o recente no momento.")
    else:
        for n in notificacoes:
            nova = usuario_id not in n.get("lido_por", [])
            with st.container(border=True):
                st.markdown(f"{'ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸Ãƒâ€¦Ã‚Â¸Ãƒâ€šÃ‚Â£ ' if nova else ''}**{n['tipo']}** ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â¢ **{n['autor_nome']}** {n['descricao']}")
                st.caption(f"ÃƒÆ’Ã‚Â°Ãƒâ€¦Ã‚Â¸ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢ {n['hora']}")

elif cat == "ConfiguraÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Âµes":
    render_configuracoes(usuario_id)

elif cat == "AdministraÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â§ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â£o":
    if user["cargo"] == "admin":
        render_admin(STORAGE_DIR, usuario_id)
    else:
        st.error("Acesso restrito aos administradores autorizados.")














