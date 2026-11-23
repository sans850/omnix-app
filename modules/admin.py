import streamlit as st
import json
from pathlib import Path
from PIL import Image, ImageOps
import pillow_heif

pillow_heif.register_heif_opener()

USERS_FILE = Path("usuarios.json")
PROFILES_DIR = Path("omnix_profiles")
PROFILES_DIR.mkdir(exist_ok=True)

DEFAULT_CONFIGS = {
    "perfil_publico": False,
    "mostrar_numero": True,
    "aceitar_pedidos_amizade": True,
    "notif_dm": True,
    "notif_grupo": True,
    "notif_posts": True,
    "notif_amizade": True
}

DEFAULT_USERS = {
    "admin": {
        "senha": "123", "cargo": "admin", "nome": "Administrador",
        "avatar": "", "banner": "", "bio": "Administrador do OMNIX", "numero": "0001",
        "configs": DEFAULT_CONFIGS.copy()
    },
    "grupo": {
        "senha": "123", "cargo": "membro", "nome": "Membro do Grupo",
        "avatar": "", "banner": "", "bio": "Membro do grupo", "numero": "0002",
        "configs": DEFAULT_CONFIGS.copy()
    }
}

def carregar_usuarios() -> dict:
    if not USERS_FILE.exists():
        salvar_usuarios(DEFAULT_USERS)
        return DEFAULT_USERS.copy()
    try:
        dados = json.loads(USERS_FILE.read_text(encoding="utf-8"))
        for idx, (uid, u) in enumerate(dados.items(), start=1):
            u.setdefault("avatar", "")
            u.setdefault("banner", "")
            u.setdefault("bio", "Olá! Estou usando o OMNIX.")
            u.setdefault("numero", f"{idx:04d}")
            u.setdefault("cor_nome", "#818CF8")
            u.setdefault("tag_nitro", "⚡")
            u.setdefault("configs", {})
            for k, v in DEFAULT_CONFIGS.items():
                u["configs"].setdefault(k, v)
        return dados
    except Exception:
        return DEFAULT_USERS.copy()

def salvar_usuarios(usuarios: dict):
    USERS_FILE.write_text(json.dumps(usuarios, indent=4, ensure_ascii=False), encoding="utf-8")

def atualizar_configuracoes_usuario(usuario_id: str, novas_configs: dict):
    usuarios = carregar_usuarios()
    if usuario_id in usuarios:
        usuarios[usuario_id]["configs"] = novas_configs
        salvar_usuarios(usuarios)

def alterar_senha_usuario(usuario_id: str, senha_atual: str, nova_senha: str) -> tuple[bool, str]:
    usuarios = carregar_usuarios()
    if usuario_id not in usuarios:
        return False, "Usuário não encontrado."
    if usuarios[usuario_id]["senha"] != senha_atual:
        return False, "A senha atual está incorreta."
    if len(nova_senha) < 3:
        return False, "A nova senha deve ter pelo menos 3 caracteres."
    usuarios[usuario_id]["senha"] = nova_senha
    salvar_usuarios(usuarios)
    return True, "Senha alterada com sucesso!"

def numero_ja_existe(numero: str, ignorar_uid: str = "") -> bool:
    usuarios = carregar_usuarios()
    num_limpo = numero.strip()
    for uid, dados in usuarios.items():
        if uid != ignorar_uid and str(dados.get("numero", "")).strip() == num_limpo:
            return True
    return False

def buscar_usuario_por_numero(numero: str) -> str:
    usuarios = carregar_usuarios()
    num_limpo = numero.strip()
    for uid, dados in usuarios.items():
        if str(dados.get("numero", "")).strip() == num_limpo:
            return uid
    return ""

def atualizar_avatar(usuario_id: str, imagem_bytes) -> str:
    usuarios = carregar_usuarios()
    if usuario_id in usuarios:
        imagem_bytes.seek(0)
        img = Image.open(imagem_bytes)
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((300, 300))
        caminho_avatar = PROFILES_DIR / f"avatar_{usuario_id}.jpg"
        img.save(caminho_avatar, format="JPEG", quality=85)
        usuarios[usuario_id]["avatar"] = str(caminho_avatar)
        salvar_usuarios(usuarios)
        return str(caminho_avatar)
    return ""

def atualizar_banner(usuario_id: str, imagem_bytes) -> str:
    usuarios = carregar_usuarios()
    if usuario_id in usuarios:
        imagem_bytes.seek(0)
        img = Image.open(imagem_bytes)
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((1200, 400))
        caminho_banner = PROFILES_DIR / f"banner_{usuario_id}.jpg"
        img.save(caminho_banner, format="JPEG", quality=85)
        usuarios[usuario_id]["banner"] = str(caminho_banner)
        salvar_usuarios(usuarios)
        return str(caminho_banner)
    return ""

