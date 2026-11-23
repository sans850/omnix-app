import streamlit as st
import streamlit.components.v1 as components
import base64
from modules.discord_extra import salvar_emoji_custom

def render_client_studio_ferramentas(usuario_id: str):
    tab_fig, tab_player = st.tabs(["🎨 Estúdio de Figurinhas (No Seu Aparelho)", "🎬 Player Rápido Local (Hardware do Aparelho)"])

    with tab_fig:
        st.caption("O recorte, redimensionamento e compressão rodam 100% no chip gráfico do seu celular ou PC.")
        html_fig = """
        <div style="background:#141C2B; border:1px solid #283449; border-radius:12px; padding:18px; font-family:sans-serif; color:#F1F2F8;">
          <div style="display:flex; gap:18px; flex-wrap:wrap; align-items:center;">
            <div style="flex:1; min-width:220px;">
              <label style="display:block; font-weight:600; margin-bottom:6px; font-size:13px;">1. Escolha uma foto do seu aparelho:</label>
              <input type="file" id="figFile" accept="image/*" style="background:#182235; color:#F1F2F8; border:1px solid #283449; padding:8px; border-radius:8px; width:100%; box-sizing:border-box; margin-bottom:12px;">

              <label style="display:block; font-weight:600; margin-bottom:6px; font-size:13px;">2. Formato do recorte:</label>
              <select id="figShape" onchange="desenharFigurinha()" style="background:#182235; color:#F1F2F8; border:1px solid #283449; padding:8px; border-radius:8px; width:100%; margin-bottom:12px;">
                <option value="square">Quadrado Arredondado</option>
                <option value="circle">Redondo (Circular)</option>
              </select>

              <a id="btnBaixarFig" style="display:none; background:#7655F5; color:#FFFFFF; text-decoration:none; padding:10px 18px; border-radius:8px; font-weight:700; font-size:13px; text-align:center;">
                ⬇️ Baixar Figurinha Pronta (.PNG)
              </a>
            </div>

            <div style="text-align:center; background:#090D16; border:1px solid #283449; border-radius:10px; padding:14px; min-width:170px;">
              <div style="font-size:11px; color:#929CAF; margin-bottom:8px;">Pré-visualização (128x128)</div>
              <canvas id="figCanvas" width="128" height="128" style="background:#101725; border-radius:8px;"></canvas>
              <div id="figMeta" style="font-size:11px; color:#35C98A; margin-top:6px;">Aguardando imagem...</div>
            </div>
          </div>
        </div>

        <script>
        let imgCarregada = null;
        document.getElementById('figFile').addEventListener('change', function(e) {
          const f = e.target.files;
          if (!f) return;
          const r = new FileReader();
          r.onload = function(ev) {
            const im = new Image();
            im.onload = function() { imgCarregada = im; desenharFigurinha(); };
            im.src = ev.target.result;
          };
          r.readAsDataURL(f);
        });

        function desenharFigurinha() {
          if (!imgCarregada) return;
          const cv = document.getElementById('figCanvas');
          const ctx = cv.getContext('2d');
          const shape = document.getElementById('figShape').value;
          ctx.clearRect(0, 0, 128, 128);
          ctx.save();
          if (shape === 'circle') {
            ctx.beginPath();
            ctx.arc(64, 64, 62, 0, Math.PI * 2);
            ctx.closePath();
            ctx.clip();
          }
          const minSide = Math.min(imgCarregada.width, imgCarregada.height);
          const sx = (imgCarregada.width - minSide) / 2;
          const sy = (imgCarregada.height - minSide) / 2;
          ctx.drawImage(imgCarregada, sx, sy, minSide, minSide, 0, 0, 128, 128);
          ctx.restore();

          cv.toBlob(function(blob) {
            const url = URL.createObjectURL(blob);
            const btn = document.getElementById('btnBaixarFig');
            btn.href = url;
            btn.download = 'figurinha_omnix.png';
            btn.style.display = 'inline-block';
            document.getElementById('figMeta').innerText = 'Pronta! ' + (blob.size / 1024).toFixed(1) + ' KB';
          }, 'image/png');
        }
        </script>
        """
        components.html(html_fig, height=280)

    with tab_player:
        st.caption("Abre vídeos, músicas e imagens direto da memória do seu aparelho sem gastar internet nem pesar no servidor.")
        html_player = """
        <div style="background:#141C2B; border:1px solid #283449; border-radius:12px; padding:18px; font-family:sans-serif; color:#F1F2F8;">
          <input type="file" id="localMediaInput" accept="video/*,audio/*,image/*" style="background:#182235; color:#F1F2F8; border:1px solid #283449; padding:10px; border-radius:8px; width:100%; box-sizing:border-box; margin-bottom:14px;">
          <div id="mediaStage" style="text-align:center; background:#090D16; border-radius:10px; padding:12px; min-height:80px; display:flex; align-items:center; justify-content:center; color:#929CAF; font-size:13px;">
            Selecione qualquer vídeo, música ou foto do seu celular/PC para reproduzir instantaneamente.
          </div>
        </div>
        <script>
        document.getElementById('localMediaInput').addEventListener('change', function(e) {
          const file = e.target.files;
          if (!file) return;
          const url = URL.createObjectURL(file);
          const stage = document.getElementById('mediaStage');
          if (file.type.startsWith('video/')) {
            stage.innerHTML = `<video src="${url}" controls autoplay playsinline style="max-width:100%; max-height:360px; border-radius:8px;"></video>`;
          } else if (file.type.startsWith('audio/')) {
            stage.innerHTML = `<div style="width:100%;"><div style="margin-bottom:8px; color:#F1F2F8; font-weight:600;">🎵 ${file.name}</div><audio src="${url}" controls autoplay style="width:100%;"></audio></div>`;
          } else if (file.type.startsWith('image/')) {
            stage.innerHTML = `<img src="${url}" style="max-width:100%; max-height:360px; border-radius:8px;">`;
          }
        });
        </script>
        """
        components.html(html_player, height=460)
