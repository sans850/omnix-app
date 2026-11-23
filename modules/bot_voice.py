import streamlit as st
import re
import json
import subprocess
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps
import pillow_heif
from google import genai
from modules.vision import carregar_api_key
from modules.discord_extra import salvar_emoji_custom

pillow_heif.register_heif_opener()

AUDIO_CHAT_DIR = Path("omnix_audio_chat")
AUDIO_CHAT_DIR.mkdir(exist_ok=True)
STORAGE_DIR = Path("omnix_storage")
STORAGE_DIR.mkdir(exist_ok=True)
BOT_CHAT_FILE = Path("bot_conversas.json")

def salvar_audio_gravado(audio_file, uid: str) -> str:
    if audio_file is None:
        return ""
    ts = int(datetime.now().timestamp() * 1000)
    caminho = AUDIO_CHAT_DIR / f"voz_{uid}_{ts}.wav"
    audio_file.seek(0)
    caminho.write_bytes(audio_file.read())
    return str(caminho)

def consultar_info_midia(url: str, altura_max: int = 720, apenas_audio: bool = False) -> str:
    fmt = "bestaudio/best" if apenas_audio else f"bestvideo[height<={altura_max}]+bestaudio/best[height<={altura_max}]/best"
    cmd = ["yt-dlp", "-f", fmt, "--no-playlist", "--print", "%(title)s | %(filesize,filesize_approx)s", url]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if res.returncode == 0 and res.stdout.strip():
            linha = next(iter(res.stdout.strip().splitlines()), "")
            partes = linha.split("|")
            titulo = next(iter(partes), "Vídeo").strip()
            tam_raw = partes[-1].strip() if len(partes) > 1 else "NA"
            peso_mb = f"{int(tam_raw) / (1024 * 1024):.1f} MB" if tam_raw.isdigit() else "Tamanho variável"
            return f"🎬 **{titulo}** • Peso estimado: `{peso_mb}`"
    except Exception:
        pass
    return "⚠️ Não foi possível estimar o peso antes do download."

def _baixar_midia_automatico(url: str, apenas_audio: bool = False, altura_max: int = 720) -> tuple[bool, str]:
    pasta_dest = STORAGE_DIR / ("Bot_Musicas" if apenas_audio else "Bot_Videos")
    pasta_dest.mkdir(parents=True, exist_ok=True)
    antes = set(pasta_dest.glob("*"))
    saida = str(pasta_dest / "%(title).50s.%(ext)s")
    if apenas_audio:
        cmd = ["yt-dlp", "-x", "--audio-format", "mp3", "--ffmpeg-location", "venv/Scripts", "--merge-output-format", "mp4", "--remux-video", "mp4", "--no-playlist", "-o", saida, url]
    else:
        fmt_str = f"bestvideo[height<={altura_max}][ext=mp4]+bestaudio[ext=m4a]/best[height<={altura_max}][ext=mp4]/best[height<={altura_max}]/best"
        cmd = ["yt-dlp", "-f", fmt_str, "--ffmpeg-location", "venv/Scripts", "--merge-output-format", "mp4", "--remux-video", "mp4", "--no-playlist", "-o", saida, url]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        if res.returncode == 0:
            novos = list(set(pasta_dest.glob("*")) - antes)
            arq = next(iter(novos), None)
            peso_txt = f" (`{arq.stat().st_size / (1024*1024):.2f} MB`)" if arq else ""
            return True, f"✅ Download concluído e salvo em **{pasta_dest.name}**{peso_txt}."
        return False, "❌ Não foi possível baixar este link."
    except Exception as e:
        return False, f"❌ Erro no download: {e}"

def _converter_imagem_automatico(caminho_img: str, formato_alvo: str) -> tuple[bool, str]:
    p = Path(caminho_img)
    if not p.exists():
        return False, "❌ Imagem não encontrada."
    pasta_conv = STORAGE_DIR / "Bot_Convertidos"
    pasta_conv.mkdir(parents=True, exist_ok=True)
    fmt = formato_alvo.upper()
    ext = "jpg" if fmt in ("JPG", "JPEG") else fmt.lower()
    pil_fmt = "JPEG" if ext == "jpg" else fmt
    destino = pasta_conv / f"{p.stem}_conv.{ext}"
    img = ImageOps.exif_transpose(Image.open(p))
    if pil_fmt == "JPEG":
        img = img.convert("RGB")
    img.save(destino, format=pil_fmt, quality=90)
    return True, f"🔄 Convertido para **{fmt}** e salvo em **Bot_Convertidos** (`{destino.name}`)."

class _ArquivoSimulado:
    def __init__(self, caminho: Path):
        self.name = caminho.name
        self._bytes = caminho.read_bytes()
    def seek(self, pos: int): pass
    def read(self) -> bytes: return self._bytes

