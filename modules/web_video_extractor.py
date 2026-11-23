import re
import subprocess
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

def baixar_midia_universal_completa(url: str, pasta_destino: Path, modo: str = "video", qualidade: str = "720") -> tuple[bool, str, Path | None]:
    """
    modo: 'video', 'audio', 'imagem'
    Retorna: (sucesso, mensagem, caminho_arquivo_baixado)
    """
    pasta_destino.mkdir(parents=True, exist_ok=True)
    base_dir = Path(__file__).resolve().parent.parent
    ytdlp_exe = str(base_dir / "venv" / "Scripts" / "yt-dlp.exe")
    ffmpeg_dir = str(base_dir / "venv" / "Scripts")
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    # MODO IMAGEM UNIVERSAL POR LINK
    if modo == "imagem":
        try:
            req = urllib.request.Request(url, headers={"User-Agent": ua})
            resp = urllib.request.urlopen(req, timeout=20)
            ctype = resp.headers.get("Content-Type", "").lower()
            dados = resp.read()

            # Se o link já aponta diretamente para uma imagem
            if "image/" in ctype or any(url.lower().split("?")[0].endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")):
                ext = ".png"
                if "jpeg" in ctype or "jpg" in url.lower(): ext = ".jpg"
                elif "webp" in ctype or "webp" in url.lower(): ext = ".webp"
                elif "gif" in ctype or "gif" in url.lower(): ext = ".gif"
                nome_limpo = re.sub(r'[^a-zA-Z0-9_-]', '_', Path(urlparse(url).path).stem)[:40] or "imagem_web"
                arq_out = pasta_destino / f"{nome_limpo}{ext}"
                arq_out.write_bytes(dados)
                return True, f"Imagem baixada com sucesso ({arq_out.name})!", arq_out

            # Se o link é de uma página web, extrai a maior imagem principal (og:image ou <img>)
            html = dados.decode("utf-8", errors="ignore")
            og = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.IGNORECASE)
            imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE)
            candidatos_img = ([og.group(1)] if og else []) + imgs
            for img_src in candidatos_img:
                full_img = urljoin(url, img_src)
                if not full_img.startswith("http"):
                    continue
                try:
                    r_im = urllib.request.urlopen(urllib.request.Request(full_img, headers={"User-Agent": ua}), timeout=12)
                    b_im = r_im.read()
                    if len(b_im) > 8000:  # ignora ícones minúsculos
                        ext_im = ".webp" if ".webp" in full_img.lower() else (".png" if ".png" in full_img.lower() else (".gif" if ".gif" in full_img.lower() else ".jpg"))
                        arq_out = pasta_destino / f"web_img_{abs(hash(full_img)) % 100000}{ext_im}"
                        arq_out.write_bytes(b_im)
                        return True, f"Imagem extraída da página ({arq_out.name})!", arq_out
                except Exception:
                    continue
            return False, "Nenhuma imagem compatível encontrada neste link.", None
        except Exception as e:
            return False, f"Falha ao baixar imagem: {e}", None

    # MODO VÍDEO OU ÁUDIO UNIVERSAL
    antes_arqs = set(pasta_destino.iterdir())
    saida_tpl = str(pasta_destino / "%(title).55s.%(ext)s")

    def _rodar_yt(alvo: str, ref: str = "", prefixo: str = "") -> bool:
        dest = str(pasta_destino / f"{prefixo}.%(ext)s") if prefixo else saida_tpl
        cmd_base = [ytdlp_exe, "--user-agent", ua, "--no-check-certificates", "--ffmpeg-location", ffmpeg_dir, "--no-playlist"]
        if ref:
            cmd_base += ["--referer", ref]
        if modo == "audio":
            cmd = cmd_base + ["-x", "--audio-format", "mp3", "-o", dest, alvo]
        else:
            fmt = f"bestvideo[height<={qualidade}][ext=mp4]+bestaudio[ext=m4a]/best[height<={qualidade}][ext=mp4]/best"
            cmd = cmd_base + ["-f", fmt, "--merge-output-format", "mp4", "--remux-video", "mp4", "-o", dest, alvo]
        return subprocess.run(cmd, capture_output=True, text=True, creationflags=flags).returncode == 0

    if _rodar_yt(url):
        novos = sorted(set(pasta_destino.iterdir()) - antes_arqs, key=lambda x: x.stat().st_mtime, reverse=True)
        return True, "Download concluído com sucesso!", (novos[0] if novos else None)

    # Varredura HTML / Iframes
    candidatos = []
    try:
        html = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua}), timeout=15).read().decode("utf-8", errors="ignore")
        for lk in re.findall(r'https?://[^\s"\'<>]+?\.(?:mp4|m3u8|webm)(?:\?[^\s"\'<>]*)?', html, re.IGNORECASE):
            if lk not in candidatos: candidatos.append(lk)
        for s in re.findall(r'<(?:video|source|iframe)[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE):
            full = urljoin(url, s)
            if full.startswith("http") and full not in candidatos: candidatos.append(full)
    except Exception:
        pass

    for i, c in enumerate(candidatos):
        if _rodar_yt(c, ref=url, prefixo=f"midia_web_{i+1}"):
            novos = sorted(set(pasta_destino.iterdir()) - antes_arqs, key=lambda x: x.stat().st_mtime, reverse=True)
            return True, "Mídia extraída da página web!", (novos[0] if novos else None)

    return False, "Não foi possível extrair mídia pública deste endereço.", None

def baixar_video_universal_web(url: str, pasta_destino: Path, qualidade: str = "720", apenas_audio: bool = False) -> tuple[bool, str]:
    ok, msg, _ = baixar_midia_universal_completa(url, pasta_destino, modo=("audio" if apenas_audio else "video"), qualidade=qualidade)
    return ok, msg
