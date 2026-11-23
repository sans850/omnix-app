import streamlit as st
from modules.image_viewer import exibir_imagem_interativa
import json
import re
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps
import pillow_heif
from modules.admin import carregar_usuarios, buscar_usuario_por_numero, atualizar_estilo_nitro
from modules.social import registrar_notificacao
from modules.bot_voice import salvar_audio_gravado, processar_comando_bot
from modules.discord_extra import (
    carregar_grupos,
    salvar_grupos,
    listar_grupos_do_usuario,
    criar_novo_grupo,
    apagar_servidor,
    verificar_permissao_servidor,
    adicionar_membro_ao_grupo,
    remover_membro_do_grupo,
    criar_cargo_servidor,
    apagar_cargo_servidor,
    atribuir_cargo_membro,
    criar_canal_servidor,
    apagar_canal_servidor,
    carregar_emojis_custom,
    salvar_emoji_custom
)

pillow_heif.register_heif_opener()

CHAT_DM_FILE = Path("mensagens_dm.json")
CHAT_MEDIA_DIR = Path("omnix_chat_media")
CHAT_MEDIA_DIR.mkdir(exist_ok=True)

def formatar_texto_discord(texto: str) -> str:
    # Destaca menções @Nome em azul estilo Discord
    texto_fmt = re.sub(
        r'(@[\w\sÀ-ÿ]+?)(?=\s|$|[.,!?])',
        r"<span style='background:rgba(88,101,242,0.28); color:#A5B4FC; padding:1px 5px; border-radius:4px; font-weight:600;'>\1</span>",
        texto
    )
    # Transforma links http/https em links clicáveis
    texto_fmt = re.sub(
        r'(https?://[^\s<]+)',
        r"<a href='\1' target='_blank' style='color:#38BDF8; text-decoration:none;'>\1</a>",
        texto_fmt
    )
    return texto_fmt

def extrair_link_video(texto: str) -> str:
    match = re.search(r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/|vimeo\.com/|.*\.mp4)[^\s]*)', texto)
    return match.group(1) if match else ""

def salvar_anexo_chat(imagem_file, uid: str) -> str:
    if imagem_file is None:
        return ""
    ts = int(datetime.now().timestamp() * 1000)
    ext = Path(imagem_file.name).suffix.lower()
    imagem_file.seek(0)
    if ext == ".gif":
        caminho = CHAT_MEDIA_DIR / f"chat_{uid}_{ts}.gif"
        caminho.write_bytes(imagem_file.read())
        return str(caminho)
    img = Image.open(imagem_file)
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((1080, 1080))
    caminho = CHAT_MEDIA_DIR / f"chat_{uid}_{ts}.jpg"
    img.save(caminho, format="JPEG", quality=85)
    return str(caminho)

def enviar_msg_grupo(gid: str, canal: str, uid: str, nome: str, cargo: str, texto: str, anexo_path: str = "", emoji_custom: str = "", reply_to: dict = None, audio_path: str = ""):
    todos = carregar_grupos()
    if gid not in todos:
        return
    ts = int(datetime.now().timestamp() * 1000)
    todos[gid]["canais"].setdefault(canal, []).append({
        "msg_id": ts,
        "id": uid.strip().lower(),
        "nome": nome,
        "cargo": cargo,
        "texto": texto,
        "anexo": anexo_path,
        "emoji_custom": emoji_custom, "audio": audio_path, "audio": audio_path,
        "reply": reply_to or {},
        "reacoes": {},
        "hora": datetime.now().strftime("%d/%m %H:%M")
    })
    todos[gid]["canais"][canal] = todos[gid]["canais"][canal][-200:]
    salvar_grupos(todos)
    registrar_notificacao(uid, nome, f"🏰 {todos[gid]['nome']}", f"enviou em #{canal}: '{texto[:25]}'")

def apagar_msg_grupo(gid: str, canal: str, msg_id: int):
    todos = carregar_grupos()
    if gid in todos and canal in todos[gid].get("canais", {}):
        todos[gid]["canais"][canal] = [m for m in todos[gid]["canais"][canal] if m.get("msg_id") != msg_id]
        salvar_grupos(todos)

def alternar_reacao_grupo(gid: str, canal: str, msg_id: int, emoji: str, uid: str):
    todos = carregar_grupos()
    for m in todos.get(gid, {}).get("canais", {}).get(canal, []):
        if m.get("msg_id") == msg_id:
            reacs = m.setdefault("reacoes", {})
            lista = reacs.setdefault(emoji, [])
            if uid in lista:
                lista.remove(uid)
            else:
                lista.append(uid)
            if not lista:
                del reacs[emoji]
            break
    salvar_grupos(todos)

def gerar_chave_sala(user_a: str, user_b: str) -> str:
    pares = sorted([user_a.strip().lower(), user_b.strip().lower()])
    return f"{pares}__{pares}"

