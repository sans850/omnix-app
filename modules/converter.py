import streamlit as st
import subprocess
from pathlib import Path
from PIL import Image, ImageOps
import pillow_heif

pillow_heif.register_heif_opener()

def render_converter(storage_dir: Path):
    st.subheader("🔄 Conversor Universal")
    st.caption("Converta imagens, áudios e vídeos de forma unificada escolhendo entre processamento local instantâneo ou servidor.")

    pasta_conv = storage_dir / "Convertidos"
    pasta_conv.mkdir(parents=True, exist_ok=True)

    categoria = st.radio("Categoria:", ["🖼️ Imagens", "🎵 Áudio", "🎬 Vídeo"], horizontal=True, label_visibility="collapsed")

    with st.container(border=True):
        if categoria == "🖼️ Imagens":
            arquivo = st.file_uploader("Arraste ou selecione uma imagem:", type=["png", "jpg", "jpeg", "webp", "bmp", "heic"], key="cv_img_u")
            c1, c2 = st.columns(2)
            fmt_saida = c1.selectbox("Formato de saída:", ["PNG", "JPG", "WEBP"])
            modalidade = c2.radio(
                "Modalidade de processamento:",
                ["Servidor OMNIX (Salva no Drive)", "Local no Navegador (Zero peso no servidor)"],
                help="Local processa direto no seu aparelho; Servidor salva uma cópia no OMNIX Drive."
            )
            with st.expander("⚙️ Configurações adicionais", expanded=False):
                qualidade = st.slider("Qualidade de compressão (%):", 50, 100, 90)

            if modalidade == "Local no Navegador (Zero peso no servidor)":
                st.iframe("""
                <div style="font-family:sans-serif; background:#090D16; color:#F8FAFC; padding:14px; border-radius:10px; border:1px solid #7C3AED;">
                    <input type="file" id="fIn" accept="image/*" style="color:white; margin-bottom:10px;"><br>
                    <select id="fmt" style="padding:8px; border-radius:8px; background:#111827; color:white; border:1px solid #7C3AED;">
                        <option value="image/png">PNG</option>
                        <option value="image/jpeg">JPG</option>
                        <option value="image/webp">WEBP</option>
                    </select>
                    <button onclick="runConv()" style="padding:8px 16px; margin-left:8px; border-radius:8px; border:none; background:#7C3AED; color:white; font-weight:bold; cursor:pointer;">Converter Localmente</button>
                    <div id="out" style="margin-top:10px;"></div>
                </div>
                <script>
                function runConv(){
                    const f = document.getElementById('fIn').files;
                    if(!f) return alert("Selecione uma imagem.");
                    const fmt = document.getElementById('fmt').value;
                    const ext = fmt.split('/');
                    const r = new FileReader();
                    r.onload = e => {
                        const img = new Image();
                        img.onload = () => {
                            const c = document.createElement('canvas');
                            c.width = img.width; c.height = img.height;
                            const ctx = c.getContext('2d');
                            if(fmt==='image/jpeg'){ ctx.fillStyle='#FFF'; ctx.fillRect(0,0,c.width,c.height); }
                            ctx.drawImage(img,0,0);
                            const a = document.createElement('a');
                            a.href = c.toDataURL(fmt, 0.9);
                            a.download = "convertido." + ext;
                            a.innerText = "⬇️ Baixar Arquivo (" + ext.toUpperCase() + ")";
                            a.style = "display:inline-block; padding:8px 14px; background:#7C3AED; color:white; border-radius:8px; text-decoration:none; font-weight:bold;";
                            document.getElementById('out').innerHTML = "";
                            document.getElementById('out').appendChild(a);
                        };
                        img.src = e.target.result;
                    };
                    r.readAsDataURL(f);
                }
                </script>
                """, height=160)
            else:
                if st.button("Converter Imagem", type="primary", width="stretch"):
                    if not arquivo:
                        st.warning("Selecione uma imagem acima.")
                    else:
                        arquivo.seek(0)
                        img = ImageOps.exif_transpose(Image.open(arquivo))
                        ext = "jpg" if fmt_saida == "JPG" else fmt_saida.lower()
                        pil_f = "JPEG" if ext == "jpg" else fmt_saida
                        if pil_f == "JPEG":
                            img = img.convert("RGB")
                        dest = pasta_conv / f"{Path(arquivo.name).stem}_conv.{ext}"
                        img.save(dest, format=pil_f, quality=qualidade)
                        st.session_state["ultimo_conv_path"] = str(dest)

        elif categoria == "🎵 Áudio":
            arquivo = st.file_uploader("Arraste ou selecione um áudio/vídeo:", type=["mp3", "wav", "ogg", "m4a", "mp4"], key="cv_aud_u")
            fmt_a = st.selectbox("Formato de saída:", ["MP3", "WAV", "OGG"])
            if st.button("Converter Áudio", type="primary", width="stretch"):
                if not arquivo:
                    st.warning("Selecione um arquivo.")
                else:
                    tmp_in = pasta_conv / f"in_{arquivo.name}"
                    tmp_in.write_bytes(arquivo.getbuffer())
                    dest = pasta_conv / f"{Path(arquivo.name).stem}_conv.{fmt_a.lower()}"
                    with st.spinner("Convertendo áudio..."):
                        subprocess.run(["ffmpeg", "-y", "-i", str(tmp_in), str(dest)], capture_output=True)
                        tmp_in.unlink(missing_ok=True)
                        if dest.exists():
                            st.session_state["ultimo_conv_path"] = str(dest)

        else:
            arquivo = st.file_uploader("Arraste ou selecione um vídeo:", type=["mp4", "mkv", "avi", "mov", "webm"], key="cv_vid_u")
            fmt_v = st.selectbox("Formato de saída:", ["MP4", "WEBM", "GIF"])
            if st.button("Converter Vídeo", type="primary", width="stretch"):
                if not arquivo:
                    st.warning("Selecione um vídeo.")
                else:
                    tmp_in = pasta_conv / f"in_{arquivo.name}"
                    tmp_in.write_bytes(arquivo.getbuffer())
                    dest = pasta_conv / f"{Path(arquivo.name).stem}_conv.{fmt_v.lower()}"
                    with st.spinner("Processando vídeo..."):
                        subprocess.run(["ffmpeg", "-y", "-i", str(tmp_in), str(dest)], capture_output=True)
                        tmp_in.unlink(missing_ok=True)
                        if dest.exists():
                            st.session_state["ultimo_conv_path"] = str(dest)

    if "ultimo_conv_path" in st.session_state and Path(st.session_state["ultimo_conv_path"]).exists():
        res_p = Path(st.session_state["ultimo_conv_path"])
        with st.container(border=True):
            cr1, cr2 = st.columns([3, 1.3])
            cr1.success(f"✅ Arquivo convertido: **{res_p.name}** (`{res_p.stat().st_size / (1024*1024):.2f} MB`)")
            cr2.download_button("⬇️ Baixar Arquivo", data=res_p.read_bytes(), file_name=res_p.name, type="primary", width="stretch")

    convs = sorted([f for f in pasta_conv.glob("*") if f.is_file()], key=lambda x: x.stat().st_mtime, reverse=True)
    with st.expander(f"🕒 Histórico de conversões ({len(convs)})", expanded=False):
        for c in convs:
            st.caption(f"📄 {c.name} — `{c.stat().st_size / (1024*1024):.2f} MB`")

