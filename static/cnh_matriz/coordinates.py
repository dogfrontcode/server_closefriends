# -*- coding: utf-8 -*-
# static/cnh_matriz/coordinates.py
"""
Matriz de coordenadas para posicionamento de elementos na CNH.
Coordenadas baseadas no template front-cnh.png (700x440px).
"""

# Coordenadas dos campos de texto (x, y)
CNH_COORDINATES = {
    # DADOS PESSOAIS PRINCIPAIS
    "nome_completo": (120.5, 144.5),
    "numero_habilitacao": (50, 304),
    
    # Outros campos baseados na análise do template
    "primeira_habilitacao": (555, 144.5),
    "data_nascimento": ( 483, 171),
    "local_nascimento": (483, 171),
    "uf_nascimento": (483, 171),
    "data_emissao": (317, 223),
    "validade": (440, 223),
    #"acc": (579, 213),
    "categoria": (581, 305), #habilitacao
    "doc_identidade": (317, 264),
    "orgao_emissor": (483, 253),
    "uf_emissor": (483, 253),
    "cpf": (315, 305),
    "numero_registro": (450, 305),
    "cat_hab": (581, 308), # oque é isso ?
    "nacionalidade": (317, 343),
    "filiacao": (317, 385),
    "nome_pai": (317, 385),      # Primeira linha - pai
    "nome_mae": (317, 400),      # Segunda linha - mãe (15px abaixo)
    "assinatura_portador": (204, 477),
    "foto_rg": (121, 180)  # Área para imagem do RG
}

# Configurações de fonte para cada campo
# Todas as fontes usam ASUL-REGULAR.TTF, exceto numero_registro que usa ASUL-BOLD.TTF
# Campos em VERMELHO: validade, categoria, numero_registro
FONT_CONFIGS = {
    "nome_completo": {"size": 14, "color": (0, 0, 0)},
    "numero_habilitacao": {"size": 30, "color": (0, 0, 0), "bold": True},  # Número vertical - ASUL-BOLD
    "primeira_habilitacao": {"size": 12, "color": (0, 0, 0)},
    "data_nascimento": {"size": 11, "color": (0, 0, 0)},
    "local_nascimento": {"size": 12, "color": (0, 0, 0)},
    "data_emissao": {"size": 11, "color": (0, 0, 0)},
    "validade": {"size": 11, "color": (195, 0, 30)},  # VERMELHO
    "acc": {"size": 11, "color": (0, 0, 0)},
    "categoria": {"size": 12, "color": (195, 0, 30)},  # VERMELHO
    "doc_identidade": {"size": 12, "color": (0, 0, 0)},
    "cpf": {"size": 11, "color": (0, 0, 0)},
    "numero_registro": {"size": 12, "color": (195, 0, 30)},  # VERMELHO + ASUL-BOLD
    "cat_hab": {"size": 12, "color": (0, 0, 0)},
    "nacionalidade": {"size": 12, "color": (0, 0, 0)},
    "filiacao": {"size": 12, "color": (0, 0, 0)},
    "nome_pai": {"size": 12, "color": (0, 0, 0)},
    "nome_mae": {"size": 12, "color": (0, 0, 0)},
    "assinatura_portador": {"size": 12, "color": (0, 0, 0)}
}

# Dimensões do template
TEMPLATE_WIDTH = 700
TEMPLATE_HEIGHT = 440

# Configurações da área da foto 3x4 da CNH (imagem do cliente)
FOTO_3X4_AREA = {
    "position": (121, 180),
    "width": 169,
    "height": 237
}

# Configurações da área da assinatura do portador (imagem do cliente)
ASSINATURA_AREA = {
    "position": (120, 430),  # Ajustado para ficar dentro da imagem (496-50=446, usando 430)
    "width": 168,
    "height": 50
}

# Caminhos dos arquivos
TEMPLATE_PATH = "static/cnh_matriz/front-cnh.png"
OUTPUT_DIR = "static/generated_cnhs"