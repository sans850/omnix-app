import streamlit as st
from modules.image_viewer import exibir_imagem_interativa
import json
import time
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps
import pillow_heif
from modules.admin import (
    carregar_usuarios,
    atualizar_avatar,
    atualizar_banner,
    atualizar_dados_perfil
)
from modules.friends import (
    obter_status_relacao,
    enviar_pedido_amizade,
    aceitar_pedido_amizade,
    recusar_ou_cancelar_pedido,
    remover_amigo,
    listar_amigos,
    listar_pedidos_recebidos
)

pillow_heif.register_heif_opener()

POSTS_FILE = Path("posts.json")
NOTIF_FILE = Path("notificacoes.json")
POSTS_DIR = Path("omnix_posts")
POSTS_DIR.mkdir(exist_ok=True)

def registrar_notificacao(autor_id: str, autor_nome: str, tipo: str, descricao: str):
    notifs = []
    if NOTIF_FILE.exists():
        try:
            notifs = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
        except Exception:
            notifs = []
    notifs.append({
        "id": int(datetime.now().timestamp() * 1000),
        "autor_id": autor_id,
        "autor_nome": autor_nome,
        "tipo": tipo,
        "descricao": descricao,
        "hora": datetime.now().strftime("%d/%m %H:%M"),
        "lido_por": [autor_id]
    })
    NOTIF_FILE.write_text(json.dumps(notifs[-50:], indent=4, ensure_ascii=False), encoding="utf-8")

def obter_notificacoes_usuario(usuario_id: str) -> tuple[list, int]:
    if not NOTIF_FILE.exists():
        return [], 0
    try:
        notifs = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
    except Exception:
        return [], 0
    usuarios_all = carregar_usuarios()
    cfgs = usuarios_all.get(usuario_id, {}).get("configs", {})
    minhas = []
    for n in notifs:
        if n["autor_id"] == usuario_id:
            continue
        t = n.get("tipo", "")
        if "DM" in t and not cfgs.get("notif_dm", True): continue
        if "Grupo" in t and not cfgs.get("notif_grupo", True): continue
        if ("Publicação" in t or "Status" in t) and not cfgs.get("notif_posts", True): continue
        if "Amizade" in t and not cfgs.get("notif_amizade", True): continue
        minhas.append(n)
    minhas.reverse()
    nao_lidas = sum(1 for n in minhas if usuario_id not in n.get("lido_por", []))
    return minhas, nao_lidas