def carregar_todas_dms() -> dict:
    if not CHAT_DM_FILE.exists():
        return {}
    try:
        return json.loads(CHAT_DM_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def salvar_mensagem_dm(remetente_id: str, remetente_nome: str, destinatario_id: str, texto: str, anexo_path: str = "", emoji_custom: str = "", audio_path: str = ""):
    todas = carregar_todas_dms()
    chave = gerar_chave_sala(remetente_id, destinatario_id)
    sala = todas.get(chave, [])
    uid_rem = remetente_id.strip().lower()
    sala.append({
        "msg_id": int(datetime.now().timestamp() * 1000),
        "id": uid_rem,
        "nome": remetente_nome,
        "texto": texto,
        "anexo": anexo_path,
        "emoji_custom": emoji_custom, "audio": audio_path, "audio": audio_path,
        "hora": datetime.now().strftime("%d/%m %H:%M")
    })
    todas[chave] = sala[-200:]
    CHAT_DM_FILE.write_text(json.dumps(todas, indent=4, ensure_ascii=False), encoding="utf-8")
    registrar_notificacao(uid_rem, remetente_nome, "🔒 DM Privada", "te enviou uma mensagem direta.")

def rolar_chat_para_baixo():
    pass

def renderizar_linha_mensagem_oled(msg: dict, uid_atual: str, cargo_global: str, usuarios: dict, gid: str = "", canal: str = "", idx: int = 0, mostrar_reacoes: bool = True, grupo_obj: dict = None, eh_ultima: bool = False):
    msg_uid = str(msg.get("id", "")).strip().lower()
    autor = usuarios.get(msg_uid, {})
    cor_nome = autor.get("cor_nome", "#F8FAFC")
    tag_nitro = autor.get("tag_nitro", "")
    avatar_path = autor.get("avatar", "")
    msg_id = msg.get("msg_id", idx)

    cargo_srv_html = ""
    if grupo_obj:
        cid = grupo_obj.get("membros_cargos", {}).get(msg_uid, "")
        if cid and cid in grupo_obj.get("cargos", {}):
            c_info = grupo_obj["cargos"][cid]
            cor_nome = c_info["cor"]
            cargo_srv_html = f"<span style='background:{c_info['cor']}25; color:{c_info['cor']}; padding:1px 6px; border-radius:4px; font-size:0.68rem; font-weight:700; margin-left:5px;'>{c_info['nome']}</span>"

    # Divisor vermelho estilo Discord antes da última mensagem nova
    if eh_ultima and msg_uid != uid_atual:
        st.markdown(
            "<div style='display:flex; align-items:center; margin:8px 0;'>"
            "<div style='flex:1; height:1px; background:#EF4444;'></div>"
            "<span style='background:#EF4444; color:white; font-size:0.65rem; font-weight:800; padding:1px 6px; border-radius:4px;'>NOVO</span>"
            "</div>",
            unsafe_allow_html=True
        )

    rep = msg.get("reply", {})
    if rep and rep.get("nome"):
        st.markdown(
            f"<div style='font-size:0.78rem; color:#94A3B8; border-left:2px solid #4F46E5; "
            f"padding-left:8px; margin-left:36px; margin-bottom:2px;'>"
            f"↩️ <b>{rep['nome']}</b>: <i>{rep.get('texto', '')[:55]}</i></div>",
            unsafe_allow_html=True
        )

    c_av, c_body, c_act = st.columns([0.55, 4.35, 1.2])
    with c_av:
        if avatar_path and Path(avatar_path).exists():
            st.image(avatar_path, width=40)
        else:
            st.markdown(
                f"<div style='width:38px; height:38px; border-radius:50%; background:#1E293B; "
                f"display:flex; align-items:center; justify-content:center; font-weight:bold; color:{cor_nome};'>"
                f"{msg['nome'][:1].upper()}</div>",
                unsafe_allow_html=True
            )

    with c_body:
        tag_html = f"<span style='background:rgba(255,255,255,0.08); color:#E2E8F0; padding:1px 5px; border-radius:4px; font-size:0.7rem; margin-left:5px;'>{tag_nitro}</span>" if tag_nitro else ""
        st.markdown(
            f"<span style='color:{cor_nome}; font-weight:700; font-size:0.96rem;'>{msg['nome']}</span>"
            f"{tag_html}{cargo_srv_html}"
            f"<span style='color:#64748B; font-size:0.72rem; margin-left:8px;'>{msg['hora']}</span>",
            unsafe_allow_html=True
        )

        emj_path = msg.get("emoji_custom", "")
        if emj_path and Path(emj_path).exists():
            st.image(emj_path, width=128)

        texto_msg = msg.get("texto", "")
        if texto_msg:
            st.markdown(f"<div style='color:#E2E8F0; font-size:0.94rem; line-height:1.4; margin-top:2px;'>{formatar_texto_discord(texto_msg)}</div>", unsafe_allow_html=True)
            link_vid = extrair_link_video(texto_msg)
            if link_vid:
                st.video(link_vid)

        if msg.get("anexo") and Path(msg["anexo"]).exists():
                exibir_imagem_interativa(msg["anexo"], f"chat_anx_{gid}_{canal}_{msg_id}_{idx}", largura_thumb=340, legenda=f"Enviado por {msg['nome']}")

        if msg.get("audio") and Path(msg["audio"]).exists():
            st.audio(msg["audio"], format="audio/wav")

    with c_act:
        pode_apagar = (msg_uid == uid_atual) or (gid and verificar_permissao_servidor(gid, uid_atual, cargo_global, "apagar_msg"))
        b_p, b_r, b_d = st.columns(3)
        if msg_uid in usuarios:
            if b_p.button("👤", key=f"p_{gid}_{canal}_{msg_id}_{idx}", help="Ver Perfil"):
                st.session_state["perfil_visitado_rapido"] = msg_uid
                st.session_state["aba_social_alvo"] = "perfis"
                st.session_state.cat_ativa = "Social"
                st.session_state["radio_sub_social"] = "👤 Perfil & Membros"
                st.rerun()
        if gid and canal:
            if b_r.button("↩️", key=f"r_{gid}_{canal}_{msg_id}_{idx}", help="Responder"):
                st.session_state["reply_alvo"] = {"nome": msg["nome"], "texto": texto_msg or "[Mídia/Figurinha]"}
                st.rerun()
            if pode_apagar:
                if b_d.button("🗑️", key=f"delm_{gid}_{canal}_{msg_id}_{idx}", help="Apagar"):
                    apagar_msg_grupo(gid, canal, msg_id)
                    st.rerun()

    # Reações compactas estilo pílula do Discord
    if gid and canal and mostrar_reacoes:
        reacs = msg.get("reacoes", {})
        emojis_rapidos = ["❤️", "✅", "👍", "😂"]
        cols_r = st.columns(6)
        for e_idx, emj in enumerate(emojis_rapidos):
            qtd = len(reacs.get(emj, []))
            lbl = f"{emj} {qtd}" if qtd > 0 else emj
            if cols_r[e_idx].button(lbl, key=f"rx_{gid}_{canal}_{msg_id}_{emj}_{idx}"):
                alternar_reacao_grupo(gid, canal, msg_id, emj, uid_atual)
                st.rerun()

    st.markdown("<hr style='margin:6px 0; border:none; border-top:1px solid rgba(255,255,255,0.04);'>", unsafe_allow_html=True)

@st.fragment(run_every=4)
def feed_grupo_realtime(uid_atual: str, cargo_global: str, gid: str, canal: str, mostrar_reacoes: bool):
    todos = carregar_grupos()
    usuarios = carregar_usuarios()
    grupo_obj = todos.get(gid, {})
    mensagens = grupo_obj.get("canais", {}).get(canal, [])[-40:]
    
    box = st.container(height=460, border=True)
    with box:
        if not mensagens:
            st.info(f"Bem-vindo a **#{canal}**! Envie a primeira mensagem.")
        else:
            for idx, msg in enumerate(mensagens):
                eh_ult = (idx == len(mensagens) - 1)
                renderizar_linha_mensagem_oled(msg, uid_atual, cargo_global, usuarios, gid, canal, idx, mostrar_reacoes, grupo_obj, eh_ult)
            rolar_chat_para_baixo()

@st.fragment(run_every=4)
def feed_dm_realtime(uid_atual: str, cargo_global: str, destinatario_id: str):
    todas = carregar_todas_dms()
    usuarios = carregar_usuarios()
    chave = gerar_chave_sala(uid_atual, destinatario_id)
    mensagens = todas.get(chave, [])[-40:]
    
    box = st.container(height=440, border=True)
    with box:
        if not mensagens:
            st.info("Início da conversa direta.")
        else:
            for idx, msg in enumerate(mensagens):
                eh_ult = (idx == len(mensagens) - 1)
                renderizar_linha_mensagem_oled(msg, uid_atual, cargo_global, usuarios, "", "", idx, False, None, eh_ult)
            rolar_chat_para_baixo()

def renderizar_mensagem_omnix(msg: dict, uid_atual: str, cargo_global: str, usuarios: dict, gid: str = "", canal: str = "", idx: int = 0, mostrar_reacoes: bool = True, grupo_obj: dict = None, eh_ultima: bool = False):
    msg_uid = str(msg.get("id", "")).strip().lower()
    autor = usuarios.get(msg_uid, {})
    cor_nome = autor.get("cor_nome", "#38BDF8")
    tag_plus = autor.get("tag_nitro", "⚡")
    avatar_path = autor.get("avatar", "")
    msg_id = msg.get("msg_id", idx)
    eh_minha = (msg_uid == uid_atual)

    cargo_sala_html = ""
    if grupo_obj:
        cid = grupo_obj.get("membros_cargos", {}).get(msg_uid, "")
        if cid and cid in grupo_obj.get("cargos", {}):
            c_info = grupo_obj["cargos"][cid]
            cor_nome = c_info["cor"]
            cargo_sala_html = (
                f"<span style='background:{c_info['cor']}20; border:1px solid {c_info['cor']}66; "
                f"color:{c_info['cor']}; padding:1px 7px; border-radius:99px; font-size:0.68rem; "
                f"font-weight:700; margin-left:6px;'>{c_info['nome']}</span>"
            )

    if eh_ultima and not eh_minha:
        st.markdown(
            "<div style='display:flex; align-items:center; gap:8px; margin:10px 0;'>"
            "<div style='flex:1; height:1px; background:linear-gradient(90deg, transparent, #38BDF8, #A855F7);'></div>"
            "<span style='background:linear-gradient(90deg, #0284C7, #7C3AED); color:white; font-size:0.64rem; "
            "font-weight:800; padding:2px 8px; border-radius:99px; letter-spacing:0.8px;'>NOVA MENSAGEM</span>"
            "</div>",
            unsafe_allow_html=True
        )

    with st.container(border=True):
        rep = msg.get("reply", {})
        if rep and rep.get("nome"):
            st.markdown(
                f"<div style='font-size:0.76rem; color:#94A3B8; background:rgba(255,255,255,0.04); "
                f"padding:3px 9px; border-radius:8px; margin-bottom:5px; display:inline-block;'>"
                f"↪️ Em resposta a <b style='color:#38BDF8;'>{rep['nome']}</b>: <i>{rep.get('texto', '')[:50]}</i></div>",
                unsafe_allow_html=True
            )

        c_av, c_body, c_act = st.columns([0.55, 4.35, 1.2])
        with c_av:
            if avatar_path and Path(avatar_path).exists():
                st.image(avatar_path, width=40)
            else:
                st.markdown(
                    f"<div style='width:38px; height:38px; border-radius:12px; background:linear-gradient(135deg, {cor_nome}44, #1E293B); "
                    f"border:1px solid {cor_nome}; display:flex; align-items:center; justify-content:center; "
                    f"font-weight:800; color:{cor_nome};'>{msg['nome'][:1].upper()}</div>",
                    unsafe_allow_html=True
                )

        with c_body:
            if msg_uid == "omnix_bot":
                cor_nome = "#A855F7"
                selo_plus = "<span style='background:linear-gradient(90deg,#38BDF8,#A855F7); color:white; padding:1px 6px; border-radius:6px; font-size:0.65rem; font-weight:800; margin-left:6px;'>🤖 IA BOT</span>"
            else:
                selo_plus = f"<span style='color:{cor_nome}; font-size:0.78rem; margin-left:4px;'>{tag_plus}</span>" if tag_plus else ""
            st.markdown(
                f"<span style='color:{cor_nome}; font-weight:800; font-size:0.95rem;'>{msg['nome']}</span>"
                f"{selo_plus}{cargo_sala_html}"
                f"<span style='color:#64748B; font-size:0.72rem; margin-left:8px;'>• {msg['hora']}</span>",
                unsafe_allow_html=True
            )

            emj_path = msg.get("emoji_custom", "")
            if emj_path and Path(emj_path).exists():
                st.image(emj_path, width=128)

            texto_msg = msg.get("texto", "")
            if texto_msg:
                st.markdown(f"<div style='color:#F1F5F9; font-size:0.94rem; line-height:1.45; margin-top:2px;'>{formatar_texto_discord(texto_msg)}</div>", unsafe_allow_html=True)
                link_vid = extrair_link_video(texto_msg)
                if link_vid:
                    st.video(link_vid)

            if msg.get("anexo") and Path(msg["anexo"]).exists():
                exibir_imagem_interativa(msg["anexo"], f"chat_anx_{gid}_{canal}_{msg_id}_{idx}", largura_thumb=340, legenda=f"Enviado por {msg['nome']}")

            if msg.get("audio") and Path(msg["audio"]).exists():
                st.audio(msg["audio"], format="audio/wav")

        with c_act:
            pode_apagar = (msg_uid == uid_atual) or (gid and verificar_permissao_servidor(gid, uid_atual, cargo_global, "apagar_msg"))
            b_p, b_r, b_d = st.columns(3)
            if msg_uid in usuarios:
                if b_p.button("👤", key=f"p_{gid}_{canal}_{msg_id}_{idx}", help="Ver Perfil"):
                    st.session_state["perfil_visitado_rapido"] = msg_uid
                    st.session_state["aba_social_alvo"] = "perfis"
                    st.session_state.cat_ativa = "Social"
                    st.session_state["radio_sub_social"] = "👤 Perfil & Membros"
                    st.rerun()
            if gid and canal:
                if b_r.button("↩️", key=f"r_{gid}_{canal}_{msg_id}_{idx}", help="Citar"):
                    st.session_state["reply_alvo"] = {"nome": msg["nome"], "texto": texto_msg or "[Mídia/Figurinha]"}
                    st.rerun()
                if pode_apagar:
                    if b_d.button("🗑️", key=f"delm_{gid}_{canal}_{msg_id}_{idx}", help="Apagar"):
                        apagar_msg_grupo(gid, canal, msg_id)
                        st.rerun()

        if gid and canal and mostrar_reacoes:
            reacs = msg.get("reacoes", {})
            emojis_rapidos = ["⚡", "🔥", "❤️", "😂"]
            cols_r = st.columns(6)
            for e_idx, emj in enumerate(emojis_rapidos):
                qtd = len(reacs.get(emj, []))
                lbl = f"{emj} {qtd}" if qtd > 0 else emj
                if cols_r[e_idx].button(lbl, key=f"rx_{gid}_{canal}_{msg_id}_{emj}_{idx}"):
                    alternar_reacao_grupo(gid, canal, msg_id, emj, uid_atual)
                    st.rerun()
@st.fragment(run_every=4)
def feed_grupo_realtime(uid_atual: str, cargo_global: str, gid: str, canal: str, mostrar_reacoes: bool):
    todos = carregar_grupos()
    usuarios = carregar_usuarios()
    grupo_obj = todos.get(gid, {})
    mensagens = grupo_obj.get("canais", {}).get(canal, [])[-40:]
    
    box = st.container(height=450, border=True)
    with box:
        if not mensagens:
            st.info(f"Frequência **#{canal}** livre! Envie a primeira mensagem ou figurinha.")
        else:
            for idx, msg in enumerate(mensagens):
                eh_ult = (idx == len(mensagens) - 1)
                renderizar_mensagem_omnix(msg, uid_atual, cargo_global, usuarios, gid, canal, idx, mostrar_reacoes, grupo_obj, eh_ult)
            rolar_chat_para_baixo()

@st.fragment(run_every=4)
def feed_dm_realtime(uid_atual: str, cargo_global: str, destinatario_id: str):
    todas = carregar_todas_dms()
    usuarios = carregar_usuarios()
    chave = gerar_chave_sala(uid_atual, destinatario_id)
    mensagens = todas.get(chave, [])[-40:]
    
    box = st.container(height=430, border=True)
    with box:
        if not mensagens:
            st.info("Canal direto criptografado pronto. Diga oi!")
        else:
            for idx, msg in enumerate(mensagens):
                eh_ult = (idx == len(mensagens) - 1)
                renderizar_mensagem_omnix(msg, uid_atual, cargo_global, usuarios, "", "", idx, False, None, eh_ult)
            rolar_chat_para_baixo()

def render_config_servidor(gid: str, grupo_obj: dict, uid_atual: str, cargo_global: str, usuarios: dict):
    st.subheader(f"🛠️ Gestão da Sala: {grupo_obj['nome']}")
    eh_dono_ou_adm = (grupo_obj.get("dono") == uid_atual) or (cargo_global == "admin")
    pode_cargos = eh_dono_ou_adm or verificar_permissao_servidor(gid, uid_atual, cargo_global, "gerenciar_cargos")
    pode_canais = eh_dono_ou_adm or verificar_permissao_servidor(gid, uid_atual, cargo_global, "gerenciar_canais")

    t_cargos, t_membros, t_canais, t_geral_srv = st.tabs(["🎖️ Cargos & Poderes", "👥 Participantes", "📡 Frequências", "🗑️ Encerrar Sala"])

    with t_cargos:
        if not pode_cargos:
            st.warning("Sem permissão para editar cargos desta sala.")
        else:
            with st.form("form_novo_cargo", clear_on_submit=True):
                c1, c2 = st.columns(2)
                nome_c = c1.text_input("Título do Cargo (ex: Líder, DJ, VIP):")
                cor_c = c2.color_picker("Cor de Destaque:", value="#38BDF8")
                perms = st.multiselect(
                    "Poderes do Cargo:",
                    ["apagar_msg", "convidar", "gerenciar_canais", "gerenciar_cargos"],
                    format_func=lambda p: {"apagar_msg": "Moderar Mensagens", "convidar": "Convidar Pessoas", "gerenciar_canais": "Criar/Apagar Frequências", "gerenciar_cargos": "Gerenciar Cargos"}[p]
                )
                if st.form_submit_button("Criar Cargo", type="primary"):
                    ok, msg = criar_cargo_servidor(gid, nome_c, cor_c, perms)
                    if ok: st.rerun()
                    else: st.error(msg)

            for cid, cdata in list(grupo_obj.get("cargos", {}).items()):
                cc1, cc2 = st.columns([4, 1])
                cc1.markdown(f"<span style='color:{cdata['cor']}; font-weight:700;'>◈ {cdata['nome']}</span>", unsafe_allow_html=True)
                if cc2.button("🗑️", key=f"del_cg_{gid}_{cid}"):
                    apagar_cargo_servidor(gid, cid)
                    st.rerun()

    with t_membros:
        cargos_srv = grupo_obj.get("cargos", {})
        opcoes_c = [""] + list(cargos_srv.keys())
        for m_id in grupo_obj.get("membros", []):
            if m_id in usuarios:
                cm1, cm2, cm3 = st.columns([2.2, 2.2, 1])
                cm1.write(f"**{usuarios[m_id]['nome']}**")
                if pode_cargos:
                    atual_c = grupo_obj.get("membros_cargos", {}).get(m_id, "")
                    novo_c = cm2.selectbox("Cargo", opcoes_c, index=opcoes_c.index(atual_c) if atual_c in opcoes_c else 0, key=f"sc_{gid}_{m_id}", format_func=lambda x: "Membro Padrão" if not x else cargos_srv[x]["nome"], label_visibility="collapsed")
                    if novo_c != atual_c:
                        atribuir_cargo_membro(gid, m_id, novo_c)
                        st.rerun()
                if eh_dono_ou_adm and m_id != grupo_obj.get("dono") and m_id != uid_atual:
                    if cm3.button("Remover", key=f"kk_{gid}_{m_id}"):
                        remover_membro_do_grupo(gid, m_id)
                        st.rerun()

    with t_canais:
        if pode_canais:
            cn1, cn2 = st.columns([3, 1.2])
            nc = cn1.text_input("Nova frequência:", label_visibility="collapsed", placeholder="ex: jogos-e-lives")
            if cn2.button("➕ Adicionar", type="primary", width="stretch"):
                ok, m = criar_canal_servidor(gid, nc)
                if ok: st.rerun()
                else: st.error(m)
            for cn in list(grupo_obj.get("canais", {}).keys()):
                ccn, ccd = st.columns([4, 1])
                ccn.write(f"**# {cn}**")
                if ccd.button("🗑️", key=f"dcn_{gid}_{cn}"):
                    apagar_canal_servidor(gid, cn)
                    st.rerun()

    with t_geral_srv:
        if eh_dono_ou_adm and gid != "grp_geral":
            if st.checkbox("Confirmar exclusão permanente desta sala", key=f"cf_d_{gid}"):
                if st.button("🗑️ APAGAR SALA", type="primary"):
                    apagar_servidor(gid)
                    st.session_state["modo_pulse"] = "dm"
                    st.session_state["abrir_config_server"] = False
                    st.rerun()

def render_messages(usuario_id: str, user_info: dict):
    usuarios = carregar_usuarios()
    uid_atual = usuario_id.strip().lower()
    cargo_global = user_info["cargo"]
    meus_grupos = listar_grupos_do_usuario(uid_atual, cargo_global)

    if "modo_pulse" not in st.session_state:
        st.session_state["modo_pulse"] = "dm"

    with st.container(border=True):
        nc_dm, nc_sel, nc_go, nc_new = st.columns([1.4, 3.2, 1.1, 1.1])
        
        tp_dm = "primary" if st.session_state["modo_pulse"] == "dm" else "secondary"
        if nc_dm.button("💬 Mensagens", key="pulse_dm_btn", type=tp_dm, width="stretch"):
            st.session_state["modo_pulse"] = "dm"
            st.rerun()

        lista_gids = list(meus_grupos.keys())
        srv_salvo = st.session_state.get("servidor_selecionado_id", next(iter(lista_gids), ""))
        idx_srv = lista_gids.index(srv_salvo) if srv_salvo in lista_gids else 0

        gid_escolhido = nc_sel.selectbox(
            "Salas:",
            options=lista_gids,
            index=idx_srv,
            format_func=lambda x: f"🌐 Sala: {meus_grupos[x]['nome']} ({len(meus_grupos[x]['membros'])})",
            label_visibility="collapsed"
        )
        if gid_escolhido != st.session_state.get("servidor_selecionado_id") and st.session_state["modo_pulse"] == "server":
            st.session_state["servidor_selecionado_id"] = gid_escolhido
            st.rerun()
        st.session_state["servidor_selecionado_id"] = gid_escolhido

        if nc_go.button("🌐 Entrar na Sala", key="pulse_go_srv", type="primary" if st.session_state["modo_pulse"] == "server" else "secondary", width="stretch"):
            st.session_state["modo_pulse"] = "server"
            st.rerun()

        with nc_new.popover("➕ Nova Sala", width="stretch"):
            novo_srv = st.text_input("Nome da Sala:")
            if st.button("Criar e Abrir", type="primary", width="stretch"):
                if novo_srv.strip():
                    novo_gid = criar_novo_grupo(novo_srv, uid_atual)
                    st.session_state["modo_pulse"] = "server"
                    st.session_state["servidor_selecionado_id"] = novo_gid
                    st.session_state["abrir_config_server"] = False
                    st.rerun()

    c_opt1, c_opt2, c_opt3 = st.columns([2.5, 1.3, 1.2])
    modo_foco = c_opt3.toggle("🔽 Foco Total", value=False)

    with c_opt2:
        with st.popover("✨ Plus & Figurinhas", width="stretch"):
            t_p1, t_p2 = st.tabs(["🎨 Estilo Plus", "🎭 Criar Fig."])
            with t_p1:
                nc = st.color_picker("Cor do seu Nome:", value=user_info.get("cor_nome", "#38BDF8"))
                nt = st.text_input("Ícone ao lado do nome:", value=user_info.get("tag_nitro", "⚡"), max_chars=6)
                if st.button("Aplicar Estilo", type="primary", width="stretch"):
                    atualizar_estilo_nitro(uid_atual, nc, nt)
                    st.rerun()
            with t_p2:
                n_emj = st.text_input("Código (ex: mito):")
                a_emj = st.file_uploader("Imagem/GIF:", type=["png", "jpg", "jpeg", "webp", "gif"], key="up_emj_pulse")
                if a_emj and st.button("Salvar Figurinha", type="primary", width="stretch"):
                    ok_e, m_e = salvar_emoji_custom(n_emj, a_emj, user_info["nome"])
                    if ok_e: st.rerun()
                    else: st.error(m_e)

    if modo_foco:
        col_chat_main = st.container()
        col_lateral = None
    else:
        col_lateral, col_chat_main = st.columns([1.65, 4.35])

    if col_lateral:
        with col_lateral:
            with st.container(border=True):
                if st.session_state["modo_pulse"] == "dm":
                    busca_dm = st.text_input("🔍 Buscar contato...", placeholder="Nome ou #Número", label_visibility="collapsed").strip().lower()
                    outros = [u for u in usuarios.keys() if u.strip().lower() != uid_atual]
                    if busca_dm:
                        outros = [u for u in outros if busca_dm in u or busca_dm in usuarios[u]["nome"].lower() or busca_dm.replace("#", "") == str(usuarios[u].get("numero", ""))]

                    dm_atual = st.session_state.get("dm_alvo_rapido", "omnix_bot")
                    sel_bot = (dm_atual == "omnix_bot")
                    if st.button("🤖 OMNIX Bot (IA)", key="dm_p_omnix_bot", type="primary" if sel_bot else "secondary", width="stretch"):
                        st.session_state["dm_alvo_rapido"] = "omnix_bot"
                        st.rerun()
                    st.markdown("<hr style='margin:6px 0; border-color:rgba(255,255,255,0.08);'>", unsafe_allow_html=True)
                    for o_uid in outros:
                        o_info = usuarios[o_uid]
                        sel = (o_uid == dm_atual)
                        if st.button(f"● {o_info['nome']}", key=f"dm_p_{o_uid}", type="primary" if sel else "secondary", width="stretch"):
                            st.session_state["dm_alvo_rapido"] = o_uid
                            st.rerun()
                else:
                    gid_ativo = st.session_state.get("servidor_selecionado_id", next(iter(meus_grupos.keys()), ""))
                    g_obj = meus_grupos[gid_ativo]
                    st.markdown(f"**🌐 {g_obj['nome']}**")
                    
                    if st.button("🛠️ Gerenciar Sala", width="stretch"):
                        st.session_state["abrir_config_server"] = not st.session_state.get("abrir_config_server", False)
                        st.rerun()

                    st.caption("FREQUÊNCIAS")
                    canais_srv = list(g_obj.get("canais", {"geral": []}).keys())
                    c_ativo = st.session_state.get("canal_grp_ativo", next(iter(canais_srv), "geral"))
                    if not isinstance(c_ativo, str) or c_ativo not in canais_srv:
                        c_ativo = next(iter(canais_srv), "geral")
                        st.session_state["canal_grp_ativo"] = c_ativo

                    for cn in canais_srv:
                        if st.button(f"◈ {cn}", key=f"ch_p_{gid_ativo}_{cn}", type="primary" if cn == c_ativo else "secondary", width="stretch"):
                            st.session_state["canal_grp_ativo"] = cn
                            st.rerun()

                    if verificar_permissao_servidor(gid_ativo, uid_atual, cargo_global, "convidar"):
                        with st.popover("➕ Convidar", width="stretch"):
                            cands = [u for u in usuarios.keys() if u not in g_obj["membros"]]
                            if cands:
                                cu = st.selectbox("Pessoa:", cands, format_func=lambda x: usuarios[x]["nome"])
                                if st.button("Adicionar à Sala", type="primary", width="stretch"):
                                    adicionar_membro_do_grupo(gid_ativo, cu)
                                    st.rerun()
                            else:
                                st.caption("Todos já participam.")

            with st.container(border=True):
                rf1, rf2 = st.columns([1, 2.5])
                if user_info.get("avatar") and Path(user_info["avatar"]).exists():
                    rf1.image(user_info["avatar"], width=36)
                else:
                    rf1.write("⚡")
                rf2.markdown(f"**{user_info['nome']}**\n<span style='color:#38BDF8; font-size:0.72rem;'>● Conectado • #{user_info.get('numero', '0000')}</span>", unsafe_allow_html=True)

    with col_chat_main:
        emojis_salvos = carregar_emojis_custom()

        if st.session_state["modo_pulse"] == "dm":
            outros = [u for u in usuarios.keys() if u.strip().lower() != uid_atual]
            if not outros:
                st.info("Nenhum outro membro cadastrado ainda.")
                return
            dest_id = st.session_state.get("dm_alvo_rapido", next(iter(outros), ""))
            if not isinstance(dest_id, str) or dest_id not in outros:
                dest_id = next(iter(outros), "")
                st.session_state["dm_alvo_rapido"] = dest_id

            dest_info = usuarios[dest_id]
            c_opt1.markdown(f"#### 💬 **{dest_info['nome']}** <span style='color:#64748B; font-size:0.85rem;'>#{dest_info.get('numero', '0000')}</span>", unsafe_allow_html=True)
            feed_dm_realtime(uid_atual, cargo_global, dest_id)
        else:
            gid_ativo = st.session_state.get("servidor_selecionado_id", next(iter(meus_grupos.keys()), ""))
            g_obj = meus_grupos[gid_ativo]
            canais_srv = list(g_obj.get("canais", {"geral": []}).keys())
            c_ativo = st.session_state.get("canal_grp_ativo", next(iter(canais_srv), "geral"))
            if not isinstance(c_ativo, str) or c_ativo not in canais_srv:
                c_ativo = next(iter(canais_srv), "geral")

            c_opt1.markdown(f"#### ◈ **{c_ativo}** <span style='color:#64748B; font-size:0.85rem;'>• {g_obj['nome']}</span>", unsafe_allow_html=True)

            if st.session_state.get("abrir_config_server", False):
                with st.container(border=True):
                    render_config_servidor(gid_ativo, g_obj, uid_atual, cargo_global, usuarios)
                    if st.button("Fechar Gestão da Sala", width="stretch"):
                        st.session_state["abrir_config_server"] = False
                        st.rerun()

            feed_grupo_realtime(uid_atual, cargo_global, gid_ativo, c_ativo, True)

        if "figurinha_engatilhada" in st.session_state and st.session_state["figurinha_engatilhada"]:
            fig_s = st.session_state["figurinha_engatilhada"]
            with st.container(border=True):
                cf1, cf2, cf3, cf4 = st.columns([1, 2.8, 1.3, 0.7])
                if Path(fig_s["caminho"]).exists():
                    cf1.image(fig_s["caminho"], width=72)
                cf2.markdown(f"**🎭 Figurinha `:{fig_s['cod']}:` pronta!** Escreva abaixo para mandar junto:")
                if cf3.button("🚀 Só Ela", key="send_fig_now", type="primary", width="stretch"):
                    fig_d = st.session_state.pop("figurinha_engatilhada")
                    if st.session_state["modo_pulse"] == "dm":
                        salvar_mensagem_dm(uid_atual, user_info["nome"], dest_id, "", "", fig_d["caminho"])
                    else:
                        rep_d = st.session_state.pop("reply_alvo", None)
                        enviar_msg_grupo(gid_ativo, c_ativo, uid_atual, user_info["nome"], cargo_global, "", "", fig_d["caminho"], rep_d)
                    st.rerun()
                if cf4.button("❌", key="c_fig_now", width="stretch"):
                    del st.session_state["figurinha_engatilhada"]
                    st.rerun()

        with st.expander("🎭 Figurinhas Especiais, GIFs & Anexos", expanded=False):
            if emojis_salvos:
                cols_em = st.columns(min(len(emojis_salvos), 5))
                for e_i, (cod, edata) in enumerate(list(emojis_salvos.items())[:15]):
                    with cols_em[e_i % 5]:
                        if Path(edata["caminho"]).exists():
                            st.image(edata["caminho"], width=68)
                            if st.button(f":{cod}:", key=f"pk_emj_{cod}", width="stretch"):
                                st.session_state["figurinha_engatilhada"] = {"cod": cod, "caminho": edata["caminho"]}
                                st.rerun()
            st.divider()
            voz_up = st.audio_input("🎙️ Gravar Mensagem de Voz:", key="rec_voz_pulse")
            if voz_up and st.button("🚀 Enviar Áudio", key="btn_send_voz", type="primary"):
                p_voz = salvar_audio_gravado(voz_up, uid_atual)
                if st.session_state["modo_pulse"] == "dm":
                    salvar_mensagem_dm(uid_atual, user_info["nome"], dest_id, "🎙️ Mensagem de voz", "", "", p_voz)
                else:
                    rep_d = st.session_state.pop("reply_alvo", None)
                    enviar_msg_grupo(gid_ativo, c_ativo, uid_atual, user_info["nome"], cargo_global, "🎙️ Mensagem de voz", "", "", rep_d, p_voz)
                st.rerun()

            st.divider()
            anx_up = st.file_uploader("Anexar imagem/GIF:", type=["jpg", "jpeg", "png", "webp", "gif", "heic"], key="up_pulse_anx")
            if anx_up and st.button("Enviar Imagem", type="primary"):
                p_a = salvar_anexo_chat(anx_up, uid_atual)
                if st.session_state["modo_pulse"] == "dm":
                    salvar_mensagem_dm(uid_atual, user_info["nome"], dest_id, "", p_a, "")
                else:
                    rep_d = st.session_state.pop("reply_alvo", None)
                    enviar_msg_grupo(gid_ativo, c_ativo, uid_atual, user_info["nome"], cargo_global, "", p_a, "", rep_d)
                st.rerun()

        # ==========================================
        # MENU FLUTUANTE '@' (MEMBROS & CAPACIDADES DO BOT)
        # ==========================================
        col_arr1, col_arr2 = st.columns([1.2, 4.8])
        with col_arr1:
            with st.popover("@ Mencionar", width="stretch"):
                st.caption("MEMBROS")
                for m_uid, m_dados in usuarios.items():
                    if m_uid == "omnix_bot":
                        continue
                    cm_a, cm_b, cm_c = st.columns([0.7, 2.5, 1.8])
                    if m_dados.get("avatar") and Path(m_dados["avatar"]).exists():
                        cm_a.image(m_dados["avatar"], width=28)
                    else:
                        cm_a.write("👤")
                    if cm_b.button(f"{m_dados['nome']}", key=f"at_m_{m_uid}", width="stretch"):
                        if st.session_state["modo_pulse"] == "dm":
                            salvar_mensagem_dm(uid_atual, user_info["nome"], dest_id, f"@{m_uid} 👋")
                        else:
                            enviar_msg_grupo(gid_ativo, c_ativo, uid_atual, user_info["nome"], cargo_global, f"@{m_uid} 👋")
                        st.rerun()
                    cm_c.caption(f"@{m_uid}")

                st.divider()
                st.caption("🤖 CAPACIDADES DO @OMNIX BOT")
                with st.expander("🤖 @omnix — Ver todas as opções e automações", expanded=True):
                    caps = [
                        ("baixar", "@omnix baixar <link>", "Baixa vídeo MP4 para o Drive"),
                        ("mp3", "@omnix mp3 <link>", "Extrai música MP3 do YouTube"),
                        ("figurinha", "@omnix figurinha <nome>", "Cria sticker com imagem anexada"),
                        ("converter", "@omnix converter", "Converte imagem anexada"),
                        ("horario", "@omnix horario", "Consulta horário dinâmico"),
                        ("pergunta", "@omnix <pergunta>", "Conversa com Inteligência Artificial")
                    ]
                    for tipo_c, cmd_txt, desc_txt in caps:
                        cc1, cc2 = st.columns([2.2, 2.8])
                        if cc1.button(cmd_txt, key=f"cap_{tipo_c}", width="stretch"):
                            if tipo_c == "horario":
                                if st.session_state["modo_pulse"] == "dm":
                                    salvar_mensagem_dm(uid_atual, user_info["nome"], dest_id, "@omnix horario")
                                    r_t, r_f = processar_comando_bot("@omnix horario", user_info["nome"])
                                    salvar_mensagem_dm("omnix_bot", "OMNIX Bot", dest_id, r_t)
                                else:
                                    enviar_msg_grupo(gid_ativo, c_ativo, uid_atual, user_info["nome"], cargo_global, "@omnix horario")
                                    r_t, r_f = processar_comando_bot("@omnix horario", user_info["nome"])
                                    enviar_msg_grupo(gid_ativo, c_ativo, "omnix_bot", "OMNIX Bot", "bot", r_t)
                            else:
                                st.session_state["bot_cmd_pendente"] = tipo_c
                            st.rerun()
                        cc2.caption(desc_txt)

        # Caixa Interativa que abre quando o usuário clica em um comando que precisa de complemento
        if "bot_cmd_pendente" in st.session_state and st.session_state["bot_cmd_pendente"]:
            tipo_p = st.session_state["bot_cmd_pendente"]
            with st.container(border=True):
                titulos_p = {
                    "baixar": "📥 Cole o link do vídeo para o @omnix baixar em MP4:",
                    "mp3": "🎵 Cole o link do YouTube para o @omnix extrair o MP3:",
                    "figurinha": "🎭 Envie a imagem e digite o nome da nova figurinha:",
                    "converter": "🔄 Envie a imagem e escolha o formato de conversão:",
                    "pergunta": "🤖 Digite sua pergunta para o @omnix Bot:"
                }
                st.markdown(f"**{titulos_p.get(tipo_p, 'Complete o comando:')}**")
                
                comp_txt = ""
                comp_img = None
                fmt_conv_p = "PNG"

                qual_chat_p = "720p"
                if tipo_p == "baixar":
                    cu1, cu2 = st.columns([2.6, 1.4])
                    comp_txt = cu1.text_input("URL / Link:", placeholder="https://...", key="in_comp_url")
                    qual_chat_p = cu2.selectbox("Qualidade:", ["1080p", "720p", "480p", "360p"], index=1, key="in_comp_qual")
                elif tipo_p == "mp3":
                    comp_txt = st.text_input("URL / Link:", placeholder="https://...", key="in_comp_url")
                elif tipo_p == "pergunta":
                    comp_txt = st.text_input("Sua pergunta:", placeholder="Ex: Me recomende 3 jogos leves...", key="in_comp_perg")
                elif tipo_p == "figurinha":
                    c_f1, c_f2 = st.columns([2, 1.5])
                    comp_img = c_f1.file_uploader("Imagem/GIF:", type=["png", "jpg", "jpeg", "webp", "gif"], key="in_comp_fig_img")
                    comp_txt = c_f2.text_input("Nome da figurinha:", placeholder="ex: mito", key="in_comp_fig_nom")
                elif tipo_p == "converter":
                    c_v1, c_v2 = st.columns([2.2, 1.3])
                    comp_img = c_v1.file_uploader("Imagem:", type=["png", "jpg", "jpeg", "webp", "heic"], key="in_comp_cv_img")
                    fmt_conv_p = c_v2.selectbox("Formato:", ["PNG", "JPG", "WEBP"], key="in_comp_cv_fmt")

                cb_ok, cb_canc = st.columns([3, 1])
                if cb_ok.button("🚀 Executar Comando", type="primary", width="stretch"):
                    p_anx_cmd = salvar_anexo_chat(comp_img, uid_atual) if comp_img else ""
                    if tipo_p == "converter":
                        cmd_final = f"@omnix converter {fmt_conv_p.lower()}"
                    elif tipo_p == "pergunta":
                        cmd_final = f"@omnix {comp_txt.strip()}"
                    else:
                        cmd_final = f"@omnix baixar {qual_chat_p} {comp_txt.strip()}" if tipo_p == "baixar" else f"@omnix {tipo_p} {comp_txt.strip()}"

                    del st.session_state["bot_cmd_pendente"]
                    if st.session_state["modo_pulse"] == "dm":
                        salvar_mensagem_dm(uid_atual, user_info["nome"], dest_id, cmd_final, p_anx_cmd)
                        with st.spinner("🤖 OMNIX Bot processando..."):
                            r_t, r_f = processar_comando_bot(cmd_final, user_info["nome"], p_anx_cmd)
                            salvar_mensagem_dm("omnix_bot", "OMNIX Bot", dest_id, r_t, "", r_f)
                    else:
                        enviar_msg_grupo(gid_ativo, c_ativo, uid_atual, user_info["nome"], cargo_global, cmd_final, p_anx_cmd)
                        with st.spinner("🤖 OMNIX Bot processando..."):
                            r_t, r_f = processar_comando_bot(cmd_final, user_info["nome"], p_anx_cmd)
                            enviar_msg_grupo(gid_ativo, c_ativo, "omnix_bot", "OMNIX Bot", "bot", r_t, "", r_f)
                    st.rerun()

                if cb_canc.button("Cancelar", width="stretch"):
                    del st.session_state["bot_cmd_pendente"]
                    st.rerun()

        placeholder_chat = f"Enviar mensagem para {dest_info['nome']}..." if st.session_state["modo_pulse"] == "dm" else f"Transmitir em ◈ {c_ativo}..."
        txt_env = st.chat_input(placeholder_chat, key="input_pulse_chat")
        if txt_env and txt_env.strip():
            texto_f = txt_env.strip()
            fig_d = st.session_state.pop("figurinha_engatilhada", None)
            emj_p = fig_d["caminho"] if fig_d else ""
            if not emj_p and emojis_salvos:
                for cod, edata in emojis_salvos.items():
                    if f":{cod}:" in texto_f:
                        emj_p = edata["caminho"]
                        texto_f = texto_f.replace(f":{cod}:", "").strip()
                        break
            if st.session_state["modo_pulse"] == "dm":
                salvar_mensagem_dm(uid_atual, user_info["nome"], dest_id, texto_f, "", emj_p)
                if "@omnix" in texto_f.lower():
                    with st.spinner("🤖 OMNIX Bot pensando..."):
                        perg = texto_f.lower().replace("@omnix", "").strip() or texto_f
                        resp_bot = processar_comando_bot(perg, user_info["nome"])
                        salvar_mensagem_dm("omnix_bot", "OMNIX Bot", dest_id, resp_bot)
            else:
                rep_d = st.session_state.pop("reply_alvo", None)
                enviar_msg_grupo(gid_ativo, c_ativo, uid_atual, user_info["nome"], cargo_global, texto_f, "", emj_p, rep_d)
                if "@omnix" in texto_f.lower():
                    with st.spinner("🤖 OMNIX Bot pensando..."):
                        hist_c = carregar_grupos().get(gid_ativo, {}).get("canais", {}).get(c_ativo, [])
                        perg = texto_f.lower().replace("@omnix", "").strip() or texto_f
                        resp_bot = processar_comando_bot(perg, user_info["nome"], hist_c)
                        enviar_msg_grupo(gid_ativo, c_ativo, "omnix_bot", "OMNIX Bot", "bot", resp_bot)
            st.rerun()















