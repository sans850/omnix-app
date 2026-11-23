import streamlit as st
import zipfile
import py_compile
import json
import hashlib
from pathlib import Path
from datetime import datetime
from google import genai
from modules.vision import carregar_api_key
from modules.admin import carregar_usuarios

AUDIT_DIR = Path.home() / "Downloads"
AUDIT_DIR.mkdir(exist_ok=True)

def gerar_zip_prints_abas(admin_user: str, admin_senha: str) -> tuple[bool, str, str]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False, "Playwright não instalado. Rode 'pip install playwright' e 'playwright install chromium'.", ""

    porta = st.get_option("server.port") or 8501
    token = hashlib.sha256(f"{admin_user}:{admin_senha}:omnix_secret".encode()).hexdigest()[:16]
    url_auth = f"http://127.0.0.1:{porta}/?u={admin_user}&t={token}"

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pasta_sessao = AUDIT_DIR / f"prints_{ts}"
    pasta_sessao.mkdir(parents=True, exist_ok=True)
    zip_path = AUDIT_DIR / f"OMNIX_Prints_Completos_{ts}.zip"

    abas_alvo = [
        ("01_Inicio", "Início"),
        ("02_Chat", "Chat"),
        ("03_Social", "Social"),
        ("04_Midia", "Mídia"),
        ("05_Arquivos", "Arquivos"),
        ("06_IA", "IA")
    ]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1366, "height": 900})
            page = context.new_page()
            page.goto(url_auth, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_selector("button", timeout=20000)
            page.wait_for_timeout(2000)

            capturados = 0
            for nome_arq, texto_btn in abas_alvo:
                try:
                    btn = page.locator("button").filter(has_text=texto_btn).first
                    if btn.count() > 0:
                        btn.click()
                        page.wait_for_timeout(2000)
                        page.screenshot(path=str(pasta_sessao / f"{nome_arq}.png"), full_page=True)
                        capturados += 1
                except Exception:
                    continue

            browser.close()

        if capturados == 0:
            return False, f"Nenhuma aba encontrada na porta {porta}.", ""

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for png in sorted(pasta_sessao.glob("*.png")):
                zf.write(png, arcname=png.name)

        return True, f"✅ {capturados} abas capturadas em alta definição!", str(zip_path)
    except Exception as e:
        return False, f"Erro durante a captura automática: {e}", ""

def executar_auditoria_sistema() -> str:
    raiz = Path(".")
    erros_sintaxe = []
    arquivos_py = list(raiz.glob("*.py")) + list(Path("modules").glob("*.py"))
    resumo_codigo = []

    for py_file in arquivos_py:
        try:
            py_compile.compile(str(py_file), doraise=True)
            linhas = len(py_file.read_text(encoding="utf-8", errors="ignore").splitlines())
            resumo_codigo.append(f"- {py_file}: OK ({linhas} linhas)")
        except Exception as e:
            erros_sintaxe.append(f"- ERRO em {py_file}: {e}")

    erros_json = []
    for jf in raiz.glob("*.json"):
        try:
            json.loads(jf.read_text(encoding="utf-8"))
        except Exception as e:
            erros_json.append(f"- JSON corrompido {jf.name}: {e}")

    diagnostico_bruto = (
        f"DIAGNÓSTICO TÉCNICO DO SISTEMA OMNIX ({datetime.now().strftime('%d/%m/%Y %H:%M')}):\n\n"
        f"1. SINTAXE PYTHON:\n" + ("\n".join(erros_sintaxe) if erros_sintaxe else "Nenhum erro de sintaxe encontrado.\n" + "\n".join(resumo_codigo)) + "\n\n"
        f"2. INTEGRIDADE DOS BANCOS JSON:\n" + ("\n".join(erros_json) if erros_json else "Todos os arquivos JSON estão íntegros e válidos.")
    )

    api_key = carregar_api_key()
    if not api_key:
        return diagnostico_bruto + "\n\n⚠️ *(Configure a Gemini API Key no módulo Vision para análise inteligente por IA).* "

    try:
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Analise este diagnóstico técnico do sistema OMNIX e liste: 1) Status Geral; 2) Possíveis Riscos; 3) Top 5 Melhorias:\n\n" + diagnostico_bruto
        )
        return resp.text + "\n\n---\n```text\n" + diagnostico_bruto + "\n```"
    except Exception as e:
        return diagnostico_bruto + f"\n\n❌ Erro ao consultar IA: {e}"

