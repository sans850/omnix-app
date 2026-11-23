import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps
import pillow_heif
from google import genai

pillow_heif.register_heif_opener()

VISION_CFG = Path("vision_config.json")
VISION_HIST = Path("vision_historico.json")

def carregar_api_key() -> str:
    if VISION_CFG.exists():
        try:
            return json.loads(VISION_CFG.read_text(encoding="utf-8")).get("api_key", "")
        except Exception:
            pass
    return ""

def salvar_api_key(chave: str):
    VISION_CFG.write_text(json.dumps({"api_key": chave.strip()}, indent=4), encoding="utf-8")

def salvar_historico_vision(titulo: str, resumo: str):
    lista = []
    if VISION_HIST.exists():
        try:
            lista = json.loads(VISION_HIST.read_text(encoding="utf-8"))
        except Exception:
            lista = []
    lista.insert(0, {"titulo": titulo, "resumo": resumo, "hora": datetime.now().strftime("%d/%m %H:%M")})
    VISION_HIST.write_text(json.dumps(lista[:20], indent=4, ensure_ascii=False), encoding="utf-8")

def analisar_imagem_estruturada(img: Image.Image, api_key: str) -> dict:
    prompt = (
        "Analise esta imagem com precisão e responda estritamente em JSON válido com as 4 chaves abaixo (em português):\n"
        '{"personagens": "Identificação de personagens, pessoas, obras ou elementos principais", '
        '"descricao": "Descrição visual detalhada do cenário, cores e composição", '
        '"textos": "Transcrição exata de qualquer texto visível na imagem (ou Nenhum texto encontrado)", '
        '"interpretacao": "Contexto, significado ou interpretação geral da cena"}'
    )
    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(model="gemini-2.5-flash", contents=[img, prompt])
    txt = resp.text.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        return json.loads(txt)
    except Exception:
        return {"personagens": "Análise concluída", "descricao": resp.text, "textos": "-", "interpretacao": "-"}

def render_vision(cargo: str):
    st.subheader("👁️ OMNIX Vision IA")
    st.caption("Envie uma imagem para identificar personagens, extrair textos e interpretar detalhes visuais.")

    api_key = carregar_api_key()
    if cargo == "admin":
        with st.expander("🔑 Configurar Chave API Gemini (Admin)", expanded=(not bool(api_key))):
            nova_k = st.text_input("Gemini API Key:", value=api_key, type="password")
            if st.button("Salvar Chave", type="primary"):
                salvar_api_key(nova_k)
                st.success("Chave salva!")
                st.rerun()

    if not api_key:
        st.warning("A chave Gemini API ainda não foi configurada pelo administrador.")
        return

    _, col_up, _ = st.columns([0.8, 2.4, 0.8])
    with col_up:
        img_file = st.file_uploader("Arraste ou selecione uma imagem para análise:", type=["png", "jpg", "jpeg", "webp", "heic"], key="vis_clean_up")

    if img_file:
        img_file.seek(0)
        img_pil = ImageOps.exif_transpose(Image.open(img_file)).convert("RGB")
        
        col_esq, col_dir = st.columns([1.15, 1.85])
        with col_esq:
            with st.container(border=True):
                st.image(img_pil, caption=img_file.name, width="stretch")
                if st.button("✨ Analisar Imagem", type="primary", width="stretch"):
                    with st.spinner("Processando análise visual..."):
                        res = analisar_imagem_estruturada(img_pil, api_key)
                        st.session_state["vision_res_atual"] = res
                        st.session_state["vision_img_nome"] = img_file.name
                        salvar_historico_vision(img_file.name, res.get("descricao", "")[:140])

        with col_dir:
            res_atual = st.session_state.get("vision_res_atual")
            if res_atual and st.session_state.get("vision_img_nome") == img_file.name:
                with st.container(border=True):
                    t1, t2, t3, t4 = st.tabs(["🎭 Personagens", "🖼️ Descrição", "📝 Textos (OCR)", "🧠 Interpretação"])
                    t1.write(res_atual.get("personagens", "-"))
                    t2.write(res_atual.get("descricao", "-"))
                    t3.write(res_atual.get("textos", "-"))
                    t4.write(res_atual.get("interpretacao", "-"))

                perg_extra = st.text_input("💬 Fazer pergunta adicional sobre esta imagem:", placeholder="Ex: Qual o modelo desse objeto ou episódio?")
                if perg_extra.strip() and st.button("Perguntar sobre a imagem", width="stretch"):
                    with st.spinner("Consultando IA..."):
                        client = genai.Client(api_key=api_key)
                        r_ex = client.models.generate_content(model="gemini-2.5-flash", contents=[img_pil, perg_extra.strip()])
                        st.info(r_ex.text)
            else:
                st.info("Clique em **✨ Analisar Imagem** ao lado para visualizar os resultados detalhados aqui.")

    hist_v = json.loads(VISION_HIST.read_text(encoding="utf-8")) if VISION_HIST.exists() else []
    with st.expander(f"🕒 Histórico de análises anteriores ({len(hist_v)})", expanded=False):
        if not hist_v:
            st.caption("Nenhuma análise salva ainda.")
        else:
            for item in hist_v:
                st.markdown(f"**{item['titulo']}** *({item['hora']})* — {item['resumo']}...")

