import streamlit as st
import json
from pathlib import Path
from datetime import datetime
from modules.social import registrar_notificacao

WATCH_FILE = Path("watch_room.json")

def carregar_sala() -> dict:
    if not WATCH_FILE.exists():
        return {"ativo": False, "host": "", "titulo": "", "tipo": "link", "fonte": "", "inicio_ts": 0, "participantes": [], "chat": []}
    try:
        d = json.loads(WATCH_FILE.read_text(encoding="utf-8"))
        d.setdefault("participantes", [])
        return d
    except Exception:
        return {"ativo": False, "host": "", "titulo": "", "tipo": "link", "fonte": "", "inicio_ts": 0, "participantes": [], "chat": []}

def salvar_sala(dados: dict):
    WATCH_FILE.write_text(json.dumps(dados, indent=4, ensure_ascii=False), encoding="utf-8")

@st.fragment(run_every=4)
def chat_ao_vivo_watch(nome_usuario: str):
    sala = carregar_sala()
    box = st.container(height=250, border=True)
    with box:
        for m in sala.get("chat", [])[-30:]:
            st.markdown(f"**{m['nome']}** *({m['hora']})*: {m['texto']}")
    msg_c = st.chat_input("Mensagem na sessão...", key="in_watch_clean")
    if msg_c and msg_c.strip():
        sala = carregar_sala()
        sala.setdefault("chat", []).append({"nome": nome_usuario, "texto": msg_c.strip(), "hora": datetime.now().strftime("%H:%M")})
        salvar_sala(sala)
        st.rerun()

def render_watch_party(usuario_id: str, user_info: dict, storage_dir: Path):
    st.subheader("🍿 Assistir Juntos")
    st.caption("Sincronize vídeos da web ou compartilhe sua tela em tempo real com os participantes.")

    sala = carregar_sala()

    # QUANDO NÃO HÁ SESSÃO ATIVA: CARTÃO CENTRALIZADO PARA CRIAR SESSÃO
    if not sala.get("ativo", False):
        _, col_c, _ = st.columns([0.7, 2.6, 0.7])
        with col_c:
            with st.container(border=True):
                st.markdown("#### 🎬 Criar ou entrar em uma sessão")
                origem = st.radio("Origem do conteúdo:", ["Link da Web (YouTube / MP4)", "Arquivo do Servidor", "Transmissão de Tela"], horizontal=True)
                
                fonte = ""
                tipo = "link"
                if origem == "Link da Web (YouTube / MP4)":
                    fonte = st.text_input("Link do vídeo:", placeholder="https://youtube.com...")
                    tipo = "link"
                elif origem == "Arquivo do Servidor":
                    vids = [f for f in storage_dir.rglob("*") if f.is_file() and f.suffix.lower() in (".mp4", ".webm", ".mkv")]
                    if vids:
                        vs = st.selectbox("Arquivo:", vids, format_func=lambda x: x.name)
                        fonte = str(vs)
                        tipo = "local"
                    else:
                        st.info("Nenhum vídeo local disponível.")
                else:
                    fonte = "webrtc_screen"
                    tipo = "tela"

                nome_sessao = st.text_input("Nome da sessão:", placeholder="Ex: Sessão da Noite")
                
                with st.expander("⚙️ Configurações básicas", expanded=False):
                    st.checkbox("Sincronizar tempo automaticamente ao entrar", value=True)

                if st.button("Iniciar Sessão", type="primary", width="stretch"):
                    if tipo != "tela" and not fonte.strip():
                        st.warning("Informe o link ou selecione o arquivo.")
                    else:
                        nova = {
                            "ativo": True,
                            "host": user_info["nome"],
                            "titulo": nome_sessao.strip() or "Sessão Compartilhada",
                            "tipo": tipo,
                            "fonte": fonte.strip(),
                            "inicio_ts": int(datetime.now().timestamp()),
                            "participantes": [user_info["nome"]],
                            "chat": []
                        }
                        salvar_sala(nova)
                        registrar_notificacao(usuario_id, user_info["nome"], "🍿 Assistir Juntos", f"iniciou '{nova['titulo']}'")
                        st.rerun()
        return

    # QUANDO A SESSÃO ESTÁ ATIVA: PLAYER PRINCIPAL + PARTICIPANTES NA LATERAL + CONTROLES
    if user_info["nome"] not in sala.get("participantes", []):
        sala.setdefault("participantes", []).append(user_info["nome"])
        salvar_sala(sala)

    col_player, col_side = st.columns([2.6, 1.2])

    with col_player:
        with st.container(border=True):
            st.markdown(f"#### 🔴 {sala['titulo']}")
            if sala["tipo"] == "tela":
                st.iframe("""
                <div style="font-family:sans-serif; background:#090D16; color:#F8FAFC; padding:14px; border-radius:10px;">
                    <script src="https://unpkg.com"></script>
                    <div style="display:flex; gap:8px; margin-bottom:10px;">
                        <input id="rc" value="omnix_live" style="padding:8px; border-radius:8px; border:1px solid #7C3AED; background:#111827; color:white; width:130px;">
                        <button onclick="host()" style="padding:8px 14px; border-radius:8px; border:none; background:#7C3AED; color:white; font-weight:bold; cursor:pointer;">📺 Transmitir Tela</button>
                        <button onclick="view()" style="padding:8px 14px; border-radius:8px; border:none; background:#334155; color:white; font-weight:bold; cursor:pointer;">👁️ Assistir</button>
                    </div>
                    <div id="st" style="font-size:12px; color:#94A3B8; margin-bottom:8px;">Pronto para conectar.</div>
                    <video id="v" autoplay playsinline controls style="width:100%; max-height:420px; background:black; border-radius:8px;"></video>
                    <script>
                        let peer, stream;
                        async function host(){
                            const c = document.getElementById('rc').value.trim();
                            stream = await navigator.mediaDevices.getDisplayMedia({video:true, audio:true});
                            document.getElementById('v').srcObject = stream;
                            peer = new Peer("omnix-w-" + c);
                            peer.on('open', () => document.getElementById('st').innerText = "Transmitindo na sala: " + c);
                            peer.on('connection', conn => conn.on('open', () => peer.call(conn.peer, stream)));
                        }
                        function view(){
                            const c = document.getElementById('rc').value.trim();
                            peer = new Peer();
                            peer.on('open', () => {
                                peer.connect("omnix-w-" + c);
                                peer.on('call', call => { call.answer(); call.on('stream', s => { document.getElementById('v').srcObject = s; document.getElementById('st').innerText = "Assistindo ao vivo"; }); });
                            });
                        }
                    </script>
                </div>
                """, height=510)
            else:
                seg = max(0, int(datetime.now().timestamp()) - sala.get("inicio_ts", 0))
                st.video(sala["fonte"], start_time=seg)

            cc1, cc2, cc3 = st.columns(3)
            if cc1.button("🔄 Ressincronizar", width="stretch"):
                st.rerun()
            if cc2.button("⏮️ Reiniciar Tempo", width="stretch"):
                sala["inicio_ts"] = int(datetime.now().timestamp())
                salvar_sala(sala)
                st.rerun()
            if cc3.button("⏹️ Encerrar Sessão", type="primary", width="stretch"):
                sala["ativo"] = False
                salvar_sala(sala)
                st.rerun()

    with col_side:
        with st.container(border=True):
            st.markdown(f"**👥 Participantes ({len(sala.get('participantes', []))})**")
            for p_nome in sala.get("participantes", []):
                st.caption(f"🟢 {p_nome}")
        chat_ao_vivo_watch(user_info["nome"])

