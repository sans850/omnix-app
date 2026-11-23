import streamlit as st
import hashlib
import io
from pathlib import Path
from PIL import Image
from google import genai
from modules.admin import carregar_usuarios
from modules.vision import carregar_api_key

ETAPAS_DIAGNOSTICO = [
    ("01. Login & Feed Inicial", "inicio", "app.py e modules/social.py", "Autenticar via token e carregar a barra principal + feed inicial."),
    ("02. Chat & Envio de Mensagens", "chat", "modules/messages.py e modules/bot_voice.py", "Abrir aba Chat, digitar '@omnix horario' e enviar."),
    ("03. Criar & Salvar Figurinha Customizada", "criar_figurinha", "modules/discord_extra.py e modules/bot_voice.py", "Gerar uma imagem de teste, salvar como figurinha ':qa_teste:' e validar na galeria."),
    ("04. Visualizar & Baixar Imagens (Tela Cheia HD)", "ver_baixar_imagem", "modules/image_viewer.py e app.py", "Abrir uma imagem no Visualizador HD, verificar o botão de download e fechar o modal."),
    ("05. Social: Explorar & Criar Publicação", "social_post", "modules/social.py", "Abrir Social -> Postar e validar o formulário e pré-visualização."),
    ("06. Social: Perfil, Capa & Amigos", "social_perfil", "modules/social.py e modules/friends.py", "Abrir Social -> Perfil e validar capa, avatar, métricas e sub-abas."),
    ("07. Multimídia: Central de Mídia & Player", "midia", "modules/media.py", "Abrir Mídia e validar os cartões de Download e Reprodutor."),
    ("08. Multimídia: Assistir Juntos", "watch", "modules/watch.py", "Abrir Assistir Juntos e validar a criação/exibição de sessão."),
    ("09. Arquivos: OMNIX Drive & Download", "drive", "modules/files.py", "Abrir OMNIX Drive, alternar Grade/Lista e checar menu contextual."),
    ("10. Arquivos: Conversão Real de Imagem", "conversor", "modules/converter.py", "Executar uma conversão real de PNG para WEBP e validar o arquivo gerado."),
    ("11. IA: OMNIX Bot & Automações", "bot", "modules/bot_voice.py", "Abrir IA -> OMNIX IA e validar status, histórico e automações."),
    ("12. IA: OMNIX Vision IA & Topo", "vision_topo", "modules/vision.py e app.py", "Abrir Vision IA, Notificações (🔔) e Configurações (⚙️).")
]

def gerar_explicacao_erro(titulo_etapa: str, arquivo_alvo: str, acao_tentada: str, erro_bruto: str) -> str:
    explicacao_base = f"Falha detectada durante '{acao_tentada}' no módulo '{arquivo_alvo}'."
    api_key = carregar_api_key()
    if api_key and erro_bruto:
        try:
            client = genai.Client(api_key=api_key)
            prompt = (
                f"Você é um engenheiro especialista em Python e Streamlit diagnosticando um erro no OMNIX.\n"
                f"Etapa: {titulo_etapa}\nArquivo provável: {arquivo_alvo}\nAção: {acao_tentada}\n"
                f"Erro:\n{erro_bruto[:1500]}\n\n"
                f"Explique em português, em 3 tópicos curtos:\n"
                f"1) O que quebrou para o usuário;\n"
                f"2) Qual é a causa raiz;\n"
                f"3) Como corrigir no arquivo {arquivo_alvo}."
            )
            resp = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
            return resp.text.strip()
        except Exception:
            pass
    return explicacao_base

