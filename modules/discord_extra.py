import json
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps
import pillow_heif

pillow_heif.register_heif_opener()

GRUPOS_FILE = Path("grupos_discord.json")
EMOJIS_FILE = Path("emojis_custom.json")
EMOJIS_DIR = Path("omnix_emojis")
EMOJIS_DIR.mkdir(exist_ok=True)

CANAIS_BASE = ["geral", "clips-e-midia", "off-topic"]

def carregar_grupos() -> dict:
    if not GRUPOS_FILE.exists():
        padrao = {
            "grp_geral": {
                "nome": "Comunidade OMNIX",
                "dono": "admin",
                "membros": ["admin", "grupo"],
                "cargos": {},
                "membros_cargos": {},
                "canais": {c: [] for c in CANAIS_BASE}
            }
        }
        salvar_grupos(padrao)
        return padrao
    try:
        dados = json.loads(GRUPOS_FILE.read_text(encoding="utf-8"))
        alterado = False
        for gid, g in dados.items():
            if "cargos" not in g:
                g["cargos"] = {}
                alterado = True
            if "membros_cargos" not in g:
                g["membros_cargos"] = {}
                alterado = True
            if not g.get("canais"):
                g["canais"] = {"geral": []}
                alterado = True
        if alterado:
            salvar_grupos(dados)
        return dados
    except Exception:
        return {}

def salvar_grupos(dados: dict):
    GRUPOS_FILE.write_text(json.dumps(dados, indent=4, ensure_ascii=False), encoding="utf-8")

def listar_grupos_do_usuario(uid: str, cargo_global: str) -> dict:
    todos = carregar_grupos()
    u = uid.strip().lower()
    meus = {}
    for gid, g in todos.items():
        if gid == "grp_geral" and u not in g["membros"]:
            g["membros"].append(u)
            salvar_grupos(todos)
        if u in g.get("membros", []) or g.get("dono") == u:
            meus[gid] = g
    return meus

def criar_novo_grupo(nome_grupo: str, dono_id: str) -> str:
    todos = carregar_grupos()
    gid = f"grp_{int(datetime.now().timestamp() * 1000)}"
    u = dono_id.strip().lower()
    todos[gid] = {
        "nome": nome_grupo.strip(),
        "dono": u,
        "membros": [u],
        "cargos": {
            "moderador": {
                "nome": "Moderador",
                "cor": "#10B981",
                "perms": ["apagar_msg", "convidar", "gerenciar_canais"]
            }
        },
        "membros_cargos": {},
        "canais": {c: [] for c in CANAIS_BASE}
    }
    salvar_grupos(todos)
    return gid

def apagar_servidor(gid: str) -> tuple[bool, str]:
    if gid == "grp_geral":
        return False, "O servidor principal da Comunidade OMNIX não pode ser apagado."
    todos = carregar_grupos()
    if gid in todos:
        del todos[gid]
        salvar_grupos(todos)
        return True, "Servidor apagado com sucesso!"
    return False, "Servidor não encontrado."

def verificar_permissao_servidor(gid: str, uid: str, cargo_global: str, perm: str) -> bool:
    u = uid.strip().lower()
    if cargo_global == "admin":
        return True
    todos = carregar_grupos()
    g = todos.get(gid, {})
    if g.get("dono") == u:
        return True
    cargo_id = g.get("membros_cargos", {}).get(u, "")
    if cargo_id and cargo_id in g.get("cargos", {}):
        return perm in g["cargos"][cargo_id].get("perms", [])
    return False

def adicionar_membro_ao_grupo(gid: str, novo_membro_id: str) -> tuple[bool, str]:
    todos = carregar_grupos()
    if gid not in todos:
        return False, "Grupo não encontrado."
    m = novo_membro_id.strip().lower()
    if m in todos[gid]["membros"]:
        return False, "Este usuário já participa do servidor."
    todos[gid]["membros"].append(m)
    salvar_grupos(todos)
    return True, "Membro adicionado ao servidor!"

def remover_membro_do_grupo(gid: str, alvo_id: str):
    todos = carregar_grupos()
    if gid in todos and alvo_id != todos[gid].get("dono"):
        if alvo_id in todos[gid]["membros"]:
            todos[gid]["membros"].remove(alvo_id)
        todos[gid].get("membros_cargos", {}).pop(alvo_id, None)
        salvar_grupos(todos)