def marcar_todas_como_lidas(usuario_id: str):
    if not NOTIF_FILE.exists():
        return
    try:
        notifs = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
        for n in notifs:
            if usuario_id not in n.get("lido_por", []):
                n.setdefault("lido_por", []).append(usuario_id)
        NOTIF_FILE.write_text(json.dumps(notifs, indent=4, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass

def carregar_posts() -> list:
    if not POSTS_FILE.exists():
        return []
    try:
        posts = json.loads(POSTS_FILE.read_text(encoding="utf-8"))
        posts.sort(key=lambda x: x["timestamp"], reverse=True)
        return posts
    except Exception:
        return []

def salvar_posts(posts: list):
    POSTS_FILE.write_text(json.dumps(posts, indent=4, ensure_ascii=False), encoding="utf-8")

def criar_post_permanente(usuario_id: str, nome: str, texto: str, imagem_file=None, visibilidade: str = "Público"):
    ts = int(datetime.now().timestamp() * 1000)
    caminho_img = ""
    if imagem_file is not None:
        imagem_file.seek(0)
        img = Image.open(imagem_file)
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((1200, 1200))
        caminho_img = str(POSTS_DIR / f"post_{usuario_id}_{ts}.jpg")
        img.save(caminho_img, format="JPEG", quality=88)
        
    posts = carregar_posts()
    posts.append({
        "id": ts,
        "usuario_id": usuario_id,
        "nome": nome,
        "texto": texto,
        "imagem": caminho_img,
        "visibilidade": visibilidade,
        "data": datetime.now().strftime("%d/%m/%Y às %H:%M"),
        "timestamp": ts,
        "curtidas": [],
        "comentarios": []
    })
    salvar_posts(posts)
    resumo = texto[:35] if texto else "uma nova mídia"
    registrar_notificacao(usuario_id, nome, "✨ Publicação", f"publicou: '{resumo}'")

def exibir_lista_posts(posts: list, usuario_id: str, user_info: dict, usuarios: dict, prefixo_key: str):
    if not posts:
        with st.container(border=True):
            st.markdown(
                "<div style='text-align:center; padding:28px 16px;'>"
                "<div style='font-size:2rem; margin-bottom:6px;'>📭</div>"
                "<div style='font-weight:700; font-size:1.05rem; color:#F8FAFC;'>Ainda não há publicações por aqui</div>"
                "<div style='color:#94A3B8; font-size:0.88rem; margin-top:4px;'>Explore as seções ou crie a primeira publicação para movimentar a comunidade.</div>"
                "</div>",
                unsafe_allow_html=True
            )
            _, c_btn, _ = st.columns([1.4, 1.6, 1.4])
            if c_btn.button("✍️ Criar Publicação", key=f"empty_cta_{prefixo_key}", type="primary", width="stretch"):
                st.session_state["cat_ativa"] = "Social"
                st.session_state["radio_sub_social"] = "✍️ Postar"
                st.rerun()
        return

    for post in posts:
        autor = usuarios.get(post["usuario_id"], {})
        avatar_autor = autor.get("avatar", "")
        
        with st.container(border=True):
            c_av, c_meta, c_del = st.columns([0.65, 4.65, 0.7])
            with c_av:
                if avatar_autor and Path(avatar_autor).exists():
                    st.image(avatar_autor, width=44)
                else:
                    st.markdown("<div style='font-size:1.6rem; text-align:center;'>👤</div>", unsafe_allow_html=True)
            with c_meta:
                st.markdown(f"**{post['nome']}** <span style='color:#64748B; font-size:0.82rem;'>• {post['data']}</span>", unsafe_allow_html=True)
            with c_del:
                if post["usuario_id"] == usuario_id or user_info["cargo"] == "admin":
                    if st.button("🗑️", key=f"{prefixo_key}_del_{post['id']}", help="Excluir"):
                        if post.get("imagem"):
                            Path(post["imagem"]).unlink(missing_ok=True)
                        salvar_posts([p for p in carregar_posts() if p["id"] != post["id"]])
                        st.rerun()

            if post.get("texto"):
                st.write(post["texto"])
            if post.get("imagem") and Path(post["imagem"]).exists():
                exibir_imagem_interativa(post["imagem"], f"{prefixo_key}_img_{post['id']}", legenda=f"Publicado por {post['nome']}", usar_largura_total=True)

            curtidas = post.get("curtidas", [])
            ja_curtiu = usuario_id in curtidas
            comentarios = post.get("comentarios", [])
            
            b_like, _ = st.columns([1.3, 4.7])
            with b_like:
                lbl_l = f"💜 {len(curtidas)}" if ja_curtiu else f"🤍 {len(curtidas)}"
                if st.button(lbl_l, key=f"{prefixo_key}_like_{post['id']}", width="stretch"):
                    todos = carregar_posts()
                    for p in todos:
                        if p["id"] == post["id"]:
                            if usuario_id in p["curtidas"]:
                                p["curtidas"].remove(usuario_id)
                            else:
                                p["curtidas"].append(usuario_id)
                    salvar_posts(todos)
                    st.rerun()

            with st.expander(f"💬 Comentários ({len(comentarios)})"):
                for com in comentarios:
                    st.markdown(f"**{com['nome']}** *({com['hora']})*: {com['texto']}")
                ct1, ct2 = st.columns([4, 1])
                nc = ct1.text_input("Comentar...", key=f"{prefixo_key}_in_{post['id']}", label_visibility="collapsed")
                if ct2.button("Enviar", key=f"{prefixo_key}_btn_{post['id']}", width="stretch"):
                    if nc.strip():
                        todos = carregar_posts()
                        for p in todos:
                            if p["id"] == post["id"]:
                                p.setdefault("comentarios", []).append({
                                    "nome": user_info["nome"],
                                    "texto": nc.strip(),
                                    "hora": datetime.now().strftime("%d/%m %H:%M")
                                })
                        salvar_posts(todos)
                        st.rerun()

def render_navegar(usuario_id: str, user_info: dict, storage_dir: Path):
    usuarios = carregar_usuarios()
    posts = carregar_posts()
    
    st.subheader("🌐 Explorar & Atividades Recentes")
    st.caption("Acompanhe as publicações, atualizações e novidades compartilhadas pela comunidade.")
    
    c_search, c_filter = st.columns([3.2, 2.2])
    busca = c_search.text_input("Pesquisar:", placeholder="🔍 Buscar publicações ou autores...", label_visibility="collapsed").strip().lower()
    filtro = c_filter.radio("Filtro:", ["Recentes", "Populares", "Seguindo"], horizontal=True, label_visibility="collapsed")
    
    if busca:
        posts = [p for p in posts if busca in p.get("texto", "").lower() or busca in p.get("nome", "").lower()]
    if filtro == "Populares":
        posts.sort(key=lambda x: len(x.get("curtidas", [])), reverse=True)
    elif filtro == "Seguindo":
        amigos = set(listar_amigos(usuario_id) + [usuario_id])
        posts = [p for p in posts if p["usuario_id"] in amigos]
        
    exibir_lista_posts(posts, usuario_id, user_info, usuarios, "nav_clean")

def render_criar_post(usuario_id: str, user_info: dict):
    _, col_centro, _ = st.columns([0.8, 2.4, 0.8])
    with col_centro:
        with st.container(border=True):
            st.subheader("✍️ Criar publicação")
            st.caption("Compartilhe uma atualização, imagem ou ideia com os membros.")
            
            ca, cb = st.columns([0.55, 4.45])
            if user_info.get("avatar") and Path(user_info["avatar"]).exists():
                ca.image(user_info["avatar"], width=40)
            else:
                ca.markdown("👤")
            cb.markdown(f"**{user_info['nome']}**")
            
            texto = st.text_area("Conteúdo:", height=110, placeholder="No que você está pensando?", label_visibility="collapsed")
            anexo_img = st.file_uploader("🖼️ Adicionar Imagem ou Mídia", type=["jpg", "jpeg", "png", "webp", "heic"], key="post_clean_img")
            
            if anexo_img:
                st.image(anexo_img, caption="Pré-visualização do anexo", width="stretch")
                
            with st.expander("⚙️ Configurações adicionais", expanded=False):
                visib = st.selectbox("Visibilidade da publicação:", ["Público (Todo o grupo)", "Apenas Amigos"])
                
            if st.button("Publicar", type="primary", width="stretch"):
                if not texto.strip() and anexo_img is None:
                    st.warning("Escreva uma mensagem ou adicione uma imagem antes de publicar.")
                else:
                    criar_post_permanente(usuario_id, user_info["nome"], texto.strip(), anexo_img, visib)
                    st.success("Publicação realizada!")
                    st.session_state.cat_ativa = "Início"
                    time.sleep(0.3)
                    st.rerun()

def render_perfil_avatar(usuario_id: str, user_info: dict):
    usuarios = carregar_usuarios()
    todos_posts = carregar_posts()
    
    c_b1, c_b2 = st.columns([1.5, 2.5])
    busca_m = c_b1.text_input("Buscar membro:", placeholder="🔎 Nome ou @login...", label_visibility="collapsed").strip().lower()
    lista_ids = [u for u in usuarios.keys() if not busca_m or busca_m in u or busca_m in usuarios[u]["nome"].lower()]
    if not lista_ids:
        lista_ids = list(usuarios.keys())
        
    alvo_init = st.session_state.pop("perfil_visitado_rapido", usuario_id)
    idx_def = lista_ids.index(alvo_init) if alvo_init in lista_ids else 0
    perfil_id = c_b2.selectbox(
        "Perfil:",
        options=lista_ids,
        index=idx_def,
        format_func=lambda x: f"{usuarios[x]['nome']} (@{x})",
        label_visibility="collapsed"
    )
    
    alvo = usuarios[perfil_id]
    eh_meu = (perfil_id == usuario_id)
    
    from modules.settings import pode_ver_perfil
    if not pode_ver_perfil(usuario_id, user_info["cargo"], perfil_id):
        with st.container(border=True):
            st.warning(f"🔒 **O perfil de {alvo['nome']} é privado.**")
            st.caption("Apenas amigos, administradores ou membros com interação prévia podem visualizar este perfil.")
            if st.button("➕ Enviar Pedido de Amizade", type="primary"):
                ok, m = enviar_pedido_amizade(usuario_id, user_info["nome"], perfil_id)
                if ok: st.success(m); st.rerun()
        return

    posts_alvo = [p for p in todos_posts if p["usuario_id"] == perfil_id]
    posts_curtidos = [p for p in todos_posts if perfil_id in p.get("curtidas", [])]
    amigos_alvo = listar_amigos(perfil_id)
    total_likes = sum(len(p.get("curtidas", [])) for p in posts_alvo)

    with st.container(border=True):
        if alvo.get("banner") and Path(alvo["banner"]).exists():
            st.image(alvo["banner"], width="stretch")
        else:
            st.markdown(
                "<div style='height:90px; border-radius:10px; background:linear-gradient(120deg, #1E1B4B, #4C1D95, #0F172A); margin-bottom:8px;'></div>",
                unsafe_allow_html=True
            )
            
        col_av, col_info, col_stats, col_acts = st.columns([0.9, 2.5, 1.5, 1.3])
        with col_av:
            if alvo.get("avatar") and Path(alvo["avatar"]).exists():
                st.image(alvo["avatar"], width=86)
            else:
                st.markdown("<div style='font-size:3.2rem; text-align:center;'>👤</div>", unsafe_allow_html=True)
                
        with col_info:
            st.markdown(f"#### {alvo['nome']} <span style='color:#64748B; font-size:0.85rem;'>@{perfil_id}</span>", unsafe_allow_html=True)
            st.caption(alvo.get("bio", "Olá! Estou usando o OMNIX."))
            
        with col_stats:
            st.markdown(
                f"<div style='background:rgba(255,255,255,0.03); padding:8px 10px; border-radius:10px; font-size:0.82rem; color:#CBD5E1;'>"
                f"🤝 <b>{len(amigos_alvo)}</b> Amigos<br>"
                f"📝 <b>{len(posts_alvo)}</b> Publicações<br>"
                f"💜 <b>{total_likes}</b> Curtidas"
                f"</div>",
                unsafe_allow_html=True
            )
            
        with col_acts:
            if eh_meu:
                if st.button("✏️ Editar Perfil", width="stretch"):
                    st.session_state["abrir_edicao_perfil"] = not st.session_state.get("abrir_edicao_perfil", False)
                    st.rerun()
            else:
                rel = obter_status_relacao(usuario_id, perfil_id)
                if rel == "nenhum":
                    if st.button("➕ Adicionar", type="primary", width="stretch"):
                        enviar_pedido_amizade(usuario_id, user_info["nome"], perfil_id)
                        st.rerun()
                elif rel == "enviado":
                    if st.button("⏳ Pendente", width="stretch"):
                        recusar_ou_cancelar_pedido(usuario_id, perfil_id)
                        st.rerun()
                elif rel == "recebido":
                    if st.button("✅ Aceitar", type="primary", width="stretch"):
                        aceitar_pedido_amizade(usuario_id, perfil_id)
                        st.rerun()
                elif rel == "amigos":
                    if st.button("💬 Mensagem", type="primary", width="stretch"):
                        st.session_state["dm_alvo_rapido"] = perfil_id
                        st.session_state.cat_ativa = "Chat"
                        st.rerun()

    if eh_meu and st.session_state.get("abrir_edicao_perfil", False):
        with st.container(border=True):
            st.markdown("**Editar Perfil**")
            c1, c2 = st.columns(2)
            nav = c1.file_uploader("Avatar:", type=["jpg", "jpeg", "png", "webp", "heic"], key="ed_av_c")
            if nav and c1.button("Salvar Avatar"):
                atualizar_avatar(usuario_id, nav); st.rerun()
            nbn = c2.file_uploader("Capa Horizontal:", type=["jpg", "jpeg", "png", "webp", "heic"], key="ed_bn_c")
            if nbn and c2.button("Salvar Capa"):
                atualizar_banner(usuario_id, nbn); st.rerun()
            nn = st.text_input("Nome:", value=alvo["nome"])
            nb = st.text_area("Bio:", value=alvo.get("bio", ""), max_chars=160)
            nnum = st.text_input("Número OMNIX:", value=alvo.get("numero", ""))
            if st.button("💾 Salvar Alterações", type="primary"):
                ok, msg = atualizar_dados_perfil(usuario_id, nn, nb, nnum)
                if ok:
                    st.session_state["abrir_edicao_perfil"] = False
                    st.rerun()
                else:
                    st.error(msg)

    t_pub, t_amg, t_curt, t_sobre = st.tabs(["📝 Publicações", "🤝 Amigos", "💜 Curtidas", "ℹ️ Sobre"])
    
    with t_pub:
        exibir_lista_posts(posts_alvo, usuario_id, user_info, usuarios, "perf_pub")
        
    with t_amg:
        if eh_meu:
            render_amigos_hub(usuario_id)
        else:
            if not amigos_alvo:
                st.info("Nenhum amigo listado.")
            else:
                for aid in amigos_alvo:
                    if aid in usuarios:
                        st.markdown(f"• **{usuarios[aid]['nome']}** (`@{aid}`)")
                        
    with t_curt:
        exibir_lista_posts(posts_curtidos, usuario_id, user_info, usuarios, "perf_curt")
        
    with t_sobre:
        with st.container(border=True):
            st.markdown(f"**Nome de Exibição:** {alvo['nome']}")
            st.markdown(f"**Identificador:** `@{perfil_id}`")
            if alvo.get("configs", {}).get("mostrar_numero", True) or eh_meu or user_info["cargo"] == "admin":
                st.markdown(f"**Número OMNIX:** `#{alvo.get('numero', '0000')}`")
            st.markdown(f"**Biografia:** {alvo.get('bio', 'Sem biografia.')}")

def render_amigos_hub(usuario_id: str):
    usuarios = carregar_usuarios()
    recebidos = listar_pedidos_recebidos(usuario_id)
    meus_amigos = listar_amigos(usuario_id)

    if recebidos:
        st.markdown(f"**📩 Solicitações Recebidas ({len(recebidos)})**")
        for rem_id in recebidos:
            if rem_id in usuarios:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1, 1])
                    c1.write(f"**{usuarios[rem_id]['nome']}** (`@{rem_id}`)")
                    if c2.button("Aceitar", key=f"ac_{rem_id}", type="primary", width="stretch"):
                        aceitar_pedido_amizade(usuario_id, rem_id); st.rerun()
                    if c3.button("Recusar", key=f"rc_{rem_id}", width="stretch"):
                        recusar_ou_cancelar_pedido(usuario_id, rem_id); st.rerun()

    st.markdown(f"**🤝 Lista de Amigos ({len(meus_amigos)})**")
    if not meus_amigos:
        st.info("Você ainda não possui amigos adicionados.")
    else:
        for am_id in meus_amigos:
            if am_id in usuarios:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([3, 1.2, 1])
                    c1.write(f"**{usuarios[am_id]['nome']}** (`@{am_id}`)")
                    if c2.button("💬 Conversar", key=f"c_am_{am_id}", type="primary", width="stretch"):
                        st.session_state["dm_alvo_rapido"] = am_id
                        st.session_state.cat_ativa = "Chat"
                        st.rerun()
                    if c3.button("Remover", key=f"rm_am_{am_id}", width="stretch"):
                        remover_amigo(usuario_id, am_id); st.rerun()




