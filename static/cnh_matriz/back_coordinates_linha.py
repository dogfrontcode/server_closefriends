# -*- coding: utf-8 -*-
"""
🔤 CNH Back Linha - Template para linha de dados do verso da CNH

Este arquivo define o template da linha de dados que aparece no verso da CNH.
A linha contém informações codificadas conforme padrão internacional.
"""

# Template da linha de dados do verso da CNH
CNH_LINHA_TEMPLATE = """
I<BRA0267451913<012<<<<<<<<<<<
0101192M3404274BRA<<<<<<<<<<6<
{nome_edit}<<<"""

# Coordenadas para posicionamento da linha no verso
CNH_LINHA_COORDINATES = {
    "linha_dados": {
        "position": (143, 330),  # Posição (x, y) onde começar a linha
        "font_size": 14,        # Tamanho da fonte
        "color": (0, 0, 0),     # Cor preta
        "bold": False,          # Usar ASUL-REGULAR.TTF (mesma fonte do sistema)
        "line_height": 15       # Altura entre linhas
    }
}

# Configurações da linha
CNH_LINHA_CONFIG = {
    "encoding": "utf-8",
    "max_width": 600,      # Largura máxima para a linha
    "word_wrap": False,    # Não quebrar palavras
    "align": "left"        # Alinhamento à esquerda
}

def get_linha_template():
    """
    Retorna o template da linha de dados.
    
    Returns:
        str: Template com placeholder {nome_edit}
    """
    return CNH_LINHA_TEMPLATE

def get_linha_coordinates():
    """
    Retorna as coordenadas para posicionamento da linha.
    
    Returns:
        dict: Dicionário com coordenadas e configurações
    """
    return CNH_LINHA_COORDINATES

def get_linha_config():
    """
    Retorna configurações da linha.
    
    Returns:
        dict: Configurações de renderização
    """
    return CNH_LINHA_CONFIG