def criar_cargo_servidor(gid: str, nome_cargo: str, cor: str, perms: list) -> tuple[bool, str]:
    todos = carregar_grupos()
    if gid not in todos:
        return False, "Servidor não encontrado."
    cid = "".join(c for c in nome_cargo.lower() if c.isalnum() or c == "_").strip("_")
    if len(cid) < 2:
        return False, "Nome do cargo muito curto."
    todos[gid].setdefault("cargos", {})[cid] = {
        "nome": nome_cargo.strip(),
        "cor": cor,
        "perms": perms
    }
    salvar_grupos(todos)
    return True, f"Cargo '{nome_cargo}' criado!"

def apagar_cargo_servidor(gid: str, cid: str):
    todos = carregar_grupos()
    if gid in todos and cid in todos[gid].get("cargos", {}):
        del todos[gid]["cargos"][cid]
        for u, c in list(todos[gid].get("membros_cargos", {}).items()):
            if c == cid:
                del todos[gid]["membros_cargos"][u]
        salvar_grupos(todos)

def atribuir_cargo_membro(gid: str, alvo_id: str, cid: str):
    todos = carregar_grupos()
    if gid in todos:
        if not cid:
            todos[gid].setdefault("membros_cargos", {}).pop(alvo_id, None)
        else:
            todos[gid].setdefault("membros_cargos", {})[alvo_id] = cid
        salvar_grupos(todos)

def criar_canal_servidor(gid: str, nome_canal: str) -> tuple[bool, str]:
    todos = carregar_grupos()
    if gid not in todos:
        return False, "Servidor não encontrado."
    c_limpo = "".join(c for c in nome_canal.lower().replace(" ", "-") if c.isalnum() or c == "-").strip("-")
    if len(c_limpo) < 2:
        return False, "Nome do canal inválido."
    if c_limpo in todos[gid]["canais"]:
        return False, "Já existe um canal com esse nome."
    todos[gid]["canais"][c_limpo] = []
    salvar_grupos(todos)
    return True, f"Canal #{c_limpo} criado!"

def apagar_canal_servidor(gid: str, nome_canal: str) -> tuple[bool, str]:
    todos = carregar_grupos()
    if gid in todos and nome_canal in todos[gid]["canais"]:
        if len(todos[gid]["canais"]) <= 1:
            return False, "O servidor precisa ter pelo menos 1 canal."
        del todos[gid]["canais"][nome_canal]
        salvar_grupos(todos)
        return True, f"Canal #{nome_canal} apagado!"
    return False, "Canal não encontrado."

def carregar_emojis_custom() -> dict:
    if not EMOJIS_FILE.exists():
        return {}
    try:
        return json.loads(EMOJIS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def salvar_emoji_custom(codigo: str, arquivo_up, autor_nome: str) -> tuple[bool, str]:
    cod_limpo = "".join(c for c in codigo.lower() if c.isalnum() or c == "_").strip("_")
    if len(cod_limpo) < 2:
        return False, "O nome do emoji deve ter pelo menos 2 letras/números."
    emojis = carregar_emojis_custom()
    if cod_limpo in emojis:
        return False, f"Já existe um emoji chamado :{cod_limpo}:"
    ext = Path(arquivo_up.name).suffix.lower()
    arquivo_up.seek(0)
    if ext == ".gif":
        caminho = EMOJIS_DIR / f"emoji_{cod_limpo}.gif"
        caminho.write_bytes(arquivo_up.read())
    else:
        caminho = EMOJIS_DIR / f"emoji_{cod_limpo}.png"
        img = Image.open(arquivo_up)
        img = ImageOps.exif_transpose(img).convert("RGBA")
        img.thumbnail((240, 240))
        img.save(caminho, format="PNG")
    emojis[cod_limpo] = {"caminho": str(caminho), "autor": autor_nome, "gif": (ext == ".gif")}
    EMOJIS_FILE.write_text(json.dumps(emojis, indent=4, ensure_ascii=False), encoding="utf-8")
    return True, f"Emoji :{cod_limpo}: criado com sucesso!"

