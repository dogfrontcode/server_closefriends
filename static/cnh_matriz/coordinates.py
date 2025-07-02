# static/cnh_matriz/coordinates.py
"""
Matriz de coordenadas para posicionamento de elementos na CNH.
Coordenadas baseadas no template front-cnh.png (700x440px).
"""

# Coordenadas dos campos de texto (x, y)
CNH_COORDINATES = {
    # DADOS PESSOAIS PRINCIPAIS
    "nome_completo": (128.5, 149.5),
    "numero_habilitacao": (67.5, 465),
    
    # Outros campos baseados na análise do template
    "primeira_habilitacao": (813, 149.5),
    "data_nascimento": (483, 171),
    "local_nascimento": (483, 171),
    "uf_nascimento": (483, 171),
    "data_emissao": (361, 213),
    "validade": (470, 213),
    "acc": (579, 213),
    "categoria": (640, 213),
    "doc_identidade": (483, 253),
    "orgao_emissor": (483, 253),
    "uf_emissor": (483, 253),
    "cpf": (361, 293),
    "numero_registro": (503, 293),
    "cat_hab": (615, 293),
    "nacionalidade": (348, 333),
    "filiacao": (483, 373),
    "assinatura_portador": (204, 477)
}

# Configurações de fonte para cada campo
FONT_CONFIGS = {
    "nome_completo": {"size": 14, "color": (0, 0, 0)},
    "numero_habilitacao": {"size": 12, "color": (0, 0, 0)},
    "primeira_habilitacao": {"size": 12, "color": (0, 0, 0)},
    "data_nascimento": {"size": 11, "color": (0, 0, 0)},
    "local_nascimento": {"size": 10, "color": (0, 0, 0)},
    "data_emissao": {"size": 11, "color": (0, 0, 0)},
    "validade": {"size": 11, "color": (0, 0, 0)},
    "acc": {"size": 11, "color": (0, 0, 0)},
    "categoria": {"size": 12, "color": (0, 0, 0)},
    "doc_identidade": {"size": 10, "color": (0, 0, 0)},
    "cpf": {"size": 11, "color": (0, 0, 0)},
    "numero_registro": {"size": 10, "color": (0, 0, 0)},
    "cat_hab": {"size": 10, "color": (0, 0, 0)},
    "nacionalidade": {"size": 10, "color": (0, 0, 0)},
    "filiacao": {"size": 9, "color": (0, 0, 0)},
    "assinatura_portador": {"size": 10, "color": (0, 0, 0)}
}

# Dimensões do template
TEMPLATE_WIDTH = 700
TEMPLATE_HEIGHT = 440

# Caminhos dos arquivos
TEMPLATE_PATH = "static/cnh_matriz/front-cnh.png"
OUTPUT_DIR = "static/generated_cnhs"