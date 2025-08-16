# -*- coding: utf-8 -*-
# static/cnh_matriz/pdf_coordinates.py
"""
Matriz de coordenadas para posicionamento de imagens CNH no PDF.
Coordenadas baseadas no template pdf-base.jpg (2480x3509px).
"""

# Coordenadas para layout padrão empilhado
PDF_LAYOUT_STACKED = {
    # CONFIGURAÇÕES GERAIS
    "base_template": "static/cnh_matriz/pdf-base.jpg",
    "spacing_between_images": 5,  # pixels entre imagens
    
    # POSIÇÕES INICIAIS
    "start_x": 50,   # margem esquerda
    "start_y": 50,   # margem superior
    
    # DIMENSÕES DE REDIMENSIONAMENTO
    "target_width": 800,   # largura máxima das imagens
    "target_height": 600,  # altura máxima das imagens
    
    # POSIÇÕES ESPECÍFICAS (calculadas automaticamente, mas podem ser override)
    "positions": {
        "front": (50, 50),      # Frente da CNH
        "back": (50, 550),      # Verso da CNH  
        "back2": (50, 1050),    # Verso alternativo (linha)
        "qrcode": (50, 1550),   # QR Code
    }
}

# Layout alternativo - lado a lado (2x2)
PDF_LAYOUT_GRID = {
    "base_template": "static/cnh_matriz/pdf-base.jpg",
    "spacing_between_images": 20,
    
    # GRID 2x2
    "positions": {
        "front": (100, 200),      # Superior esquerdo
        "back": (1300, 200),      # Superior direito
        "back2": (100, 1800),     # Inferior esquerdo
        "qrcode": (1300, 1800),   # Inferior direito
    },
    
    # Redimensionar para caber no grid
    "target_width": 1000,
    "target_height": 1400,
}

# Layout baseado no template original (posições específicas)
PDF_LAYOUT_TEMPLATE_BASED = {
    "base_template": "static/cnh_matriz/pdf-base.jpg",
    
    # Posições onde ficam as imagens no template original
    # (você deve ajustar essas coordenadas baseado na sua base)
    "positions": {
        "front": (50, 150),       # Onde está a frente no template
        "back": (1240, 150),      # Onde está o verso no template  
        "back2": (50, 1800),      # Onde está o back2 no template
        "qrcode": (1700, 150),    # Onde está o QR no template
    },
    
    # Manter tamanhos originais ou redimensionar levemente
    "target_width": 600,
    "target_height": 400,
    "preserve_original_size": False,  # Se True, não redimensiona
}

# CONFIGURAÇÃO ATIVA (altere aqui para mudar o layout)
ACTIVE_LAYOUT = PDF_LAYOUT_STACKED

# Função helper para obter coordenadas
def get_pdf_coordinates(layout_name="stacked"):
    """
    Retorna as coordenadas para o layout especificado.
    
    Args:
        layout_name (str): "stacked", "grid", ou "template_based"
        
    Returns:
        dict: Configurações do layout
    """
    layouts = {
        "stacked": PDF_LAYOUT_STACKED,
        "grid": PDF_LAYOUT_GRID, 
        "template_based": PDF_LAYOUT_TEMPLATE_BASED
    }
    
    return layouts.get(layout_name, PDF_LAYOUT_STACKED)

def calculate_stacked_positions(start_x, start_y, spacing, image_heights):
    """
    Calcula posições Y dinâmicas para layout empilhado.
    
    Args:
        start_x (int): Posição X inicial
        start_y (int): Posição Y inicial  
        spacing (int): Espaçamento entre imagens
        image_heights (list): Lista com alturas das imagens [front, back, back2, qrcode]
        
    Returns:
        dict: Posições calculadas {"front": (x,y), "back": (x,y), ...}
    """
    positions = {}
    current_y = start_y
    image_names = ["front", "back", "back2", "qrcode"]
    
    for i, name in enumerate(image_names):
        positions[name] = (start_x, current_y)
        if i < len(image_heights):
            current_y += image_heights[i] + spacing
        else:
            current_y += 500 + spacing  # altura padrão se não especificada
    
    return positions
