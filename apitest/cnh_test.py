# -*- coding: utf-8 -*-
"""
🧪 CNH Test API - Endpoints para testes de geração de CNH
"""

from flask import Blueprint, jsonify, request
import os
import logging
from datetime import datetime
import sys

# Imports locais
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from services.cnh_generator import CNHImageGenerator
from models.cnh_request import CNHRequest
from services.path_manager import CNHPathManager

logger = logging.getLogger(__name__)

# Blueprint para testes
cnh_test_bp = Blueprint('cnh_test', __name__, url_prefix='/api/test')

class CNHTestRequest:
    """Classe simplificada para testes de CNH"""
    
    def __init__(self, user_id=117):
        self.id = user_id
        self.user_id = user_id
        self.cpf = f"{user_id:011d}"  # CPF fictício baseado no user_id
        # Nomes diferentes para testar formatação MRZ
        nomes_teste = [
            "JOAO SILVA",
            "MARIA SANTOS OLIVEIRA", 
            "PEDRO HENRIQUE COSTA LIMA",
            "ANA BEATRIZ",
            "CARLOS EDUARDO FERREIRA SANTOS"
        ]
        nome_base = nomes_teste[user_id % len(nomes_teste)]
        self.nome_completo = nome_base
        self.data_nascimento = datetime(1990, 1, 1).date()
        self.local_nascimento = "SAO PAULO"
        self.uf_nascimento = "SP"
        self.categoria_habilitacao = "B"
        self.primeira_habilitacao = datetime(2020, 1, 1).date()
        self.data_emissao = datetime.now().date()
        self.validade = datetime(2030, 1, 1).date()
        self.numero_registro = f"{user_id + 5000000000:011d}"
        self.numero_espelho = f"{user_id + 1000000000:011d}"
        self.numero_renach = f"SP{user_id:09d}"
        self.codigo_validacao = f"{user_id:010d}"
        self.doc_identidade_numero = f"{user_id * 123:08d}"
        self.doc_identidade_orgao = "SSP"
        self.doc_identidade_uf = "SP"
        self.acc = "NAO"
        self.nome_pai = "PAI TESTE"
        self.nome_mae = "MAE TESTE"
        self.sexo_condutor = "M"
        self.local_municipio = "SAO PAULO"
        self.local_uf = "SP"
        self.local_da_cnh = "SAO PAULO"
        self.observacoes = None
        self.uf_cnh = "SP"
        self.created_at = datetime.now()
        self.status = "pending"
        
    def get_idade(self):
        """Calcula idade fictícia"""
        return 33
        
    def marcar_como_processando(self):
        self.status = "processing"
        
    def marcar_como_completa(self, path):
        self.status = "completed"
        
    def marcar_como_falha(self, error):
        self.status = "failed"

@cnh_test_bp.route('/cnh-back/<int:user_id>', methods=['GET'])
def generate_back2_cnh(user_id):
    """
    Gera imagem back-line.png para teste
    
    GET /api/test/cnh-back/117
    
    Salva em: static/uploads/user/117/
    """
    try:
        logger.info(f"🧪 Iniciando teste de geração back2-cnh para user_id: {user_id}")
        
        # Criar objeto de teste
        test_request = CNHTestRequest(user_id)
        
        # Criar gerador
        generator = CNHImageGenerator()
        
        # Definir path de saída
        output_dir = f"static/uploads/user/{user_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "back-line.png")
        
        # Gerar imagem back2
        result_path = generator.generate_back2_cnh(test_request, output_path)
        
        # Verificar se arquivo foi criado
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            
            response_data = {
                "success": True,
                "message": f"Back-line.png gerado com sucesso para user {user_id}",
                "user_id": user_id,
                "file_path": result_path,
                "file_size": file_size,
                "template_used": "back-linha.png",
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Back-line gerado: {result_path} ({file_size} bytes)")
            return jsonify(response_data), 200
        else:
            error_msg = "Arquivo não foi criado"
            logger.error(f"❌ {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg,
                "user_id": user_id
            }), 500
            
    except Exception as e:
        error_msg = f"Erro ao gerar back-line: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg,
            "user_id": user_id
        }), 500

@cnh_test_bp.route('/cnh-front/<int:user_id>', methods=['GET'])
def generate_front_cnh_test(user_id):
    """
    Gera imagem da frente para teste
    
    GET /api/test/cnh-front/117
    """
    try:
        logger.info(f"🧪 Iniciando teste de geração frente-cnh para user_id: {user_id}")
        
        # Criar objeto de teste
        test_request = CNHTestRequest(user_id)
        
        # Criar gerador
        generator = CNHImageGenerator()
        
        # Definir path de saída
        output_dir = f"static/uploads/user/{user_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        output_path = os.path.join(output_dir, "front.png")
        
        # Gerar imagem frente
        result_path = generator.generate_basic_cnh(test_request, output_path)
        
        # Verificar se arquivo foi criado
        if os.path.exists(result_path):
            file_size = os.path.getsize(result_path)
            
            response_data = {
                "success": True,
                "message": f"Frente da CNH gerada com sucesso para user {user_id}",
                "user_id": user_id,
                "file_path": result_path,
                "file_size": file_size,
                "template_used": "front-cnh.png",
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"✅ Frente gerada: {result_path} ({file_size} bytes)")
            return jsonify(response_data), 200
        else:
            error_msg = "Arquivo não foi criado"
            logger.error(f"❌ {error_msg}")
            return jsonify({
                "success": False,
                "error": error_msg,
                "user_id": user_id
            }), 500
            
    except Exception as e:
        error_msg = f"Erro ao gerar frente: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return jsonify({
            "success": False,
            "error": error_msg,
            "user_id": user_id
        }), 500

@cnh_test_bp.route('/info', methods=['GET'])
def api_info():
    """Informações sobre a API de teste"""
    return jsonify({
        "name": "CNH Test API",
        "version": "1.0",
        "endpoints": {
            "cnh-back": "GET /api/test/cnh-back/<user_id> - Gera back-line.png",
            "cnh-front": "GET /api/test/cnh-front/<user_id> - Gera frente da CNH",
            "info": "GET /api/test/info - Esta página"
        },
        "examples": [
            "curl -X GET 'http://localhost:5001/api/test/cnh-back/117'",
            "curl -X GET 'http://localhost:5001/api/test/cnh-front/117'"
        ]
    })