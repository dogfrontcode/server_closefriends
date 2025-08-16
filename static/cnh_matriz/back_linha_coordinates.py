# -*- coding: utf-8 -*-
"""
🎯 Coordenadas e configurações para MRZ (Machine Readable Zone) no back-linha.png
Sistema de alinhamento perfeito para as 3 linhas MRZ com 30 caracteres cada.
"""

# Configurações do MRZ para back-linha.png (700x440px)
MRZ_CONFIG = {
    # Posicionamento das linhas MRZ (centralizadas na imagem)
    'chars_per_line': 30,           # Padrão MRZ: exatamente 30 caracteres por linha
    'total_lines': 3,               # 3 linhas MRZ
    
    # Espaçamento e fonte
    'char_spacing': 3,              # 3px entre caracteres (como no teste.py)
    'line_spacing': 25,             # Espaçamento entre linhas MRZ
    'font_size': 16,                # Tamanho da fonte MRZ
    
    # Posicionamento central na imagem 700x440
    'start_x': 80,                  # Posição X inicial (centralizada)
    'start_y': 200,                 # Posição Y da primeira linha (meio da tela)
    
    # Estilo visual
    'font_color': (0, 0, 0),        # Preto para MRZ
    'background_color': None,       # Sem fundo (transparente)
    
    # Validação MRZ
    'strict_30_chars': True,        # Forçar exatamente 30 caracteres
    'fill_char': '<',               # Caractere de preenchimento MRZ
}

# Coordenadas específicas de cada linha MRZ
MRZ_LINE_COORDINATES = {
    "mrz_line_1": {
        "position": (MRZ_CONFIG['start_x'], MRZ_CONFIG['start_y']),
        "description": "Primeira linha MRZ - Documento e país"
    },
    "mrz_line_2": {
        "position": (MRZ_CONFIG['start_x'], MRZ_CONFIG['start_y'] + MRZ_CONFIG['line_spacing']),
        "description": "Segunda linha MRZ - Data nascimento, sexo, validade"
    },
    "mrz_line_3": {
        "position": (MRZ_CONFIG['start_x'], MRZ_CONFIG['start_y'] + MRZ_CONFIG['line_spacing'] * 2),
        "description": "Terceira linha MRZ - Nome do titular"
    }
}

# Configurações de fonte para cada linha MRZ
MRZ_FONT_CONFIGS = {
    "mrz_line_1": {
        "size": MRZ_CONFIG['font_size'],
        "color": MRZ_CONFIG['font_color'],
        "bold": False,
        "family": "OCR-B"  # Fonte ideal para MRZ
    },
    "mrz_line_2": {
        "size": MRZ_CONFIG['font_size'],
        "color": MRZ_CONFIG['font_color'],
        "bold": False,
        "family": "OCR-B"
    },
    "mrz_line_3": {
        "size": MRZ_CONFIG['font_size'],
        "color": MRZ_CONFIG['font_color'],
        "bold": False,
        "family": "OCR-B"
    }
}

# Dimensões do template back-linha.png
BACK_LINHA_TEMPLATE_WIDTH = 700
BACK_LINHA_TEMPLATE_HEIGHT = 440

# Caminho do template
BACK_LINHA_TEMPLATE_PATH = "static/cnh_matriz/back-linha.png"

# Área de segurança para o MRZ (para não sobrepor outros elementos)
MRZ_SAFE_AREA = {
    "x": 50,
    "y": 180,
    "width": 600,
    "height": 120
}

# Exemplo de dados MRZ padrão para testes
SAMPLE_MRZ_DATA = {
    "line_1": "I<BRA0318154714<022<<<<<<<<<<",  # 30 caracteres
    "line_2": "7506291M3407242BRA<<<<<<<<<<8<",  # 30 caracteres  
    "line_3": "RODRIGO<<ANDRADE<DE<FIGUEIREDO"   # 30 caracteres
}

# Validador de caracteres MRZ válidos
MRZ_VALID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789<")

def validate_mrz_line(line: str) -> bool:
    """
    Valida se uma linha MRZ está no formato correto.
    
    Args:
        line: Linha MRZ para validar
        
    Returns:
        bool: True se válida, False caso contrário
    """
    if not line:
        return False
    
    # Deve ter exatamente 30 caracteres
    if len(line) != 30:
        return False
    
    # Todos os caracteres devem ser válidos para MRZ
    for char in line.upper():
        if char not in MRZ_VALID_CHARS:
            return False
    
    return True

def format_mrz_line(text: str, max_chars: int = 30) -> str:
    """
    Formata uma linha MRZ para ter exatamente 30 caracteres.
    (Mesmo algoritmo do teste.py)
    
    Args:
        text: Texto da linha MRZ
        max_chars: Número máximo de caracteres (padrão 30)
        
    Returns:
        String com exatamente 30 caracteres
    """
    # Remove caracteres não-ASCII e substitui por '<'
    ascii_text = ''
    for char in text:
        if ord(char) < 128:
            ascii_text += char.upper()
        else:
            ascii_text += '<'
    
    # Trunca se for maior que 30 caracteres
    if len(ascii_text) > max_chars:
        return ascii_text[:max_chars]
    
    # Preenche com '<' se for menor que 30 caracteres (padrão MRZ)
    while len(ascii_text) < max_chars:
        ascii_text += '<'
    
    return ascii_text

def get_mrz_char_positions(line_num: int, font_char_width: int) -> list:
    """
    Calcula as posições X exatas de cada caractere MRZ para alinhamento perfeito.
    (Adaptado do teste.py)
    
    Args:
        line_num: Número da linha (0, 1, 2)
        font_char_width: Largura de um caractere na fonte
        
    Returns:
        Lista com posições X de cada um dos 30 caracteres
    """
    positions = []
    start_x = MRZ_CONFIG['start_x']
    char_spacing = MRZ_CONFIG['char_spacing']
    
    for i in range(30):  # 30 caracteres por linha
        x = start_x + (i * (font_char_width + char_spacing))
        positions.append(x)
    
    return positions

# Informações para debug e logging
DEBUG_INFO = {
    "template_file": BACK_LINHA_TEMPLATE_PATH,
    "total_mrz_width": MRZ_CONFIG['start_x'] * 2 + (29 * (16 + MRZ_CONFIG['char_spacing'])),  # Estimativa
    "center_x": BACK_LINHA_TEMPLATE_WIDTH // 2,
    "center_y": BACK_LINHA_TEMPLATE_HEIGHT // 2,
    "mrz_start_y": MRZ_CONFIG['start_y'],
    "mrz_end_y": MRZ_CONFIG['start_y'] + (MRZ_CONFIG['line_spacing'] * 2)
}
