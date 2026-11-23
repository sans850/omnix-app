import streamlit as st
from pathlib import Path
from modules.web_video_extractor import baixar_midia_universal_completa
from modules.whatsapp_studio import gerar_figurinha_whatsapp, converter_arquivo_universal
from modules.safety_lock import obter_config_trava

def render_studio_hub():
    cfg = obter_config_trava()
    trava_on = cfg.get("ativa", True)
    qual_max = "720" if trava_on else "1080"

    st.markdown("### 🧰 Estúdio Universal OMNIX")
    st.caption("Baixe vídeos, músicas e imagens por link, converta arquivos e crie figurinhas estáticas ou animadas para WhatsApp.")

    tab_dl, tab_conv, tab_wpp = st.tabs([
        "🌐 Baixar Vídeos, Músicas e Imagens",
        "🔄 Conversor Universal de Arquivos",
        "💚 Figurinhas WhatsApp (Imagens & GIFs)"
    ])

    # 1. DOWNLOADER UNIVERSAL POR LINK
    with tab_dl:
        st.markdown("#### Baixar Mídia Universal por Link")
        st.caption("Cole o link direto ou da página de qualquer vídeo, música ou imagem da web.")
        url_in = st.text_input("Cole o link aqui:", placeholder="https://...", key="studio_dl_url")
        c1, c2 = st.columns([1.4, 1.6])
        tipo_dl = c1.selectbox(
            "Tipo de mídia:",
            ["Vídeo (MP4 com som)", "Música / Áudio (MP3)", "Imagem (PNG / JPG / WEBP / GIF)"],
            key="studio_dl_tipo"
        )
        if c2.button("⬇️ Extrair e Baixar Agora", type="primary", use_container_width=True, key="studio_dl_btn"):
            if not url_in.strip():
                st.warning("Cole um link válido primeiro.")
            else:
                modo = "imagem" if "Imagem" in tipo_dl else ("audio" if "Música" in tipo_dl else "video")
                dest = Path("omnix_storage") / "Universal_Downloads"
                with st.spinner("Extraindo mídia do link..."):
                    ok, msg, arq_path = baixar_midia_universal_completa(url_in.strip(), dest, modo=modo, qualidade=qual_max)
                if ok and arq_path and arq_path.exists():
                    st.success(msg)
                    if modo == "imagem":
                        st.image(str(arq_path), width=260)
                    st.download_button(
                        label=f"📥 Salvar '{arq_path.name}' no Meu Aparelho",
                        data=arq_path.read_bytes(),
                        file_name=arq_path.name,
                        use_container_width=True,
                        key="studio_dl_save"
                    )
                else:
                    st.error(msg)

    # 2. CONVERSOR UNIVERSAL DE ARQUIVOS
    with tab_conv:
        st.markdown("#### Conversor Universal de Arquivos")
        st.caption("Converta imagens (PNG, JPG, WEBP, ICO, PDF), áudios (MP3, WAV, OGG) e vídeos (MP4, WEBM, GIF).")
        up_file = st.file_uploader(
            "Escolha o arquivo para converter:",
            type=["png", "jpg", "jpeg", "webp", "bmp", "ico", "mp3", "wav", "ogg", "m4a", "mp4", "webm", "gif"],
            key="studio_conv_up"
        )
        if up_file:
            ext_u = Path(up_file.name).suffix.lower()
            if ext_u in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".ico"):
                opcoes_fmt = ["PNG", "JPG", "WEBP", "PDF", "ICO", "BMP"]
            elif ext_u in (".mp3", ".wav", ".ogg", ".m4a"):
                opcoes_fmt = ["MP3", "WAV", "OGG"]
            else:
                opcoes_fmt = ["MP4", "GIF", "MP3", "WEBM"]

            fmt_dest = st.selectbox("Converter para:", opcoes_fmt, key="studio_conv_fmt")
            if st.button("⚡ Converter Arquivo", type="primary", key="studio_conv_btn"):
                with st.spinner("Convertendo arquivo..."):
                    ok_c, bytes_out, nome_out = converter_arquivo_universal(up_file.getvalue(), up_file.name, fmt_dest)
                if ok_c:
                    st.success(f"Convertido com sucesso: **{nome_out}**")
                    st.download_button(
                        f"⬇️ Baixar {nome_out}",
                        data=bytes_out,
                        file_name=nome_out,
                        use_container_width=True,
                        key="studio_conv_save"
                    )
                else:
                    st.error(nome_out)

    # 3. CRIADOR DE FIGURINHAS WHATSAPP (ESTÁTICAS + GIFS ANIMADOS)
    with tab_wpp:
        st.markdown("#### Criador de Figurinhas para WhatsApp (Estáticas & Animadas)")
        st.caption("Gera arquivos .WEBP no padrão oficial 512x512 px do WhatsApp a partir de fotos, GIFs animados ou vídeos curtos.")
        up_wpp = st.file_uploader(
            "Envie uma Imagem (PNG/JPG/WEBP) ou GIF/Vídeo curto:",
            type=["png", "jpg", "jpeg", "webp", "gif", "mp4"],
            key="studio_wpp_up"
        )
        ajuste = st.radio(
            "Enquadramento da imagem:",
            ["Manter proporção (fundo transparente)", "Preencher quadrado 512x512"],
            horizontal=True,
            key="studio_wpp_fit"
        )
        if up_wpp and st.button("💚 Gerar Figurinha WhatsApp (.WEBP)", type="primary", key="studio_wpp_btn"):
            modo_rec = "preencher" if "Preencher" in ajuste else "quadrado"
            with st.spinner("Otimizando figurinha no padrão oficial do WhatsApp..."):
                ok_w, bytes_w, msg_w = gerar_figurinha_whatsapp(up_wpp.getvalue(), up_wpp.name, formato_recorte=modo_rec)
            if ok_w:
                st.success(msg_w)
                c_prev, c_dl = st.columns()
                c_prev.image(bytes_w, width=160)
                nome_stk = f"{Path(up_wpp.name).stem}_whatsapp.webp"
                c_dl.download_button(
                    label="📥 Baixar Figurinha WhatsApp (.WEBP)",
                    data=bytes_w,
                    file_name=nome_stk,
                    mime="image/webp",
                    use_container_width=True,
                    key="studio_wpp_save"
                )
                c_dl.caption("💡 No celular, basta abrir o arquivo `.webp` baixado usando um app como *Sticker Maker* ou importar direto no WhatsApp Web/Desktop.")
            else:
                st.error(msg_w)
