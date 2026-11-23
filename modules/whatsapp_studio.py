import io
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageOps
import streamlit as st

def gerar_figurinha_whatsapp(arquivo_bytes: bytes, nome_arquivo: str, formato_recorte: str = "quadrado") -> tuple[bool, bytes, str]:
    """
    Converte Imagem estática ou GIF animado para o padrão oficial de Figurinha do WhatsApp:
    - Dimensão exata: 512x512 px
    - Formato: WEBP (estático < 100 KB ou animado < 500 KB)
    """
    ext = Path(nome_arquivo).suffix.lower()
    base_dir = Path(__file__).resolve().parent.parent
    ffmpeg_exe = str(base_dir / "venv" / "Scripts" / "ffmpeg.exe")
    if not Path(ffmpeg_exe).exists():
        ffmpeg_exe = "ffmpeg"

    # 1. FIGURINHA ANIMADA (GIF ou Vídeo curto -> WEBP Animado 512x512 para WhatsApp)
    if ext in (".gif", ".mp4", ".webm"):
        with tempfile.TemporaryDirectory() as tmp:
            in_path = Path(tmp) / f"in{ext}"
            out_webp = Path(tmp) / "sticker_animado.webp"
            in_path.write_bytes(arquivo_bytes)

            # Converte para WEBP animado 512x512, 15fps, máx 6 segundos, otimizado para WhatsApp (<500KB)
            vf = "fps=15,scale=512:512:force_original_aspect_ratio=decrease,pad=512:512:(ow-iw)/2:(oh-ih)/2:color=0x00000000"
            for q in ("65", "45", "30"):
                cmd = [
                    ffmpeg_exe, "-y", "-t", "6", "-i", str(in_path),
                    "-vf", vf, "-vcodec", "libwebp", "-lossless", "0",
                    "-compression_level", "4", "-q:v", q, "-loop", "0",
                    "-preset", "default", "-an", str(out_webp)
                ]
                subprocess.run(cmd, capture_output=True)
                if out_webp.exists() and out_webp.stat().st_size <= 490 * 1024:
                    break

            if out_webp.exists():
                return True, out_webp.read_bytes(), f"Figurinha Animada WhatsApp pronta ({out_webp.stat().st_size / 1024:.1f} KB)"
            return False, b"", "Não foi possível converter o GIF/vídeo para figurinha animada."

    # 2. FIGURINHA ESTÁTICA (PNG/JPG/WEBP -> WEBP 512x512 < 100 KB)
    try:
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(arquivo_bytes))).convert("RGBA")
        if formato_recorte == "preencher":
            im = ImageOps.fit(im, (512, 512), Image.Resampling.LANCZOS)
        else:
            im.thumbnail((512, 512), Image.Resampling.LANCZOS)
            tela = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
            tela.paste(im, ((512 - im.width) // 2, (512 - im.height) // 2), im)
            im = tela

        buf = io.BytesIO()
        for qual in (85, 70, 55, 40):
            buf = io.BytesIO()
            im.save(buf, format="WEBP", quality=qual, method=6)
            if len(buf.getvalue()) <= 98 * 1024:
                break

        dados_out = buf.getvalue()
        return True, dados_out, f"Figurinha WhatsApp pronta ({len(dados_out) / 1024:.1f} KB • 512x512 px)"
    except Exception as e:
        return False, b"", f"Erro ao gerar figurinha: {e}"

def converter_arquivo_universal(arquivo_bytes: bytes, nome_origem: str, formato_destino: str) -> tuple[bool, bytes, str]:
    """Converte imagens (PNG, JPG, WEBP, ICO, PDF), áudios (MP3, WAV, OGG) e vídeos (MP4, GIF)."""
    ext_orig = Path(nome_origem).suffix.lower()
    fmt = formato_destino.lower()
    stem = Path(nome_origem).stem
    base_dir = Path(__file__).resolve().parent.parent
    ffmpeg_exe = str(base_dir / "venv" / "Scripts" / "ffmpeg.exe")
    if not Path(ffmpeg_exe).exists():
        ffmpeg_exe = "ffmpeg"

    # Conversões de Imagem (incluindo exportar para PDF ou ICO)
    if ext_orig in (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".ico") and fmt in ("png", "jpg", "webp", "bmp", "ico", "pdf"):
        im = ImageOps.exif_transpose(Image.open(io.BytesIO(arquivo_bytes)))
        buf = io.BytesIO()
        if fmt in ("jpg", "pdf"):
            im = im.convert("RGB")
        if fmt == "ico":
            im.thumbnail((256, 256), Image.Resampling.LANCZOS)
            im.save(buf, format="ICO")
        elif fmt == "pdf":
            im.save(buf, format="PDF")
        else:
            pil_fmt = "JPEG" if fmt == "jpg" else fmt.upper()
            im.save(buf, format=pil_fmt, quality=92)
        return True, buf.getvalue(), f"{stem}_omnix.{fmt}"

    # Conversões de Áudio e Vídeo via FFmpeg
    with tempfile.TemporaryDirectory() as tmp:
        in_p = Path(tmp) / f"in{ext_orig}"
        out_p = Path(tmp) / f"{stem}_omnix.{fmt}"
        in_p.write_bytes(arquivo_bytes)
        cmd = [ffmpeg_exe, "-y", "-i", str(in_p), str(out_p)]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0 and out_p.exists():
            return True, out_p.read_bytes(), out_p.name
    return False, b"", "Conversão não suportada para esta combinação."