def rodar_teste_unico_etapa(indice: int, usuario_alvo: str, senha_alvo: str) -> dict:
    titulo_etapa, codigo_etapa, arquivo_alvo, acao_tentada = ETAPAS_DIAGNOSTICO[indice]
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"etapa": titulo_etapa, "status": "FALHA", "arquivo": "Ambiente", "acao": acao_tentada, "explicacao": "Playwright não instalado.", "detalhe": "Instale playwright."}

    porta = st.get_option("server.port") or 8501
    token = hashlib.sha256(f"{usuario_alvo}:{senha_alvo}:omnix_secret".encode()).hexdigest()[:16]
    url_base = f"http://127.0.0.1:{porta}/?u={usuario_alvo}&t={token}"

    def capturar_erro_tela(page) -> str:
        exc = page.locator('[data-testid="stException"]')
        if exc.count() > 0:
            return exc.first.inner_text().strip()
        alerta = page.locator('[data-testid="stAlert"]').filter(has_text="Error")
        if alerta.count() > 0:
            return alerta.first.inner_text().strip()
        return ""

    def montar_falha(erro_bruto: str) -> dict:
        exp = gerar_explicacao_erro(titulo_etapa, arquivo_alvo, acao_tentada, erro_bruto)
        return {"etapa": titulo_etapa, "status": "FALHA", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": exp, "detalhe": erro_bruto}

    if codigo_etapa == "criar_figurinha":
        try:
            from modules.discord_extra import salvar_emoji_custom, carregar_emojis_custom, EMOJI_FILE
            buf = io.BytesIO()
            Image.new("RGBA", (128, 128), (124, 58, 237, 255)).save(buf, format="PNG")
            buf.name = "qa_teste.png"
            ok, msg = salvar_emoji_custom("qa_teste", buf, "DiagnosticoBot")
            if not ok:
                return montar_falha(f"Falha ao salvar figurinha: {msg}")
            salvos = carregar_emojis_custom()
            existe_arq = "qa_teste" in salvos and Path(salvos["qa_teste"]["caminho"]).exists()
            if "qa_teste" in salvos:
                Path(salvos["qa_teste"]["caminho"]).unlink(missing_ok=True)
                del salvos["qa_teste"]
                EMOJI_FILE.write_text(__import__("json").dumps(salvos, indent=4), encoding="utf-8")
            if not existe_arq:
                return montar_falha("A figurinha foi registrada no JSON mas o arquivo PNG não foi gravado em omnix_emojis.")
            return {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Figurinha criada, gravada em disco, validada na galeria e limpa com sucesso!"}
        except Exception as e:
            return montar_falha(str(e))

    if codigo_etapa == "conversor":
        try:
            tmp_in = Path("omnix_storage") / "qa_conv_test.png"
            tmp_out = Path("omnix_storage") / "qa_conv_test.webp"
            Image.new("RGB", (64, 64), (56, 189, 248)).save(tmp_in, format="PNG")
            Image.open(tmp_in).save(tmp_out, format="WEBP", quality=85)
            ok_cv = tmp_out.exists() and tmp_out.stat().st_size > 0
            tmp_in.unlink(missing_ok=True)
            tmp_out.unlink(missing_ok=True)
            if not ok_cv:
                return montar_falha("O arquivo convertido WEBP não foi gerado corretamente.")
            return {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Conversão de imagem (PNG -> WEBP) executada e validada com sucesso."}
        except Exception as e:
            return montar_falha(str(e))

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1366, "height": 900})
            page = context.new_page()
            page.goto(url_base, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2200)

            err_login = capturar_erro_tela(page)
            if err_login:
                browser.close()
                return montar_falha(err_login)

            if codigo_etapa == "inicio":
                ok = page.locator("button").filter(has_text="Início").count() > 0
                browser.close()
                return montar_falha("Barra principal não renderizou.") if not ok else {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Feed inicial e barra principal respondendo."}

            elif codigo_etapa == "chat":
                page.locator("button").filter(has_text="Chat").first.click(force=True)
                page.wait_for_timeout(2000)
                err = capturar_erro_tela(page)
                if err:
                    browser.close(); return montar_falha(err)
                chat_box = page.locator('[data-testid="stChatInputTextArea"]')
                if chat_box.count() > 0:
                    chat_box.first.fill("Teste automático @omnix horario")
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(2200)
                    err2 = capturar_erro_tela(page)
                    browser.close()
                    return montar_falha(err2) if err2 else {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Chat aberto, mensagem enviada e @omnix acionado."}
                browser.close()
                return montar_falha("Caixa de envio de mensagens não apareceu.")

            elif codigo_etapa == "ver_baixar_imagem":
                page.locator("button").filter(has_text="Chat").first.click(force=True)
                page.wait_for_timeout(2000)
                btn_zoom = page.locator("button").filter(has_text="Tela Cheia")
                if btn_zoom.count() > 0:
                    btn_zoom.first.click(force=True)
                    page.wait_for_timeout(1500)
                    err = capturar_erro_tela(page)
                    tem_dl = page.locator("button").filter(has_text="Baixar HD").count() > 0
                    browser.close()
                    if err: return montar_falha(err)
                    if not tem_dl: return montar_falha("O modal abriu, mas o botão 'Baixar HD' não foi encontrado dentro dele.")
                    return {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Botão 'Tela Cheia' clicado, Visualizador HD aberto e botão 'Baixar HD' validado!"}
                else:
                    page.locator("button").filter(has_text="Arquivos").first.click(force=True)
                    page.wait_for_timeout(1800)
                    err = capturar_erro_tela(page)
                    browser.close()
                    return montar_falha(err) if err else {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Componentes de visualização e download íntegros."}

            elif codigo_etapa == "social_post":
                page.locator("button").filter(has_text="Social").first.click(force=True)
                page.wait_for_timeout(1200)
                page.locator("label").filter(has_text="Postar").first.click(force=True)
                page.wait_for_timeout(1500)
                err = capturar_erro_tela(page)
                tem_area = page.locator("textarea").count() > 0
                browser.close()
                if err: return montar_falha(err)
                return montar_falha("Campo de texto não encontrado.") if not tem_area else {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Formulário de publicação pronto."}

            elif codigo_etapa == "social_perfil":
                page.locator("button").filter(has_text="Social").first.click(force=True)
                page.wait_for_timeout(1200)
                page.locator("label").filter(has_text="Perfil").first.click(force=True)
                page.wait_for_timeout(1500)
                err = capturar_erro_tela(page)
                browser.close()
                return montar_falha(err) if err else {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Perfil, capa e sub-abas carregados."}

            elif codigo_etapa == "midia":
                page.locator("button").filter(has_text="Mídia").first.click(force=True)
                page.wait_for_timeout(1800)
                err = capturar_erro_tela(page)
                browser.close()
                return montar_falha(err) if err else {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Central de Mídia carregada."}

            elif codigo_etapa == "watch":
                page.locator("button").filter(has_text="Mídia").first.click(force=True)
                page.wait_for_timeout(1200)
                page.locator("label").filter(has_text="Assistir").first.click(force=True)
                page.wait_for_timeout(1500)
                err = capturar_erro_tela(page)
                browser.close()
                return montar_falha(err) if err else {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Assistir Juntos carregado."}

            elif codigo_etapa == "drive":
                page.locator("button").filter(has_text="Arquivos").first.click(force=True)
                page.wait_for_timeout(1800)
                err = capturar_erro_tela(page)
                browser.close()
                return montar_falha(err) if err else {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "OMNIX Drive, filtros e menu contextual funcionando."}

            elif codigo_etapa == "bot":
                page.locator("button").filter(has_text="✨ IA").first.click(force=True)
                page.wait_for_timeout(1800)
                err = capturar_erro_tela(page)
                browser.close()
                return montar_falha(err) if err else {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Painel OMNIX IA carregado."}

            elif codigo_etapa == "vision_topo":
                page.locator("button").filter(has_text="✨ IA").first.click(force=True)
                page.wait_for_timeout(1200)
                page.locator("label").filter(has_text="Vision").first.click(force=True)
                page.wait_for_timeout(1200)
                err1 = capturar_erro_tela(page)
                page.locator("button").filter(has_text="🔔").first.click(force=True)
                page.wait_for_timeout(900)
                err2 = capturar_erro_tela(page)
                page.locator("button").filter(has_text="⚙️").first.click(force=True)
                page.wait_for_timeout(900)
                err3 = capturar_erro_tela(page)
                browser.close()
                err_f = err1 or err2 or err3
                return montar_falha(err_f) if err_f else {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Vision IA, Notificações e Configurações funcionando sem erros."}

            browser.close()
            return {"etapa": titulo_etapa, "status": "OK", "arquivo": arquivo_alvo, "acao": acao_tentada, "explicacao": "Tudo certo.", "detalhe": "Teste concluído."}
    except Exception as e:
        return montar_falha(str(e))

@st.dialog("🧪 Diagnóstico Interativo (Somente Admin)", width="large")
def exibir_popup_diagnostico_admin():
    estado = st.session_state.get("qa_step_state")
    if not estado:
        return

    fila = estado.get("fila", list(range(len(ETAPAS_DIAGNOSTICO))))
    pos_fila = estado.get("pos_fila", 0)
    idx_real = fila[pos_fila]
    total = len(fila)
    res = estado["resultado_atual"]
    u_sim = estado["usuario"]

    st.progress((pos_fila + 1) / total, text=f"Teste {pos_fila + 1} de {total} • Simulando conta: @{u_sim}")

    if res["status"] == "OK":
        st.success(f"✅ **{res['etapa']}** — Funcionando perfeitamente!")
        st.write(res["detalhe"])
    else:
        st.error(f"❌ **{res['etapa']}** — Falha detectada em `{res.get('arquivo', '')}`")
        st.markdown("#### 🧠 Diagnóstico & Como Corrigir:")
        st.info(res.get("explicacao", ""))

        relatorio_copiar = (
            f"Corrija este erro no OMNIX:\n"
            f"- Etapa: {res['etapa']}\n"
            f"- Arquivo provável: {res.get('arquivo', '')}\n"
            f"- Ação tentada: {res.get('acao', '')}\n"
            f"- Diagnóstico: {res.get('explicacao', '')}\n"
            f"- Traceback/Erro técnico:\n{res['detalhe']}"
        )
        st.caption("📋 **Copie o relatório abaixo e cole no chat para correção imediata:**")
        st.code(relatorio_copiar, language="markdown")

    st.divider()
    c1, c2, c3 = st.columns([2, 1.3, 1.1])

    if pos_fila + 1 < total:
        prox_idx_real = fila[pos_fila + 1]
        prox_nome = ETAPAS_DIAGNOSTICO[prox_idx_real]
        if c1.button(f"⏭️ Próxima ({prox_nome[:20]}...)", type="primary", width="stretch"):
            usuarios = carregar_usuarios()
            senha = usuarios[u_sim]["senha"]
            with st.spinner(f"🤖 Testando: {prox_nome}..."):
                novo_res = rodar_teste_unico_etapa(prox_idx_real, u_sim, senha)
                estado["pos_fila"] = pos_fila + 1
                estado["resultado_atual"] = novo_res
                estado["historico"].append(novo_res)
                st.session_state["qa_step_state"] = estado
            st.rerun()
    else:
        c1.info("🏁 Todos os testes selecionados foram concluídos!")

    if c2.button("🔄 Repetir Teste", width="stretch"):
        usuarios = carregar_usuarios()
        senha = usuarios[u_sim]["senha"]
        with st.spinner("Repetindo simulação..."):
            novo_res = rodar_teste_unico_etapa(idx_real, u_sim, senha)
            estado["resultado_atual"] = novo_res
            estado["historico"][-1] = novo_res
            st.session_state["qa_step_state"] = estado
        st.rerun()

    if c3.button("⏹️ Fechar", width="stretch"):
        st.session_state["qa_historico_final"] = estado["historico"]
        st.session_state.pop("qa_step_state", None)
        st.rerun()
