import streamlit as st
import subprocess
from pathlib import Path

def obter_info_link(url: str) -> dict:
    cmd = ["yt-dlp", "--no-playlist", "--print", "%(title)s | %(duration_string)s", url]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        if res.returncode == 0 and res.stdout.strip():
            linha = next(iter(res.stdout.strip().splitlines()), "")
            partes = linha.split("|")
            return {
                "titulo": next(iter(partes), "Mídia identificada").strip(),
                "duracao": partes[-1].strip() if len(partes) > 1 else "--:--"
            }
    except Exception:
        pass
    return {"titulo": "Link pronto para download", "duracao": "--:--"}

def render_media(storage_dir: Path):
    st.subheader("🎬 Central de Mídia")
    st.caption("Baixe vídeos ou extraia áudios e reproduza diretamente na plataforma.")

    pasta_midia = storage_dir / "Media_Downloads"
    pasta_midia.mkdir(parents=True, exist_ok=True)

    col_dl, col_play = st.columns([1.15, 1.35])

    # CARTÃO 1: DOWNLOAD DE MÍDIA
    with col_dl:
        with st.container(border=True):
            st.markdown("#### 📥 Download de mídia")
            url = st.text_input("Link:", placeholder="https://youtube.com...", label_visibility="collapsed")
            
            if url.strip():
                if st.session_state.get("last_checked_url") != url.strip():
                    st.session_state["last_checked_url"] = url.strip()
                    st.session_state["last_checked_info"] = obter_info_link(url.strip())
                info = st.session_state.get("last_checked_info", {})
                st.caption(f"🎯 **{info.get('titulo', '')}** • Duração: `{info.get('duracao', '--:--')}`")

            c_fmt, c_qual = st.columns(2)
            formato = c_fmt.selectbox("Formato:", ["Vídeo (MP4)", "Áudio (MP3)"])
            qualidade = c_qual.selectbox("Qualidade:", ["1080p", "720p", "480p", "360p"], index=1, disabled=(formato == "Áudio (MP3)"))

            if st.button("⬇️ Baixar Mídia", type="primary", width="stretch"):
                if not url.strip():
                    st.warning("Insira um link válido acima.")
                else:
                    saida = str(pasta_midia / "%(title).50s.%(ext)s")
                    if formato == "Áudio (MP3)":
                        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "--ffmpeg-location", "venv/Scripts", "--merge-output-format", "mp4", "--remux-video", "mp4", "--no-playlist", "-o", saida, url.strip()]
                    else:
                        alt = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}[qualidade]
                        cmd = ["yt-dlp", "-f", f"bestvideo[height<={alt}][ext=mp4]+bestaudio[ext=m4a]/best[height<={alt}][ext=mp4]/best", "--ffmpeg-location", "venv/Scripts", "--merge-output-format", "mp4", "--remux-video", "mp4", "--no-playlist", "-o", saida, url.strip()]
                    with st.spinner("Baixando mídia..."):
                        res = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
                        if res.returncode == 0:
                            st.success("Download concluído!")
                            st.rerun()
                        else:
                            st.error("Não foi possível baixar este link.")

    # CARTÃO 2: REPRODUTOR DE MÍDIA
    arquivos_midia = sorted(
        [f for f in storage_dir.rglob("*") if f.is_file() and f.suffix.lower() in (".mp4", ".webm", ".mkv", ".mp3", ".wav", ".m4a")],
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    with col_play:
        with st.container(border=True):
            st.markdown("#### ▶️ Reprodutor de mídia")
            if not arquivos_midia:
                st.info("Nenhuma mídia baixada ainda. Faça um download ao lado para reproduzir aqui.")
            else:
                arq_sel = st.selectbox(
                    "Arquivo:",
                    options=arquivos_midia,
                    format_func=lambda f: f"{f.name} ({f.stat().st_size / (1024*1024):.1f} MB)",
                    label_visibility="collapsed"
                )
                if arq_sel:
                    if arq_sel.suffix.lower() in (".mp3", ".wav", ".m4a"):
                        st.audio(str(arq_sel))
                    else:
                        st.video(str(arq_sel))

    # HISTÓRICO RECOLHÍVEL ABAIXO
    with st.expander(f"🕒 Histórico de downloads ({len(arquivos_midia)})", expanded=False):
        if not arquivos_midia:
            st.caption("Nenhum arquivo registrado no histórico.")
        else:
            for f in arquivos_midia:
                ch1, ch2 = st.columns([4.5, 0.8])
                ch1.write(f"📄 **{f.name}** — `{f.stat().st_size / (1024*1024):.2f} MB`")
                if ch2.button("🗑️", key=f"del_med_{f.name}", help="Excluir"):
                    f.unlink(missing_ok=True)
                    st.rerun()



