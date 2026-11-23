import streamlit as st
import json
from pathlib import Path
from modules.admin import (
    carregar_usuarios,
    atualizar_configuracoes_usuario,
    alterar_senha_usuario
)

CHAT_GRUPO_FILE = Path("mensagens.json")
CHAT_DM_FILE = Path("mensagens_dm.json")
FRIENDS_FILE = Path("amizades.json")

def ja_conversou_com(user_a: str, user_b: str) -> bool:
    a, b = user_a.strip().lower(), user_b.strip().lower()
    if a == b:
        return True

    # 1. Verifica se são amigos
    if FRIENDS_FILE.exists():
        try:
            amz = json.loads(FRIENDS_FILE.read_text(encoding="utf-8"))
            if b in amz.get("amigos", {}).get(a, []):
                return True
        except Exception:
            pass

    # 2. Verifica se já trocaram mensagens no Chat Direto (DM)
    if CHAT_DM_FILE.exists():
        try:
            dms = json.loads(CHAT_DM_FILE.read_text(encoding="utf-8"))
            pares = sorted([a, b])
            chave = f"{pares}__{pares}"
            if len(dms.get(chave, [])) > 0:
                return True
        except Exception:
            pass

    # 3. Verifica se ambos já participaram do Chat do Grupo
    if CHAT_GRUPO_FILE.exists():
        try:
            grp = json.loads(CHAT_GRUPO_FILE.read_text(encoding="utf-8"))
            autores = {str(m.get("id", "")).strip().lower() for m in grp}
            if a in autores and b in autores:
                return True
        except Exception:
            pass

    return False

def pode_ver_perfil(visitante_id: str, visitante_cargo: str, alvo_id: str) -> bool:
    v_id = visitante_id.strip().lower()
    a_id = alvo_id.strip().lower()
    
    # Admin ou próprio dono sempre podem ver
    if visitante_cargo == "admin" or v_id == a_id:
        return True
        
    usuarios = carregar_usuarios()
    alvo = usuarios.get(a_id, {})
    configs = alvo.get("configs", {})
    
    # Se o usuário deixou o perfil público nas configurações
    if configs.get("perfil_publico", False):
        return True
        
    # Caso contrário, exige amizade ou interação prévia no chat
    return ja_conversou_com(v_id, a_id)

def render_configuracoes(usuario_id: str):
    st.header("⚙️ Configurações da Conta")
    usuarios = carregar_usuarios()
    user = usuarios.get(usuario_id, {})
    configs = user.get("configs", {})

    tab_priv, tab_notif, tab_seg = st.tabs([
        "🔒 Privacidade",
        "🔔 Notificações",
        "🛡️ Segurança & Senha"
    ])

    # ==========================================
    # ABA 1: PRIVACIDADE
    # ==========================================
    with tab_priv:
        st.subheader("Controle de Visibilidade")
        with st.container(border=True):
            p_publico = st.toggle(
                "🌐 Perfil Público (Permitir que membros que nunca falaram comigo vejam meu perfil)",
                value=configs.get("perfil_publico", False)
            )
            st.caption("Quando desativado, apenas Administradores, Amigos ou pessoas com quem você já conversou no chat podem ver seu perfil completo.")
            
            st.divider()
            p_numero = st.toggle(
                "📞 Exibir meu Número OMNIX no meu perfil",
                value=configs.get("mostrar_numero", True)
            )
            
            st.divider()
            p_pedidos = st.toggle(
                "🤝 Permitir receber pedidos de amizade",
                value=configs.get("aceitar_pedidos_amizade", True)
            )

            if st.button("💾 Salvar Privacidade", type="primary"):
                configs["perfil_publico"] = p_publico
                configs["mostrar_numero"] = p_numero
                configs["aceitar_pedidos_amizade"] = p_pedidos
                atualizar_configuracoes_usuario(usuario_id, configs)
                st.success("Configurações de privacidade salvas!")
                st.rerun()

    # ==========================================
    # ABA 2: NOTIFICAÇÕES
    # ==========================================
    with tab_notif:
        st.subheader("Alertas no Sininho 🔔")
        with st.container(border=True):
            n_dm = st.toggle("🔒 Mensagens Diretas (DM)", value=configs.get("notif_dm", True))
            n_grp = st.toggle("🌐 Mensagens no Chat do Grupo", value=configs.get("notif_grupo", True))
            n_post = st.toggle("✨ Novas Publicações e Status", value=configs.get("notif_posts", True))
            n_amz = st.toggle("🤝 Novos Pedidos de Amizade", value=configs.get("notif_amizade", True))

            if st.button("💾 Salvar Preferências de Notificação", type="primary"):
                configs["notif_dm"] = n_dm
                configs["notif_grupo"] = n_grp
                configs["notif_posts"] = n_post
                configs["notif_amizade"] = n_amz
                atualizar_configuracoes_usuario(usuario_id, configs)
                st.success("Preferências de notificação atualizadas!")
                st.rerun()

    # ==========================================
    # ABA 3: SEGURANÇA & SENHA
    # ==========================================
    with tab_seg:
        st.subheader("Alterar Senha de Acesso")
        with st.form("form_trocar_senha", clear_on_submit=True):
            s_atual = st.text_input("Senha atual:", type="password")
            s_nova = st.text_input("Nova senha:", type="password")
            s_conf = st.text_input("Confirme a nova senha:", type="password")
            
            if st.form_submit_button("🔑 Atualizar Senha", type="primary"):
                if not s_atual or not s_nova:
                    st.warning("Preencha todos os campos.")
                elif s_nova != s_conf:
                    st.error("A nova senha e a confirmação não coincidem.")
                else:
                    ok, msg = alterar_senha_usuario(usuario_id, s_atual, s_nova)
                    if ok:
                        st.success(msg)
                    else:
                        st.error(msg)
