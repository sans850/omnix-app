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
""", height=0, width=0).exists() else "⚡",
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
    st.session_state.cat_ativa = "Início"

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
                "<div style='color:#94A3B8; font-size:0.86rem; margin-top:4px;'>Plataforma Integrada • Minimalista & Privada</div>"
                "</div>",
                unsafe_allow_html=True
            )
            t_in, t_reg = st.tabs(["🔑 Entrar", "📝 Criar Conta"])
            with t_in:
                u_in = st.text_input("Usuário", key="l_u").strip().lower()
                p_in = st.text_input("Senha", type="password", key="l_p")
                lembrar = st.checkbox("Manter sessão ativa", value=True)
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
                        st.error("Credenciais inválidas.")
            with t_reg:
                with st.form("f_reg_clean", clear_on_submit=True):
                    r_nome = st.text_input("Nome de Exibição").strip()
                    r_user = st.text_input("Login (sem espaços)").strip().lower()
                    r_num = st.text_input("Número OMNIX (3 a 10 dígitos)").strip()
                    r_pass = st.text_input("Senha", type="password")
                    r_pass2 = st.text_input("Confirmar Senha", type="password")
                    if st.form_submit_button("Concluir Cadastro", type="primary", width="stretch"):
                        if not r_nome or not r_user or not r_pass or not r_num:
                            st.warning("Preencha todos os campos.")
                        elif " " in r_user or not r_num.isdigit() or len(r_num) < 3:
                            st.warning("Verifique o formato do login e do número.")
                        elif r_user in USUARIOS or numero_ja_existe(r_num):
                            st.error("Login ou Número OMNIX já cadastrado.")
                        elif r_pass != r_pass2:
                            st.error("As senhas não coincidem.")
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

# Cabeçalho Compacto: Identidade + Nome à esquerda; Apenas ícones à direita
h_left, h_right = st.columns([4.2, 1.8])
with h_left:
    if Path("omnix_icon.png").exists():
        c_ico, c_brand, c_user_info = st.columns([0.45, 1.15, 3.4])
        c_ico.image("omnix_icon.png", width=34)
        c_brand.markdown("<div class='omnix-logo' style='padding-top:3px;'>OMNIX</div>", unsafe_allow_html=True)
    else:
        c_brand, c_user_info = st.columns([1.2, 3.8])
        c_brand.markdown("<div class='omnix-logo'>⚡ OMNIX</div>", unsafe_allow_html=True)
    c_user_info.markdown(
        f"<div style='padding-top:5px; color:#E2E8F0; font-size:0.92rem;'>"
        f"Olá, <b>{user['nome']}</b> <span style='color:#64748B;'>• Conectado</span></div>",
        unsafe_allow_html=True
    )

with h_right:
    b_notif, b_cfg, b_prof = st.columns(3)
    with b_notif:
        lbl_n = f"🔔 {nao_lidas}" if nao_lidas > 0 else "🔔"
        if st.button(lbl_n, key="hdr_notif", type="primary" if st.session_state.cat_ativa == "Notificações" else "secondary", width="stretch", help="Notificações"):
            st.session_state.cat_ativa = "Notificações"
            st.rerun()
    with b_cfg:
        if st.button("⚙️", key="hdr_cfg", type="primary" if st.session_state.cat_ativa == "Configurações" else "secondary", width="stretch", help="Configurações"):
            st.session_state.cat_ativa = "Configurações"
            st.rerun()
    with b_prof:
        with st.popover("👤", width="stretch"):
            st.markdown(f"**{user['nome']}**")
            st.caption(f"Identificador: `@{usuario_id}`")
            st.caption(f"Número OMNIX: `#{user.get('numero', '0000')}`")
            st.caption(f"Permissões: `{user['cargo'].upper()}`")
            st.divider()
            if st.button("👤 Abrir Meu Perfil", key="pop_my_prof", width="stretch"):
                st.session_state["perfil_visitado_rapido"] = usuario_id
                st.session_state["radio_sub_social"] = "👤 Perfil & Membros"
                st.session_state.cat_ativa = "Social"
                st.rerun()
            if user["cargo"] == "admin":
                if st.button("🛡️ Administração", key="pop_admin", width="stretch"):
                    st.session_state.cat_ativa = "Administração"
                    st.rerun()
            if st.button("🚪 Encerrar Sessão", key="pop_logout", width="stretch"):
                cookies.remove("omnix_user")
                st.query_params.clear()
                st.session_state.logado = False
                st.session_state.usuario_id = None
                time.sleep(0.25)
                st.rerun()

categorias = [
    ("🏠 Início", "Início"), ("💬 Chat", "Chat"),
    (f"👥 Social ({qtd_ped})" if qtd_ped > 0 else "👥 Social", "Social"),
    ("🎬 Mídia", "Multimídia"),
    ("📁 Arquivos", "Arquivos"),
    ("✨ IA", "Inteligência Artificial")
]

nav_cols = st.columns(len(categorias))
for idx, (label, nome_cat) in enumerate(categorias):
    ativo = (st.session_state.cat_ativa == nome_cat)
    if nav_cols[idx].button(label, key=f"main_nav_{nome_cat}", type="primary" if ativo else "secondary", width="stretch"):
        st.session_state.cat_ativa = nome_cat
        st.rerun()

st.markdown("<hr style='margin:6px 0 14px 0; border:none; border-top:1px solid rgba(148,163,184,0.12);'>", unsafe_allow_html=True)

cat = st.session_state.cat_ativa

if cat == "Início":
    render_navegar(usuario_id, user, STORAGE_DIR)

elif cat == "Chat":
    render_messages(usuario_id, user)

elif cat == "Social":
    sub_soc = st.radio(
        "Navegação Social:",
        ["🌐 Navegar", "✍️ Postar", "👤 Perfil & Membros"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_social"
    )
    if sub_soc == "🌐 Navegar":
        render_navegar(usuario_id, user, STORAGE_DIR)
    elif sub_soc == "✍️ Postar":
        render_criar_post(usuario_id, user)
    elif sub_soc == "👤 Perfil & Membros":
        render_perfil_avatar(usuario_id, user)
    elif sub_soc == "💬 Mensagens & Salas":
        render_messages(usuario_id, user)

elif cat == "Multimídia":
    sub_mid = st.radio(
        "Navegação Multimídia:",
        ["📥 Central de Mídia", "🍿 Assistir Juntos"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_midia"
    )
    if sub_mid == "📥 Central de Mídia":
        render_media(STORAGE_DIR)
    else:
        render_watch_party(usuario_id, user, STORAGE_DIR)

elif cat == "Arquivos":
    sub_arq = st.radio(
        "Navegação Arquivos:",
        ["📂 OMNIX Drive", "🔄 Conversor Universal"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_arquivos"
    )
    if sub_arq == "📂 OMNIX Drive":
        render_files(STORAGE_DIR, user["cargo"])
    else:
        render_converter(STORAGE_DIR)

elif cat == "Inteligência Artificial":
    sub_ia = st.radio(
        "Navegação IA:",
        ["🤖 OMNIX IA", "👁️ OMNIX Vision IA"],
        horizontal=True,
        label_visibility="collapsed",
        key="radio_sub_ia"
    )
    if sub_ia == "🤖 OMNIX IA":
        render_bot_hub(usuario_id, user)
    else:
        render_vision(user["cargo"])

elif cat == "Notificações":
    c1, c2 = st.columns([3.5, 1.5])
    c1.subheader("🔔 Notificações")
    if nao_lidas > 0 and c2.button("✅ Marcar todas como lidas", type="primary", width="stretch"):
        marcar_todas_como_lidas(usuario_id)
        st.rerun()
    if not notificacoes:
        st.info("Nenhuma notificação recente no momento.")
    else:
        for n in notificacoes:
            nova = usuario_id not in n.get("lido_por", [])
            with st.container(border=True):
                st.markdown(f"{'🟣 ' if nova else ''}**{n['tipo']}** • **{n['autor_nome']}** {n['descricao']}")
                st.caption(f"🕒 {n['hora']}")

elif cat == "Configurações":
    render_configuracoes(usuario_id)

elif cat == "Administração":
    if user["cargo"] == "admin":
        render_admin(STORAGE_DIR, usuario_id)
    else:
        st.error("Acesso restrito aos administradores autorizados.")