def processar_comando_bot(texto_bruto: str, autor_nome: str, anexo_path: str = "", contexto_recente: list = None, modo_direto: bool = False) -> tuple[str, str]:
    limpo = re.sub(r'@omnix', '', texto_bruto, flags=re.IGNORECASE).strip()
    lower = limpo.lower()

    if lower in ("", "ajuda", "help", "comandos", "?"):
        return (
            "🤖 **Capacidades do OMNIX IA:**\n"
            "• `baixar <link>` — Baixa vídeo MP4 para o Drive.\n"
            "• `mp3 <link>` — Extrai áudio MP3.\n"
            "• `figurinha <nome>` — Cria figurinha a partir de uma imagem.\n"
            "• `converter png/jpg/webp` — Converte imagem.\n"
            "• `horario` — Consulta o horário atual do servidor.",
            ""
        )

    if any(k in lower for k in ["horario", "horário", "hora", "time"]):
        return f"🕒 **Horário atual:** `{datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}`", ""

    url_match = re.search(r'(https?://[^\s]+)', limpo)
    if url_match and any(k in lower for k in ["baixar", "download", "mp3", "audio", "áudio", "musica", "música", "video", "vídeo"]):
        url = url_match.group(1)
        eh_mp3 = any(k in lower for k in ["mp3", "audio", "áudio", "musica", "música"])
        alt = 1080 if "1080" in lower else (480 if "480" in lower else (360 if "360" in lower else 720))
        _, msg_dl = _baixar_midia_automatico(url, apenas_audio=eh_mp3, altura_max=alt)
        return msg_dl, ""

    if any(k in lower for k in ["figurinha", "sticker", "emoji"]) and anexo_path and Path(anexo_path).exists():
        palavras = [p for p in re.sub(r'(figurinha|sticker|emoji|criar|fazer)', '', lower).split() if p.isalnum()]
        cod = next(iter(palavras), f"fig{int(datetime.now().timestamp()) % 10000}")
        ok_f, msg_f = salvar_emoji_custom(cod, _ArquivoSimulado(Path(anexo_path)), autor_nome)
        if ok_f:
            cam = str(Path("omnix_emojis") / (f"emoji_{cod}.gif" if anexo_path.endswith(".gif") else f"emoji_{cod}.png"))
            return f"✨ Figurinha **`:{cod}:`** criada com sucesso:", cam
        return f"⚠️ {msg_f}", ""

    if any(k in lower for k in ["converter", "para png", "para jpg", "para webp"]) and anexo_path and Path(anexo_path).exists():
        fmt = "JPG" if ("jpg" in lower or "jpeg" in lower) else ("WEBP" if "webp" in lower else "PNG")
        _, msg_cv = _converter_imagem_automatico(anexo_path, fmt)
        return msg_cv, ""

    api_key = carregar_api_key()
    if not api_key:
        return "⚠️ Chave Gemini API não configurada no módulo Vision.", ""
    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(model="gemini-2.5-flash", contents=f"Responda em português de forma clara e objetiva para {autor_nome}: {limpo}")
        return resp.text, ""
    except Exception as e:
        return f"❌ Erro na IA: {e}", ""

def carregar_historico_bot(uid: str) -> list:
    if not BOT_CHAT_FILE.exists():
        return []
    try:
        return json.loads(BOT_CHAT_FILE.read_text(encoding="utf-8")).get(uid.strip().lower(), [])
    except Exception:
        return []

def salvar_msg_historico_bot(uid: str, autor: str, texto: str, figurinha_path: str = ""):
    dados = json.loads(BOT_CHAT_FILE.read_text(encoding="utf-8")) if BOT_CHAT_FILE.exists() else {}
    u = uid.strip().lower()
    dados.setdefault(u, []).append({"autor": autor, "texto": texto, "figurinha": figurinha_path, "hora": datetime.now().strftime("%d/%m %H:%M")})
    dados[u] = dados[u][-60:]
    BOT_CHAT_FILE.write_text(json.dumps(dados, indent=4, ensure_ascii=False), encoding="utf-8")

