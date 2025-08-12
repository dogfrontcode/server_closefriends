# -*- coding: utf-8 -*-
# static/cnh_matriz/back_coordinates.py
"""
Matriz de coordenadas para posicionamento de elementos no VERSO da CNH.
Coordenadas baseadas no template back-cnh.png (700x440px).
"""

# Coordenadas dos campos de texto no verso (x, y)
CNH_BACK_COORDINATES = {
    # INFORMAÇÕES TÉCNICAS
    "numero_renach": (100, 50),           # Código RENACH
    "codigo_validacao": (400, 50),        # Código de validação
    "numero_espelho": (100, 80),          # Número do espelho
    "numero_registro": (30, 300),         # Número da CNH (vertical na lateral esquerda)
    
    # OBSERVAÇÕES E RESTRIÇÕES
    "observacoes": (50, 120),             # Observações gerais
    "restricoes": (50, 160),              # Códigos de restrição
    
    # HISTÓRICO DE CATEGORIAS
    "categoria_a_data": (273, 56),       # Data categoria A
    "categoria_b_data": (273, 103),       # Data categoria B  
    "categoria_c_data": (273, 150),       # Data categoria C
    "categoria_d_data": (553 , 32),       # Data categoria D
    "categoria_e_data": (553, 220),       # Data categoria E
    
    # INFORMAÇÕES ADICIONAIS
    "local_habilitacao": (50, 280),       # Local da primeira habilitação
    "uf_habilitacao": (300, 280),         # UF da habilitação
    
    # ÁREA PARA QR CODE (se necessário)
    "qr_code": (550, 300),                # Posição do QR Code
    
    # CÓDIGOS DE SEGURANÇA
    "codigo_seguranca_1": (50, 380),      # Primeiro código
    "codigo_seguranca_2": (200, 380),     # Segundo código
    "codigo_seguranca_3": (350, 380),     # Terceiro código
    
    # INFORMAÇÕES DO SISTEMA
    "versao_sistema": (500, 410),         # Versão do sistema
    "data_geracao": (50, 410)             # Data de geração
}

# Configurações de fonte para cada campo do verso
BACK_FONT_CONFIGS = {
    # Códigos técnicos - fonte menor e monospaciada
    "numero_renach": {"size": 10, "color": (0, 0, 0), "bold": True},
    "codigo_validacao": {"size": 10, "color": (0, 0, 0), "bold": True},
    "numero_espelho": {"size": 10, "color": (0, 0, 0)},
    "numero_registro": {"size": 12, "color": (0, 0, 0), "bold": True},  # Número da CNH no verso
    
    # Observações - texto normal
    "observacoes": {"size": 11, "color": (0, 0, 0)},
    "restricoes": {"size": 11, "color": (195, 0, 30)},  # VERMELHO para restrições
    
    # Datas das categorias - pequeno e centralizado
    "categoria_a_data": {"size": 11, "color": (0, 0, 0)},
    "categoria_b_data": {"size": 11, "color": (0, 0, 0)},
    "categoria_c_data": {"size": 11, "color": (0, 0, 0)},
    "categoria_d_data": {"size": 11, "color": (0, 0, 0)},
    "categoria_e_data": {"size": 11   , "color": (0, 0, 0)},
    
    # Local da habilitação
    "local_habilitacao": {"size": 11, "color": (0, 0, 0)},
    "uf_habilitacao": {"size": 11, "color": (0, 0, 0)},
    
    # Códigos de segurança - muito pequeno
    "codigo_seguranca_1": {"size": 8, "color": (128, 128, 128)},  # CINZA
    "codigo_seguranca_2": {"size": 8, "color": (128, 128, 128)},  # CINZA
    "codigo_seguranca_3": {"size": 8, "color": (128, 128, 128)},  # CINZA
    
    # Informações do sistema
    "versao_sistema": {"size": 8, "color": (128, 128, 128)},  # CINZA
    "data_geracao": {"size": 8, "color": (128, 128, 128)}     # CINZA
}

# Dimensões do template (mesmo da frente)
BACK_TEMPLATE_WIDTH = 700
BACK_TEMPLATE_HEIGHT = 440

# Configurações específicas do verso
BACK_TEMPLATE_PATH = "static/cnh_matriz/back-cnh.png"

# Área para QR Code (se implementado)
QR_CODE_AREA = {
    "position": (550, 300),
    "width": 100,
    "height": 100
}

# Mapeamento de códigos de restrição comuns
CODIGOS_RESTRICAO = {
    "A": "Obrigatório uso de lentes corretivas",
    "B": "Obrigatório uso de prótese auditiva",
    "C": "Vedado dirigir após o pôr do sol",
    "D": "Obrigatório uso de acelerador à esquerda",
    "E": "Obrigatório uso de embreagem no pé esquerdo",
    "F": "Obrigatório uso de knob no volante",
    "G": "Obrigatório uso de embreagem manual adaptada",
    "H": "Obrigatório uso de acelerador e freio manual"
} 