def render_habilidades_admin_bot(usuario_id: str):
    from modules.qa_simulator import rodar_teste_unico_etapa, ETAPAS_DIAGNOSTICO

    st.markdown("#### 🧪 Pseudo-IA de Diagnóstico Personalizável (Escolha o que Testar)")
    st.caption("Selecione uma ou várias capacidades do OMNIX para simular um usuário real e receber o relatório no pop-up.")

    usuarios = carregar_usuarios()
    lista_u = list(usuarios.keys())
    u_teste = st.selectbox("Simular com a conta de:", lista_u, index=0, key="sel_qa_user_unique")

    nomes_etapas = [next(iter(e)) for e in ETAPAS_DIAGNOSTICO]
    selecionadas = st.multiselect(
        "Escolha quais capacidades/funções deseja testar:",
        options=nomes_etapas,
        default=nomes_etapas,
        key="multi_qa_etapas"
    )

    if st.button("▶️ Iniciar Diagnóstico Selecionado (Abrir Pop-up)", type="primary", width="stretch"):
        if not selecionadas:
            st.warning("Selecione pelo menos uma função acima para testar.")
        else:
            fila_indices = [nomes_etapas.index(s) for s in selecionadas]
            primeiro_idx = next(iter(fila_indices))
            senha_t = usuarios[u_teste]["senha"]
            with st.spinner(f"🤖 Testando {next(iter(ETAPAS_DIAGNOSTICO[primeiro_idx]))}..."):
                res_0 = rodar_teste_unico_etapa(primeiro_idx, u_teste, senha_t)
                st.session_state["qa_step_state"] = {
                    "usuario": u_teste,
                    "fila": fila_indices,
                    "pos_fila": 0,
                    "resultado_atual": res_0,
                    "historico": [res_0]
                }
            st.rerun()

    if "qa_historico_final" in st.session_state and st.session_state["qa_historico_final"]:
        st.markdown("**📋 Resumo da Última Simulação:**")
        for item in st.session_state["qa_historico_final"]:
            if item["status"] == "OK":
                st.success(f"✅ **{item['etapa']}** — {item['detalhe']}")
            else:
                st.error(f"❌ **{item['etapa']}** — {item['detalhe']}")

    st.divider()
    col_s1, col_s2 = st.columns(2)

    with col_s1:
        with st.container(border=True):
            st.markdown("#### 📸 Capturar Prints das Abas (.ZIP)")
            if st.button("📸 Gerar ZIP de Prints", width="stretch"):
                senha_adm = usuarios.get(usuario_id, {}).get("senha", "")
                with st.spinner("🤖 Capturando prints..."):
                    ok, msg, zip_file = gerar_zip_prints_abas(usuario_id, senha_adm)
                    if ok:
                        st.session_state["ultimo_zip_prints"] = zip_file
                        st.success(msg)
                    else:
                        st.error(msg)

            if "ultimo_zip_prints" in st.session_state and Path(st.session_state["ultimo_zip_prints"]).exists():
                zp = Path(st.session_state["ultimo_zip_prints"])
                st.download_button(
                    label=f"⬇️ Baixar {zp.name}",
                    data=zp.read_bytes(),
                    file_name=zp.name,
                    mime="application/zip",
                    type="primary",
                    width="stretch"
                )

    with col_s2:
        with st.container(border=True):
            st.markdown("#### 🩺 Relatório de Erros & Melhorias (IA)")
            if st.button("🩺 Gerar Relatório do Sistema", width="stretch"):
                with st.spinner("🤖 Auditando sistema..."):
                    st.session_state["ultimo_relatorio_admin"] = executar_auditoria_sistema()

            if "ultimo_relatorio_admin" in st.session_state and st.session_state["ultimo_relatorio_admin"]:
                rel_txt = st.session_state["ultimo_relatorio_admin"]
                st.download_button(
                    label="⬇️ Baixar Relatório (.MD)",
                    data=rel_txt.encode("utf-8"),
                    file_name=f"Relatorio_OMNIX_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    width="stretch"
                )

    if "ultimo_relatorio_admin" in st.session_state and st.session_state["ultimo_relatorio_admin"]:
        with st.container(border=True):
            st.markdown(st.session_state["ultimo_relatorio_admin"])



