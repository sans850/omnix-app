import json
from pathlib import Path


FRIENDS_FILE = Path("amizades.json")

def carregar_amizades() -> dict:
    if not FRIENDS_FILE.exists():
        return {"amigos": {}, "pendentes": []}
    try:
        dados = json.loads(FRIENDS_FILE.read_text(encoding="utf-8"))
        dados.setdefault("amigos", {})
        dados.setdefault("pendentes", [])
        return dados
    except Exception:
        return {"amigos": {}, "pendentes": []}

def salvar_amizades(dados: dict):
    FRIENDS_FILE.write_text(json.dumps(dados, indent=4, ensure_ascii=False), encoding="utf-8")

def obter_status_relacao(user_a: str, user_b: str) -> str:
    a, b = user_a.strip().lower(), user_b.strip().lower()
    if a == b:
        return "proprio"
    dados = carregar_amizades()
    
    if b in dados["amigos"].get(a, []):
        return "amigos"
        
    for req in dados["pendentes"]:
        if req["de"] == a and req["para"] == b:
            return "enviado"
        if req["de"] == b and req["para"] == a:
            return "recebido"
            
    return "nenhum"

def enviar_pedido_amizade(de_id: str, de_nome: str, para_id: str) -> tuple[bool, str]:
    a, b = de_id.strip().lower(), para_id.strip().lower()
    if a == b:
        return False, "Você não pode adicionar a si mesmo."
        
    status = obter_status_relacao(a, b)
    if status == "amigos":
        return False, "Vocês já são amigos!"
    if status == "enviado":
        return False, "Já existe um pedido pendente enviado."
    if status == "recebido":
        aceitar_pedido_amizade(a, b)
        return True, "Vocês tinham pedidos mútuos e agora são amigos!"
        
    dados = carregar_amizades()
    dados["pendentes"].append({"de": a, "para": b})
    salvar_amizades(dados)
    from modules.social import registrar_notificacao
    registrar_notificacao(a, de_nome, "🤝 Amizade", "enviou um pedido de amizade para você!")
    return True, "Pedido de amizade enviado!"

def aceitar_pedido_amizade(meu_id: str, amigo_id: str):
    a, b = meu_id.strip().lower(), amigo_id.strip().lower()
    dados = carregar_amizades()
    
    # Remove da lista de pendentes
    dados["pendentes"] = [
        r for r in dados["pendentes"]
        if not ((r["de"] == b and r["para"] == a) or (r["de"] == a and r["para"] == b))
    ]
    
    # Adiciona nos dois lados
    dados["amigos"].setdefault(a, [])
    dados["amigos"].setdefault(b, [])
    if b not in dados["amigos"][a]:
        dados["amigos"][a].append(b)
    if a not in dados["amigos"][b]:
        dados["amigos"][b].append(a)
        
    salvar_amizades(dados)

def recusar_ou_cancelar_pedido(user_a: str, user_b: str):
    a, b = user_a.strip().lower(), user_b.strip().lower()
    dados = carregar_amizades()
    dados["pendentes"] = [
        r for r in dados["pendentes"]
        if not ((r["de"] == a and r["para"] == b) or (r["de"] == b and r["para"] == a))
    ]
    salvar_amizades(dados)

def remover_amigo(user_a: str, user_b: str):
    a, b = user_a.strip().lower(), user_b.strip().lower()
    dados = carregar_amizades()
    if b in dados["amigos"].get(a, []):
        dados["amigos"][a].remove(b)
    if a in dados["amigos"].get(b, []):
        dados["amigos"][b].remove(a)
    salvar_amizades(dados)

def listar_amigos(user_id: str) -> list:
    dados = carregar_amizades()
    return dados["amigos"].get(user_id.strip().lower(), [])

def listar_pedidos_recebidos(user_id: str) -> list:
    uid = user_id.strip().lower()
    dados = carregar_amizades()
    return [r["de"] for r in dados["pendentes"] if r["para"] == uid]

def listar_pedidos_enviados(user_id: str) -> list:
    uid = user_id.strip().lower()
    dados = carregar_amizades()
    return [r["para"] for r in dados["pendentes"] if r["de"] == uid]

