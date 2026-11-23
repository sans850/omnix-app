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
""", height=0, width=0).exists() else "âš¡",
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
    st.session_state.cat_ativa = "InÃ­cio"

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
                "<div style='color:#94A3B8; font-size:0.86rem; margin-top:4px;'>Plataforma Integrada â€¢ Minimalista & Privada</div>"
                "</div>",
                unsafe_allow_html=True
            )
            t_in, t_reg = st.tabs(["ðŸ”‘ Entrar", "ðŸ“ Criar Conta"])
            with t_in:
                u_in = st.text_input("UsuÃ¡rio", key="l_u").strip().lower()
                p_in = st.text_input("Senha", type="password", key="l_p")
                lembrar = st.checkbox("Manter sessÃ£o ativa", value=True)
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
                        st.error("Credenciais invÃ¡lidas.")
            with t_reg:
                with st.form("f_reg_clean", clear_on_submit=True):
                    r_nome = st.text_input("Nome de ExibiÃ§Ã£o").strip()
                    r_user = st.text_input("Login (sem espaÃ§os)").strip().lower()
                    r_num = st.text_input("NÃºmero OMNIX (3 a 10 dÃ­gitos)").strip()
                    r_pass = st.text_input("Senha", type="password")
                    r_pass2 = st.text_input("Confirmar Senha", type="password")
                    if st.form_submit_button("Concluir Cadastro", type="primary", width="stretch"):
                        if not r_nome or not r_user or not r_pass or not r_num:
                            st.warning("Preencha todos os campos.")
                        elif " " in r_user or not r_num.isdigit() or len(r_num) < 3:
                            st.warning("Verifique o formato do login e do nÃºmero.")
                        elif r_user in USUARIOS or numero_ja_existe(r_num):
                            st.error("Login ou NÃºmero OMNIX jÃ¡ cadastrado.")
                        elif r_pass != r_pass2:
                            st.error("As senhas nÃ£o coincidem.")
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

# CabeÃ§alho Compacto: Identidade + Nome Ã  esquerda; Apenas Ã­cones Ã  direita
h_left, h_right = st.columns([4.2, 1.8])
with h_left:
    if Path("omnix_icon.png").exists():
        c_ico, c_brand, c_user_info = st.columns([0.45, 1.15, 3.4])
        c_ico.image("omnix_icon.png", width=34)
        c_brand.markdown("<div class='omnix-logo' style='padding-top:3px;'>OMNIX</div>", unsafe_allow_html=True)
    else:
        c_brand, c_user_info = st.columns([1.2, 3.8])
        c_brand.markdown("<div class='omnix-logo'>âš¡ OMNIX</div>", unsafe_allow_html=True)
    c_user_info.markdown(
        f"<div style='padding-top:5px; color:#E2E8F0; font-size:0.92rem;'>"
        f"OlÃ¡, <b>{user['nome']}</b> <span style='color:#64748B;'>â€¢ Conectado</span></div>",
        unsafe_allow_html=True
    )

with h_right:
    b_notif, b_cfg, b_prof = st.columns(3)
    with b_notif:
        lbl_n = f"ðŸ”” {nao_lidas}" if nao_lidas > 0 else "ðŸ””"
        if st.button(lbl_n, key="hdr_notif", type="primary" if st.session_state.cat_ativa == "NotificaÃ§Ãµes" else "secondary", width="stretch", help="NotificaÃ§Ãµes"):
            st.session_state.cat_ativa = "NotificaÃ§Ãµes"
            st.rerun()
    with b_cfg:
        if st.button("âš™ï¸", key="hdr_cfg", type="primary" if st.session_state.cat_ativa == "ConfiguraÃ§Ãµes" else "secondary", width="stretch", help="ConfiguraÃ§Ãµes"):
            st.session_state.cat_ativa = "ConfiguraÃ§Ãµes"
            st.rerun()
    with b_prof:
        with st.popover("ðŸ‘¤", width="stretch"):
            st.markdown(f"**{user['nome']}**")
            st.caption(f"Identificador: `@{usuario_id}`")
            st.caption(f"NÃºmero OMNIX: `#{user.get('numero', '0000')}`")
            st.caption(f"PermissÃµes: `{user['cargo'].upper()}`")
            st.divider()
            if st.button("ðŸ‘¤ Abrir Meu Perfil", key="pop_my_prof", width="stretch"):
                st.session_state["perfil_visitado_rapido"] = usuario_id
                st.session_state["radio_sub_social"] = "ðŸ‘¤ Perfil & Membros"
                st.session_state.cat_ativa = "Social"
                st.rerun()
            if user["cargo"] == "admin":
                if st.button("ðŸ›¡ï¸ AdministraÃ§Ã£o", key="pop_admin", width="stretch"):
                    st.session_state.cat_ativa = "AdministraÃ§Ã£o"
                    st.rerun()
            if st.button("ðŸšª Encerrar SessÃ£o", key="pop_logout", width="stretch"):
                cookies.remove("omnix_user")
                st.query_params.clear()
                st.session_state.logado = False
                st.session_state.usuario_id = None
                time.sleep(0.25)
                st.rerun()

categorias = [
    ("ðŸ  InÃ­cio", "InÃ­cio"), ("ðŸ’¬ Chat", "Chat"),
    (f"ðŸ‘¥ Social ({qtd_ped})" if qtd_ped > 0 else "ðŸ‘¥ Social", "Social"),
    ("ðŸŽ¬ MÃ­dia", "MultimÃ­dia"),
    ("ðŸ“ Arquivos", "Arquivos"),
    ("âœ¨ IA", "InteligÃªncia Artificial")
]

nav_cols = st.columns(len(categorias))
for idx, (label, nome_cat) in enumerate(categorias):
    ativo = (st.session_state.cat_ativa == nome_cat)
    if nav_cols[idx].button(label, key=f"main_nav_{nome_cat}", type="primary" if ativo else "secondary", width="stretch"):
        st.session_state.cat_ativa = nome_cat
        st.rerun()

st.markdown("<hr style='margin:6px 0 14px 0; border:none; border-top:1px solid rgba(148,163,184,0.12);'>", unsafe_allow_html=True)

cat = st.session_state.cat_ativa

if cat == "InÃ­cio":
    render_navegar(usuario_id, user, STORAGE_DIR)

elif cat == "Chat":
    render_messages(usuario_id, user)

elif cat == "Social":
    sub_soc = st.radio(
        "NavegaÃ§Ã£o Social:",
        ["ðŸŒ Navegar", "âœï¸ Postar", "ðŸ‘¤ Perfil & Membros"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_social"
    )
    if sub_soc == "ðŸŒ Navegar":
        render_navegar(usuario_id, user, STORAGE_DIR)
    elif sub_soc == "âœï¸ Postar":
        render_criar_post(usuario_id, user)
    elif sub_soc == "ðŸ‘¤ Perfil & Membros":
        render_perfil_avatar(usuario_id, user)
    elif sub_soc == "ðŸ’¬ Mensagens & Salas":
        render_messages(usuario_id, user)

elif cat == "MultimÃ­dia":
    sub_mid = st.radio(
        "NavegaÃ§Ã£o MultimÃ­dia:",
        ["ðŸ“¥ Central de MÃ­dia", "ðŸ¿ Assistir Juntos"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_midia"
    )
    if sub_mid == "ðŸ“¥ Central de MÃ­dia":
        render_media(STORAGE_DIR)
    else:
        render_watch_party(usuario_id, user, STORAGE_DIR)

elif cat == "Arquivos":
    sub_arq = st.radio(
        "NavegaÃ§Ã£o Arquivos:",
        ["ðŸ“‚ OMNIX Drive", "ðŸ”„ Conversor Universal"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_arquivos"
    )
    if sub_arq == "ðŸ“‚ OMNIX Drive":
        render_files(STORAGE_DIR, user["cargo"])
    else:
        render_converter(STORAGE_DIR)

elif cat == "InteligÃªncia Artificial":
    sub_ia = st.radio(
        "NavegaÃ§Ã£o IA:",
        ["ðŸ¤– OMNIX IA", "ðŸ‘ï¸ OMNIX Vision IA"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_ia"
    )
    if sub_ia == "ðŸ¤– OMNIX IA":
        render_bot_hub(usuario_id, user)
    else:
        render_vision(user["cargo"])

elif cat == "NotificaÃ§Ãµes":
    c1, c2 = st.columns([3.5, 1.5])
    c1.subheader("ðŸ”” NotificaÃ§Ãµes")
    if nao_lidas > 0 and c2.button("âœ… Marcar todas como lidas", type="primary", width="stretch"):
        marcar_todas_como_lidas(usuario_id)
        st.rerun()
    if not notificacoes:
        st.info("Nenhuma notificaÃ§Ã£o recente no momento.")
    else:
        for n in notificacoes:
            nova = usuario_id not in n.get("lido_por", [])
            with st.container(border=True):
                st.markdown(f"{'ðŸŸ£ ' if nova else ''}**{n['tipo']}** â€¢ **{n['autor_nome']}** {n['descricao']}")
                st.caption(f"ðŸ•’ {n['hora']}")

elif cat == "ConfiguraÃ§Ãµes":
    render_configuracoes(usuario_id)

elif cat == "AdministraÃ§Ã£o":
    if user["cargo"] == "admin":
        render_admin(STORAGE_DIR, usuario_id)
    else:
        st.error("Acesso restrito aos administradores autorizados.")














