import re
import subprocess
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

def baixar_video_universal_web(url: str, pasta_destino: Path, qualidade: str = "720", apenas_audio: bool = False) -> tuple[bool, str]:
    pasta_destino.mkdir(parents=True, exist_ok=True)
    base_dir = Path(__file__).resolve().parent.parent
    ytdlp_exe = str(base_dir / "venv" / "Scripts" / "yt-dlp.exe")
    ffmpeg_dir = str(base_dir / "venv" / "Scripts")
    saida_tpl = str(pasta_destino / "%(title).55s.%(ext)s")
    flags = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

    def _tentar_ytdlp(alvo_url: str, referer: str = "", nome_custom: str = "") -> bool:
        destino = str(pasta_destino / f"{nome_custom}.%(ext)s") if nome_custom else saida_tpl
        base_cmd = [ytdlp_exe, "--user-agent", ua, "--no-check-certificates", "--ffmpeg-location", ffmpeg_dir, "--no-playlist"]
        if referer:
            base_cmd += ["--referer", referer]
        if apenas_audio:
            cmd = base_cmd + ["-x", "--audio-format", "mp3", "-o", destino, alvo_url]
        else:
            fmt = f"bestvideo[height<={qualidade}][ext=mp4]+bestaudio[ext=m4a]/best[height<={qualidade}][ext=mp4]/best"
            cmd = base_cmd + ["-f", fmt, "--merge-output-format", "mp4", "--remux-video", "mp4", "-o", destino, alvo_url]
        res = subprocess.run(cmd, capture_output=True, text=True, creationflags=flags)
        return res.returncode == 0

    # CAMADA 1: Extração direta via yt-dlp
    if _tentar_ytdlp(url):
        return True, "Download concluído com sucesso!"

    # CAMADA 2: Varredura de HTML e Iframes incorporados
    candidatos = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": ua})
        html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", errors="ignore")

        for lk in re.findall(r'https?://[^\s"\'<>]+?\.(?:mp4|m3u8|mpd|webm)(?:\?[^\s"\'<>]*)?', html, re.IGNORECASE):
            if lk not in candidatos:
                candidatos.append(lk)

        for s in re.findall(r'<(?:video|source)[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE):
            full = urljoin(url, s)
            if full not in candidatos:
                candidatos.append(full)

        for ifr in re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.IGNORECASE):
            full_ifr = urljoin(url, ifr)
            if full_ifr.startswith("http") and full_ifr not in candidatos:
                candidatos.append(full_ifr)
    except Exception:
        pass

    for idx, cand in enumerate(candidatos):
        if _tentar_ytdlp(cand, referer=url, nome_custom=f"midia_web_{idx+1}"):
            return True, "Vídeo extraído da página e salvo em MP4!"

    # CAMADA 3: Interceptação de Rede Real com Navegador Headless + Auto-Play
    streams_rede = []
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=ua)
            page = context.new_page()

            def on_resp(r):
                u_r = r.url
                ctype = r.headers.get("content-type", "").lower()
                if any(ext in u_r.lower() for ext in (".m3u8", ".mp4", ".mpd", ".webm")) or "mpegurl" in ctype or "video/" in ctype:
                    if u_r not in streams_rede and not u_r.endswith(".ts"):
                        streams_rede.append(u_r)

            page.on("response", on_resp)
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(2500)

            # Tenta clicar em elementos de vídeo/play para disparar o carregamento do stream
            try:
                vid_el = page.locator("video, [class*='play'], [aria-label*='Play']").first
                if vid_el.count() > 0:
                    vid_el.click(timeout=2000, force=True)
            except Exception:
                pass

            page.wait_for_timeout(4500)
            browser.close()
    except Exception:
        pass

    for idx, st_url in enumerate(streams_rede):
        if _tentar_ytdlp(st_url, referer=url, nome_custom=f"stream_capturado_{idx+1}"):
            return True, "Stream interceptado com sucesso e unido em MP4!"

    return False, "Não foi possível extrair vídeo público (página sem mídia ou protegida por DRM/login)."
