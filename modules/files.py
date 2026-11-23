import streamlit as st
from modules.image_viewer import abrir_modal_imagem
from pathlib import Path
from modules.social import criar_post_permanente

def render_files(storage_dir: Path, cargo: str):
    if "drive_subpasta" not in st.session_state:
        st.session_state["drive_subpasta"] = ""

    pasta_atual = storage_dir / st.session_state["drive_subpasta"]
    pasta_atual.mkdir(parents=True, exist_ok=True)
    caminho_exibicao = f"OMNIX Drive / {st.session_state['drive_subpasta']}".rstrip(" /")

    top1, top2 = st.columns([3.5, 1.5])
    with top1:
        st.subheader("📂 OMNIX Drive")
        st.caption(f"📍 Caminho atual: `{caminho_exibicao}`")
    with top2:
        with st.popover("⬆️ Enviar Arquivos", width="stretch"):
            ups = st.file_uploader("Selecione os arquivos:", accept_multiple_files=True, key="drive_up_clean")
            if ups and st.button("Salvar no Drive", type="primary", width="stretch"):
                for u in ups:
                    (pasta_atual / u.name).write_bytes(u.getbuffer())
                st.rerun()
            st.divider()
            nova_p = st.text_input("Nova pasta:")
            if nova_p.strip() and st.button("📁 Criar Pasta", width="stretch"):
                (pasta_atual / nova_p.strip()).mkdir(exist_ok=True)
                st.rerun()

    if st.session_state["drive_subpasta"]:
        if st.button("⬅️ Voltar para raiz do Drive"):
            st.session_state["drive_subpasta"] = ""
            st.rerun()

    f1, f2, f3, f4 = st.columns([2.5, 1.3, 1.3, 1.1])
    busca = f1.text_input("Pesquisar:", placeholder="🔍 Filtrar por nome...", label_visibility="collapsed").strip().lower()
    tipo_f = f2.selectbox("Tipo:", ["Todos", "Imagens", "Vídeos", "Áudios", "Documentos"], label_visibility="collapsed")
    ordem = f3.selectbox("Ordenar:", ["Mais recentes", "Nome (A-Z)", "Maior tamanho"], label_visibility="collapsed")
    modo_vis = f4.radio("Visão:", ["Grade", "Lista"], horizontal=True, label_visibility="collapsed")

    itens = list(pasta_atual.iterdir())
    pastas = [i for i in itens if i.is_dir() and (not busca or busca in i.name.lower())]
    arquivos = [i for i in itens if i.is_file() and (not busca or busca in i.name.lower())]

    ext_map = {
        "Imagens": (".png", ".jpg", ".jpeg", ".webp", ".gif"),
        "Vídeos": (".mp4", ".webm", ".mkv", ".mov"),
        "Áudios": (".mp3", ".wav", ".m4a", ".ogg"),
        "Documentos": (".pdf", ".txt", ".docx", ".xlsx", ".zip")
    }
    if tipo_f != "Todos":
        arquivos = [a for a in arquivos if a.suffix.lower() in ext_map[tipo_f]]

    if ordem == "Mais recentes":
        arquivos.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    elif ordem == "Nome (A-Z)":
        arquivos.sort(key=lambda x: x.name.lower())
    else:
        arquivos.sort(key=lambda x: x.stat().st_size, reverse=True)

    if pastas:
        st.caption("PASTAS")
        cols_p = st.columns(min(len(pastas), 4))
        for idx, p in enumerate(pastas):
            if cols_p[idx % 4].button(f"📁 {p.name}", key=f"open_dir_{p.name}", width="stretch"):
                st.session_state["drive_subpasta"] = p.name
                st.rerun()

    if not arquivos and not pastas:
        st.info("Esta pasta está vazia. Clique em **⬆️ Enviar Arquivos** no topo para adicionar itens.")
    elif arquivos:
        st.caption(f"ARQUIVOS ({len(arquivos)})")
        if modo_vis == "Grade":
            cols = st.columns(3)
            for idx, arq in enumerate(arquivos):
                with cols[idx % 3]:
                    with st.container(border=True):
                        c_tit, c_menu = st.columns([4, 1])
                        c_tit.markdown(f"**{arq.name[:24]}**")
                        with c_menu.popover("⋮"):
                            st.download_button("⬇️ Baixar", data=arq.read_bytes(), file_name=arq.name, key=f"dl_g_{arq.name}", width="stretch")
                            novo_n = st.text_input("Novo nome:", value=arq.name, key=f"rn_in_g_{arq.name}")
                            if st.button("✏️ Renomear", key=f"rn_bt_g_{arq.name}", width="stretch"):
                                if novo_n.strip():
                                    arq.rename(pasta_atual / novo_n.strip())
                                    st.rerun()
                            if arq.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
                                if st.button("🌐 Compartilhar no Feed", key=f"sh_g_{arq.name}", width="stretch"):
                                    criar_post_permanente(st.session_state.usuario_id, "Membro", f"Compartilhado do Drive: {arq.name}", arq.open("rb"))
                                    st.success("Publicado no Feed!")
                            if st.button("🗑️ Excluir", key=f"del_g_{arq.name}", width="stretch"):
                                arq.unlink(missing_ok=True)
                                st.rerun()

                        if arq.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp", ".gif"):
                            st.image(str(arq), width="stretch")
                            if st.button("🔍 Abrir / Baixar", key=f"open_drv_{arq.name}", width="stretch"):
                                abrir_modal_imagem(str(arq), arq.name)
                        else:
                            icone = "🎬" if arq.suffix.lower() in (".mp4", ".webm", ".mkv") else ("🎵" if arq.suffix.lower() in (".mp3", ".wav") else "📄")
                            st.markdown(f"<div style='font-size:2.4rem; text-align:center; padding:12px 0;'>{icone}</div>", unsafe_allow_html=True)

                        mb = arq.stat().st_size / (1024 * 1024)
                        st.caption(f"{arq.suffix.upper().replace('.', '')} • `{mb:.2f} MB`")
        else:
            for arq in arquivos:
                with st.container(border=True):
                    cl1, cl2, cl3, cl4 = st.columns([3.5, 1, 1.2, 0.6])
                    cl1.write(f"📄 **{arq.name}**")
                    cl2.caption(arq.suffix.upper().replace(".", ""))
                    cl3.caption(f"{arq.stat().st_size / (1024*1024):.2f} MB")
                    with cl4.popover("⋮"):
                        st.download_button("⬇️ Baixar", data=arq.read_bytes(), file_name=arq.name, key=f"dl_l_{arq.name}", width="stretch")
                        novo_n = st.text_input("Renomear:", value=arq.name, key=f"rn_in_l_{arq.name}")
                        if st.button("Salvar Nome", key=f"rn_bt_l_{arq.name}", width="stretch"):
                            if novo_n.strip():
                                arq.rename(pasta_atual / novo_n.strip())
                                st.rerun()
                        if st.button("🗑️ Excluir", key=f"del_l_{arq.name}", width="stretch"):
                            arq.unlink(missing_ok=True)
                            st.rerun()

    todos_arqs = [f for f in storage_dir.rglob("*") if f.is_file()]
    uso_mb = sum(f.stat().st_size for f in todos_arqs) / (1024 * 1024)
    st.markdown(
        f"<div style='margin-top:16px; padding:8px 14px; border-radius:10px; background:rgba(255,255,255,0.02); "
        f"border:1px solid rgba(148,163,184,0.1); color:#94A3B8; font-size:0.82rem; display:flex; justify-content:space-between;'>"
        f"<span>💾 Armazenamento utilizado no OMNIX Drive: <b>{uso_mb:.2f} MB</b></span>"
        f"<span>Total de itens: <b>{len(todos_arqs)}</b></span></div>",
        unsafe_allow_html=True
    )