def atualizar_estilo_nitro(usuario_id: str, cor_nome: str, tag_nitro: str):
    usuarios = carregar_usuarios()
    if usuario_id in usuarios:
        usuarios[usuario_id]["cor_nome"] = cor_nome
        usuarios[usuario_id]["tag_nitro"] = tag_nitro.strip()[:6]
        salvar_usuarios(usuarios)

def atualizar_dados_perfil(usuario_id: str, novo_nome: str, nova_bio: str, novo_numero: str) -> tuple[bool, str]:
    usuarios = carregar_usuarios()
    if usuario_id not in usuarios:
        return False, "Usuário não encontrado."
    num_limpo = novo_numero.strip()
    if not num_limpo.isdigit() or len(num_limpo) < 3 or len(num_limpo) > 10:
        return False, "O Número OMNIX deve conter apenas dígitos (entre 3 e 10 números)."
    if numero_ja_existe(num_limpo, ignorar_uid=usuario_id):
        return False, f"O número #{num_limpo} já pertence a outro membro!"
    
    if novo_nome.strip():
        usuarios[usuario_id]["nome"] = novo_nome.strip()
    usuarios[usuario_id]["bio"] = nova_bio.strip()
    usuarios[usuario_id]["numero"] = num_limpo
    salvar_usuarios(usuarios)
    return True, "Perfil e Número OMNIX atualizados com sucesso!"

def render_admin(storage_dir: Path, usuario_atual_id: str):
    st.header("🛡️ Painel de Administração")
    tab_users, tab_storage, tab_opt = st.tabs(["👥 Gerenciar Usuários & Permissões", "📊 Armazenamento & Limpeza", "⚡ Otimização do Servidor"])
    
    with tab_users:
        usuarios = carregar_usuarios()
        st.subheader("➕ Adicionar Novo Membro ou Admin")
        with st.form("form_novo_usuario", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                novo_login = st.text_input("Login de acesso").strip().lower()
                novo_nome = st.text_input("Nome de exibição").strip()
                novo_num = st.text_input("Número OMNIX (ex: 1010)").strip()
            with col2:
                nova_senha = st.text_input("Senha inicial", type="password")
                novo_cargo = st.selectbox("Nível de Permissão", ["membro", "admin"])
                
            if st.form_submit_button("Criar Conta", type="primary"):
                if not novo_login or not novo_nome or not novo_senha or not novo_num:
                    st.warning("Preencha todos os campos.")
                elif not novo_num.isdigit():
                    st.warning("O Número OMNIX deve conter apenas números.")
                elif novo_login in usuarios:
                    st.error("Esse login já existe!")
                elif numero_ja_existe(novo_num):
                    st.error("Esse Número OMNIX já está em uso!")
                else:
                    usuarios[novo_login] = {
                        "senha": nova_senha,
                        "cargo": novo_cargo,
                        "nome": novo_nome,
                        "avatar": "",
                        "banner": "",
                        "bio": "Membro do OMNIX",
                        "numero": novo_num,
                        "configs": DEFAULT_CONFIGS.copy()
                    }
                    salvar_usuarios(usuarios)
                    st.success(f"Conta **{novo_nome}** (`#{novo_num}`) criada!")
                    st.rerun()

        st.divider()
        st.subheader("🔑 Contas Ativas e Permissões")
        for login_id, dados in list(usuarios.items()):
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2.5, 1.5, 2, 1])
                icone = "🛡️" if dados["cargo"] == "admin" else "👤"
                c1.markdown(f"**{icone} {dados['nome']}** (`@{login_id}` • **#{dados.get('numero', '0000')}**)")
                c2.caption(f"Cargo: **{dados['cargo'].upper()}**")
                if login_id == usuario_atual_id:
                    c3.info("Sua conta")
                else:
                    if dados["cargo"] == "membro":
                        if c3.button("⬆️ Dar Admin", key=f"prom_{login_id}"):
                            usuarios[login_id]["cargo"] = "admin"
                            salvar_usuarios(usuarios)
                            st.rerun()
                    else:
                        if c3.button("⬇️ Tirar Admin", key=f"reb_{login_id}"):
                            usuarios[login_id]["cargo"] = "membro"
                            salvar_usuarios(usuarios)
                            st.rerun()
                    if c4.button("🗑️", key=f"del_{login_id}"):
                        del usuarios[login_id]
                        salvar_usuarios(usuarios)
                        st.rerun()

    with tab_storage:
        arquivos = [f for f in storage_dir.rglob("*") if f.is_file()]
        tamanho_total = sum(f.stat().st_size for f in arquivos) / (1024 * 1024)
        st.info(f"Pasta: `{storage_dir.resolve()}`")
        st.metric("Espaço utilizado", f"{tamanho_total:.2f} MB", f"{len(arquivos)} arquivos")
        if st.button("🗑️ Limpar arquivos temporários", type="primary"):
            for f in arquivos:
                f.unlink()
            st.success("Limpo!")
            st.rerun()

    with tab_opt:
        from modules.optimizer import render_painel_otimizacao
        render_painel_otimizacao(storage_dir)