def render_bot_hub(usuario_id: str, user_info: dict):
    uid = usuario_id.strip().lower()
    nome_u = user_info["nome"]
    api_ativa = bool(carregar_api_key())

    with st.container(border=True):
        ch1, ch2, ch3 = st.columns([2.8, 1.6, 1.2])
        ch1.markdown("#### 🤖 OMNIX IA")
        estado_txt = "🟢 Online • Pronto" if api_ativa else "🟡 Modo Automação (Sem API)"
        ch2.markdown(f"<div style='padding-top:6px; font-size:0.85rem; color:#94A3B8;'>{estado_txt}</div>", unsafe_allow_html=True)
        with ch3.popover("🕒 Histórico", width="stretch"):
            hist_p = carregar_historico_bot(uid)
            st.caption(f"{len(hist_p)} mensagens registradas")
            if st.button("🗑️ Limpar Conversa", width="stretch"):
                d = json.loads(BOT_CHAT_FILE.read_text(encoding="utf-8")) if BOT_CHAT_FILE.exists() else {}
                d[uid] = []
                BOT_CHAT_FILE.write_text(json.dumps(d, indent=4, ensure_ascii=False), encoding="utf-8")
                st.rerun()

    with st.expander("⚡ Automações rápidas (Download, Figurinhas & Conversão)", expanded=False):
        t_dl, t_fig, t_conv = st.tabs(["📥 Baixar Mídia", "🎭 Criar Figurinha", "🔄 Converter Imagem"])
        with t_dl:
            c1, c2, c3 = st.columns([2.5, 1.1, 1.3])
            link_dl = c1.text_input("Link:", placeholder="https://...", key="b_l_clean")
            tipo_dl = c2.selectbox("Tipo:", ["Vídeo MP4", "Áudio MP3"], key="b_t_clean")
            qual_dl = c3.selectbox("Qualidade:", ["1080p", "720p", "480p", "360p"], index=1, disabled=(tipo_dl == "Áudio MP3"), key="b_q_clean")
            alt_s = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}.get(qual_dl, 720)
            b_est, b_go = st.columns(2)
            if b_est.button("🔍 Estimar Peso", width="stretch") and link_dl.strip():
                st.info(consultar_info_midia(link_dl.strip(), alt_s, apenas_audio=(tipo_dl == "Áudio MP3")))
            if b_go.button("⬇️ Baixar Agora", type="primary", width="stretch") and link_dl.strip():
                cmd = f"{'mp3' if tipo_dl == 'Áudio MP3' else f'baixar {alt_s}p'} {link_dl.strip()}"
                salvar_msg_historico_bot(uid, nome_u, f"Solicitação: {tipo_dl} ({qual_dl})")
                with st.spinner("Processando..."):
                    r, f = processar_comando_bot(cmd, nome_u, modo_direto=True)
                    salvar_msg_historico_bot(uid, "OMNIX IA", r, f)
                st.rerun()

        with t_fig:
            cf1, cf2 = st.columns([2.5, 1.5])
            img_f = cf1.file_uploader("Imagem/GIF:", type=["png", "jpg", "jpeg", "webp", "gif"], key="b_f_up")
            nom_f = cf2.text_input("Código:", placeholder="ex: mito", key="b_f_nm")
            if st.button("✨ Criar Figurinha", type="primary", width="stretch") and img_f and nom_f.strip():
                tp = Path("omnix_chat_media") / f"t_{int(datetime.now().timestamp())}_{img_f.name}"
                tp.parent.mkdir(exist_ok=True); img_f.seek(0); tp.write_bytes(img_f.read())
                r, f = processar_comando_bot(f"figurinha {nom_f.strip()}", nome_u, str(tp), modo_direto=True)
                tp.unlink(missing_ok=True)
                salvar_msg_historico_bot(uid, "OMNIX IA", r, f)
                st.rerun()

        with t_conv:
            cc1, cc2 = st.columns([2.8, 1.2])
            img_c = cc1.file_uploader("Imagem:", type=["png", "jpg", "jpeg", "webp", "heic"], key="b_c_up")
            fmt_c = cc2.selectbox("Para:", ["PNG", "JPG", "WEBP"], key="b_c_fm")
            if st.button("🔄 Converter", type="primary", width="stretch") and img_c:
                tc = Path("omnix_chat_media") / f"tc_{int(datetime.now().timestamp())}_{img_c.name}"
                tc.parent.mkdir(exist_ok=True); img_c.seek(0); tc.write_bytes(img_c.read())
                r, f = processar_comando_bot(f"converter {fmt_c.lower()}", nome_u, str(tc), modo_direto=True)
                tc.unlink(missing_ok=True)
                salvar_msg_historico_bot(uid, "OMNIX IA", r, f)
                st.rerun()

    if user_info.get("cargo") == "admin":
        from modules.admin_skills import render_habilidades_admin_bot
        with st.expander("🛡️ Ferramentas de Diagnóstico Admin", expanded=False):
            render_habilidades_admin_bot(usuario_id)

    hist = carregar_historico_bot(uid)
    box = st.container(height=400, border=True)
    with box:
        if not hist:
            st.info("Olá! Como posso ajudar hoje? Digite sua pergunta abaixo ou abra as automações acima.")
        else:
            for item in hist:
                eh_bot = (item["autor"] == "OMNIX IA")
                with st.chat_message("assistant" if eh_bot else "user", avatar="🤖" if eh_bot else "👤"):
                    st.markdown(f"**{item['autor']}** • *{item['hora']}*")
                    st.markdown(item["texto"])
                    if item.get("figurinha") and Path(item["figurinha"]).exists():
                        st.image(item["figurinha"], width=128)

    msg_in = st.chat_input("Envie uma mensagem para o OMNIX IA...", key="in_omnix_ia_clean")
    if msg_in and msg_in.strip():
        salvar_msg_historico_bot(uid, nome_u, msg_in.strip())
        with st.spinner("Processando..."):
            r, f = processar_comando_bot(msg_in.strip(), nome_u, modo_direto=True)
            salvar_msg_historico_bot(uid, "OMNIX IA", r, f)
        st.rerun()



