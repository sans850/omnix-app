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
from modules.vision import render_vision
from modules.bot_voice import render_bot_hub
from modules.settings import render_configuracoes
from modules.optimizer import executar_faxina_automatica
from modules.friends import listar_pedidos_recebidos

st.set_page_config(
    page_title="OMNIX",
    page_icon="omnix_icon.png" if Path("omnix_icon.png")
import json as _json_st
from pathlib import Path as _Path_st
_st_file = _Path_st("omnix_online_status.json")
if _st_file.exists():
    try:
        _st_data = _json_st.loads(_st_file.read_text(encoding="utf-8"))
        if not _st_data.get("online", True):
            st.markdown("""
            <div style="text-align:center; padding:80px 20px; font-family:sans-serif;">
                <h1 style="color:#A855F7; margin-bottom:8px;">OMNIX Offline</h1>
                <p style="color:#94A3B8; font-size:16px;">O servidor online está temporariamente desativado pelo administrador.</p>
                <p style="color:#64748B; font-size:13px;">Tente novamente mais tarde quando o painel for iniciado.</p>
            </div>
            """, unsafe_allow_html=True)
            st.stop()
    except Exception:
        pass
st.markdown('''<style>
[data-testid="stAppViewContainer"], .main, .block-container {
    visibility: visible !important;
    opacity: 1 !important;
    display: block !important;
}
</style>''', unsafe_allow_html=True)
_stc.html("""
<script>
(function() {
  const p = window.parent.document;
  p.documentElement.setAttribute('translate', 'no');
  p.documentElement.classList.add('notranslate');
  const origRemove = window.parent.Node.prototype.removeChild;
  window.parent.Node.prototype.removeChild = function(child) {
    if (child && child.parentNode !== this) { return child; }
    return origRemove.apply(this, arguments);
  };
})();
</script>
""", height=0, width=0).exists() else "Ã¢Å¡Â¡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

ativar_lightbox_global()

st.html("""
<meta name="google" content="notranslate"><script>document.documentElement.setAttribute("translate", "no");</script><style>
    header[data-testid='stHeader'], [data-testid='stSkillsNudgeAnchor'] { display: none !important; }
    [data-testid='StyledFullScreenButton'] { display: none !important; }
        button[title="View fullscreen"],
    [data-testid="StyledFullScreenButton"],
    [data-testid="stFullScreenButton"],
    [data-testid="stElementToolbar"] {
        display: none !important;
    }
        [data-testid='stImage'] img { cursor: zoom-in !important; border-radius: 10px; }
    .block-container {
        max-width: 1120px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }
    .omnix-logo {
        background: linear-gradient(135deg, #A855F7 0%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 900;
        font-size: 1.45rem;
        letter-spacing: 1.2px;
        line-height: 1.1;
    }
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 14px;
        border: 1px solid rgba(148, 163, 184, 0.13);
        background-color: #0F1623;
    }
    div.stButton > button {
        min-height: 38px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.88rem;
        transition: all 0.15s ease;
    }
    div.stButton > button[kind="primary"] {
        background-color: #7C3AED !important;
        border-color: #7C3AED !important;
        color: #FFFFFF !important;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #6D28D9 !important;
        border-color: #6D28D9 !important;
    }
    input, select, textarea {
        font-size: 15px !important;
        border-radius: 10px !important;
    }
    @media (max-width: 768px) {
        header[data-testid='stHeader'], [data-testid='stSkillsNudgeAnchor'] { display: none !important; }
    [data-testid='StyledFullScreenButton'] { display: none !important; }
        button[title="View fullscreen"],
    [data-testid="StyledFullScreenButton"],
    [data-testid="stFullScreenButton"],
    [data-testid="stElementToolbar"] {
        display: none !important;
    }
        [data-testid='stImage'] img { cursor: zoom-in !important; border-radius: 10px; }
    .block-container {
            padding-top: 2.1rem;
            padding-left: 0.6rem;
            padding-right: 0.6rem;
        }
    }
</style>
""")

STORAGE_DIR = Path("omnix_storage")
STORAGE_DIR.mkdir(exist_ok=True)
executar_faxina_automatica(STORAGE_DIR)

USUARIOS = carregar_usuarios()
cookies = CookieController()

def gerar_token_sessao(uid: str, senha: str) -> str:
    return hashlib.sha256(f"{uid}:{senha}:omnix_secret".encode()).hexdigest()[:16]

if "logado" not in st.session_state:
    st.session_state.logado = False
    st.session_state.usuario_id = None

if "cat_ativa" not in st.session_state:
    st.session_state.cat_ativa = "InÃƒÂ­cio"

qp_user = st.query_params.get("u", "")
qp_token = st.query_params.get("t", "")

if not st.session_state.logado and qp_user in USUARIOS:
    if qp_token == gerar_token_sessao(qp_user, USUARIOS[qp_user]["senha"]):
        st.session_state.logado = True
        st.session_state.usuario_id = qp_user

if not st.session_state.logado:
    usuario_salvo = cookies.get("omnix_user")
    if usuario_salvo in USUARIOS:
        st.session_state.logado = True
        st.session_state.usuario_id = usuario_salvo

if not st.session_state.logado or st.session_state.usuario_id not in USUARIOS:
    st.write("")
    c1, c2, c3 = st.columns([1, 1.3, 1])
    with c2:
        with st.container(border=True):
            if Path("omnix_icon.png").exists():
                _, cl_img, _ = st.columns([1.4, 1.2, 1.4])
                cl_img.image("omnix_icon.png", width="stretch")
            st.markdown(
                "<div style='text-align:center; padding:4px 0 10px 0;'>"
                "<div class='omnix-logo'>OMNIX</div>"
                "<div style='color:#94A3B8; font-size:0.86rem; margin-top:4px;'>Plataforma Integrada Ã¢â‚¬Â¢ Minimalista & Privada</div>"
                "</div>",
                unsafe_allow_html=True
            )
            t_in, t_reg = st.tabs(["Ã°Å¸â€â€˜ Entrar", "Ã°Å¸â€œÂ Criar Conta"])
            with t_in:
                u_in = st.text_input("UsuÃƒÂ¡rio", key="l_u").strip().lower()
                p_in = st.text_input("Senha", type="password", key="l_p")
                lembrar = st.checkbox("Manter sessÃƒÂ£o ativa", value=True)
                if st.button("Acessar OMNIX", type="primary", width="stretch"):
                    if u_in in USUARIOS and USUARIOS[u_in]["senha"] == p_in:
                        st.session_state.logado = True
                        st.session_state.usuario_id = u_in
                        if lembrar:
                            cookies.set("omnix_user", u_in, max_age=30 * 24 * 60 * 60)
                            st.query_params["u"] = u_in
                            st.query_params["t"] = gerar_token_sessao(u_in, p_in)
                            time.sleep(0.25)
                        st.rerun()
                    else:
                        st.error("Credenciais invÃƒÂ¡lidas.")
            with t_reg:
                with st.form("f_reg_clean", clear_on_submit=True):
                    r_nome = st.text_input("Nome de ExibiÃƒÂ§ÃƒÂ£o").strip()
                    r_user = st.text_input("Login (sem espaÃƒÂ§os)").strip().lower()
                    r_num = st.text_input("NÃƒÂºmero OMNIX (3 a 10 dÃƒÂ­gitos)").strip()
                    r_pass = st.text_input("Senha", type="password")
                    r_pass2 = st.text_input("Confirmar Senha", type="password")
                    if st.form_submit_button("Concluir Cadastro", type="primary", width="stretch"):
                        if not r_nome or not r_user or not r_pass or not r_num:
                            st.warning("Preencha todos os campos.")
                        elif " " in r_user or not r_num.isdigit() or len(r_num) < 3:
                            st.warning("Verifique o formato do login e do nÃƒÂºmero.")
                        elif r_user in USUARIOS or numero_ja_existe(r_num):
                            st.error("Login ou NÃƒÂºmero OMNIX jÃƒÂ¡ cadastrado.")
                        elif r_pass != r_pass2:
                            st.error("As senhas nÃƒÂ£o coincidem.")
                        else:
                            USUARIOS[r_user] = {
                                "senha": r_pass, "cargo": "membro", "nome": r_nome,
                                "avatar": "", "banner": "", "bio": "Membro do OMNIX", "numero": r_num
                            }
                            salvar_usuarios(USUARIOS)
                            st.session_state.logado = True
                            st.session_state.usuario_id = r_user
                            cookies.set("omnix_user", r_user, max_age=30 * 24 * 60 * 60)
                            st.query_params["u"] = r_user
                            st.query_params["t"] = gerar_token_sessao(r_user, r_pass)
                            time.sleep(0.3)
                            st.rerun()
    st.stop()

verificar_e_abrir_modal_global()
usuario_id = st.session_state.usuario_id
user = USUARIOS[usuario_id]
if user.get("cargo") == "admin" and st.session_state.get("qa_step_state"):
    from modules.qa_simulator import exibir_popup_diagnostico_admin
    exibir_popup_diagnostico_admin()
notificacoes, nao_lidas = obter_notificacoes_usuario(usuario_id)
qtd_ped = len(listar_pedidos_recebidos(usuario_id))

# CabeÃƒÂ§alho Compacto: Identidade + Nome ÃƒÂ  esquerda; Apenas ÃƒÂ­cones ÃƒÂ  direita
h_left, h_right = st.columns([4.2, 1.8])
with h_left:
    if Path("omnix_icon.png").exists():
        c_ico, c_brand, c_user_info = st.columns([0.45, 1.15, 3.4])
        c_ico.image("omnix_icon.png", width=34)
        c_brand.markdown("<div class='omnix-logo' style='padding-top:3px;'>OMNIX</div>", unsafe_allow_html=True)
    else:
        c_brand, c_user_info = st.columns([1.2, 3.8])
        c_brand.markdown("<div class='omnix-logo'>Ã¢Å¡Â¡ OMNIX</div>", unsafe_allow_html=True)
    c_user_info.markdown(
        f"<div style='padding-top:5px; color:#E2E8F0; font-size:0.92rem;'>"
        f"OlÃƒÂ¡, <b>{user['nome']}</b> <span style='color:#64748B;'>Ã¢â‚¬Â¢ Conectado</span></div>",
        unsafe_allow_html=True
    )

with h_right:
    b_notif, b_cfg, b_prof = st.columns(3)
    with b_notif:
        lbl_n = f"Ã°Å¸â€â€ {nao_lidas}" if nao_lidas > 0 else "Ã°Å¸â€â€"
        if st.button(lbl_n, key="hdr_notif", type="primary" if st.session_state.cat_ativa == "NotificaÃƒÂ§ÃƒÂµes" else "secondary", width="stretch", help="NotificaÃƒÂ§ÃƒÂµes"):
            st.session_state.cat_ativa = "NotificaÃƒÂ§ÃƒÂµes"
            st.rerun()
    with b_cfg:
        if st.button("Ã¢Å¡â„¢Ã¯Â¸Â", key="hdr_cfg", type="primary" if st.session_state.cat_ativa == "ConfiguraÃƒÂ§ÃƒÂµes" else "secondary", width="stretch", help="ConfiguraÃƒÂ§ÃƒÂµes"):
            st.session_state.cat_ativa = "ConfiguraÃƒÂ§ÃƒÂµes"
            st.rerun()
    with b_prof:
        with st.popover("Ã°Å¸â€˜Â¤", width="stretch"):
            st.markdown(f"**{user['nome']}**")
            st.caption(f"Identificador: `@{usuario_id}`")
            st.caption(f"NÃƒÂºmero OMNIX: `#{user.get('numero', '0000')}`")
            st.caption(f"PermissÃƒÂµes: `{user['cargo'].upper()}`")
            st.divider()
            if st.button("Ã°Å¸â€˜Â¤ Abrir Meu Perfil", key="pop_my_prof", width="stretch"):
                st.session_state["perfil_visitado_rapido"] = usuario_id
                st.session_state["radio_sub_social"] = "Ã°Å¸â€˜Â¤ Perfil & Membros"
                st.session_state.cat_ativa = "Social"
                st.rerun()
            if user["cargo"] == "admin":
                if st.button("Ã°Å¸â€ºÂ¡Ã¯Â¸Â AdministraÃƒÂ§ÃƒÂ£o", key="pop_admin", width="stretch"):
                    st.session_state.cat_ativa = "AdministraÃƒÂ§ÃƒÂ£o"
                    st.rerun()
            if st.button("Ã°Å¸Å¡Âª Encerrar SessÃƒÂ£o", key="pop_logout", width="stretch"):
                cookies.remove("omnix_user")
                st.query_params.clear()
                st.session_state.logado = False
                st.session_state.usuario_id = None
                time.sleep(0.25)
                st.rerun()

categorias = [
    ("Ã°Å¸ÂÂ  InÃƒÂ­cio", "InÃƒÂ­cio"), ("Ã°Å¸â€™Â¬ Chat", "Chat"),
    (f"Ã°Å¸â€˜Â¥ Social ({qtd_ped})" if qtd_ped > 0 else "Ã°Å¸â€˜Â¥ Social", "Social"),
    ("Ã°Å¸Å½Â¬ MÃƒÂ­dia", "MultimÃƒÂ­dia"),
    ("Ã°Å¸â€œÂ Arquivos", "Arquivos"),
    ("Ã¢Å“Â¨ IA", "InteligÃƒÂªncia Artificial")
]

nav_cols = st.columns(len(categorias))
for idx, (label, nome_cat) in enumerate(categorias):
    ativo = (st.session_state.cat_ativa == nome_cat)
    if nav_cols[idx].button(label, key=f"main_nav_{nome_cat}", type="primary" if ativo else "secondary", width="stretch"):
        st.session_state.cat_ativa = nome_cat
        st.rerun()

st.markdown("<hr style='margin:6px 0 14px 0; border:none; border-top:1px solid rgba(148,163,184,0.12);'>", unsafe_allow_html=True)

cat = st.session_state.cat_ativa

if cat == "InÃƒÂ­cio":
    render_navegar(usuario_id, user, STORAGE_DIR)

elif cat == "Chat":
    render_messages(usuario_id, user)

elif cat == "Social":
    sub_soc = st.radio(
        "NavegaÃƒÂ§ÃƒÂ£o Social:",
        ["Ã°Å¸Å’Â Navegar", "Ã¢Å“ÂÃ¯Â¸Â Postar", "Ã°Å¸â€˜Â¤ Perfil & Membros"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_social"
    )
    if sub_soc == "Ã°Å¸Å’Â Navegar":
        render_navegar(usuario_id, user, STORAGE_DIR)
    elif sub_soc == "Ã¢Å“ÂÃ¯Â¸Â Postar":
        render_criar_post(usuario_id, user)
    elif sub_soc == "Ã°Å¸â€˜Â¤ Perfil & Membros":
        render_perfil_avatar(usuario_id, user)
    elif sub_soc == "Ã°Å¸â€™Â¬ Mensagens & Salas":
        render_messages(usuario_id, user)

elif cat == "MultimÃƒÂ­dia":
    sub_mid = st.radio(
        "NavegaÃƒÂ§ÃƒÂ£o MultimÃƒÂ­dia:",
        ["Ã°Å¸â€œÂ¥ Central de MÃƒÂ­dia", "Ã°Å¸ÂÂ¿ Assistir Juntos"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_midia"
    )
    if sub_mid == "Ã°Å¸â€œÂ¥ Central de MÃƒÂ­dia":
        render_media(STORAGE_DIR)
    else:
        render_watch_party(usuario_id, user, STORAGE_DIR)

elif cat == "Arquivos":
    sub_arq = st.radio(
        "NavegaÃƒÂ§ÃƒÂ£o Arquivos:",
        ["Ã°Å¸â€œâ€š OMNIX Drive", "Ã°Å¸â€â€ž Conversor Universal"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_arquivos"
    )
    if sub_arq == "Ã°Å¸â€œâ€š OMNIX Drive":
        render_files(STORAGE_DIR, user["cargo"])
    else:
        render_converter(STORAGE_DIR)

elif cat == "InteligÃƒÂªncia Artificial":
    sub_ia = st.radio(
        "NavegaÃƒÂ§ÃƒÂ£o IA:",
        ["Ã°Å¸Â¤â€“ OMNIX IA", "Ã°Å¸â€˜ÂÃ¯Â¸Â OMNIX Vision IA"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_ia"
    )
    if sub_ia == "Ã°Å¸Â¤â€“ OMNIX IA":
        render_bot_hub(usuario_id, user)
    else:
        render_vision(user["cargo"])

elif cat == "NotificaÃƒÂ§ÃƒÂµes":
    c1, c2 = st.columns([3.5, 1.5])
    c1.subheader("Ã°Å¸â€â€ NotificaÃƒÂ§ÃƒÂµes")
    if nao_lidas > 0 and c2.button("Ã¢Å“â€¦ Marcar todas como lidas", type="primary", width="stretch"):
        marcar_todas_como_lidas(usuario_id)
        st.rerun()
    if not notificacoes:
        st.info("Nenhuma notificaÃƒÂ§ÃƒÂ£o recente no momento.")
    else:
        for n in notificacoes:
            nova = usuario_id not in n.get("lido_por", [])
            with st.container(border=True):
                st.markdown(f"{'Ã°Å¸Å¸Â£ ' if nova else ''}**{n['tipo']}** Ã¢â‚¬Â¢ **{n['autor_nome']}** {n['descricao']}")
                st.caption(f"Ã°Å¸â€¢â€™ {n['hora']}")

elif cat == "ConfiguraÃƒÂ§ÃƒÂµes":
    render_configuracoes(usuario_id)

elif cat == "AdministraÃƒÂ§ÃƒÂ£o":
    if user["cargo"] == "admin":
        render_admin(STORAGE_DIR, usuario_id)
    else:
        st.error("Acesso restrito aos administradores autorizados.")














