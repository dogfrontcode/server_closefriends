# controllers/cnh.py
from flask import Blueprint, request, jsonify, session, send_file
from models.cnh_request import CNHRequest
from models.user import User
from services.cnh_generator import gerar_cnh_basica
from datetime import datetime, timedelta
import threading
import logging
import os

logger = logging.getLogger(__name__)

# Blueprint para rotas CNH
cnh_bp = Blueprint('cnh', __name__, url_prefix='/api/cnh')

def require_auth(f):
    """Middleware para verificar autenticação."""
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Usuário não autenticado'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ==================== ENDPOINTS PRINCIPAIS ====================

@cnh_bp.route('/generate', methods=['POST'])
@require_auth
def generate_cnh():
    """
    Endpoint para gerar nova CNH.
    
    Body (JSON):
    {
        "nome_completo": "João Silva",
        "cpf": "123.456.789-09", 
        "rg": "12.345.678-9",
        "data_nascimento": "1990-01-01",
        "categoria": "B"
    }
    """
    try:
        user_id = session['user_id']
        dados = request.get_json()
        
        if not dados:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        logger.info(f"Solicitação de geração CNH - User ID: {user_id}, Dados: {dados.get('nome_completo', 'N/A')}")
        
        # Validar dados
        is_valid, validated_data, errors = CNHRequest.validar_dados_completos(dados)
        
        if not is_valid:
            logger.warning(f"Dados inválidos para CNH - User ID: {user_id}, Erros: {errors}")
            return jsonify({
                'error': 'Dados inválidos',
                'details': errors
            }), 400
        
        # Criar CNH request
        success, cnh_request, error_msg = CNHRequest.criar_cnh_request(user_id, validated_data)
        
        if not success:
            logger.error(f"Erro ao criar CNH request - User ID: {user_id}, Erro: {error_msg}")
            return jsonify({'error': error_msg}), 400
        
        # Gerar imagem em background (assíncrono)
        def generate_async():
            try:
                from __init__ import app
                with app.app_context():
                    gerar_cnh_basica(cnh_request)
            except Exception as e:
                logger.error(f"Erro na geração assíncrona - CNH ID: {cnh_request.id}, Erro: {str(e)}")
        
        # Iniciar geração em thread separada
        generation_thread = threading.Thread(target=generate_async)
        generation_thread.daemon = True
        generation_thread.start()
        
        # Retornar resposta imediata
        return jsonify({
            'success': True,
            'message': 'CNH criada com sucesso! Geração em andamento...',
            'cnh': cnh_request.to_dict()
        }), 201
        
    except Exception as e:
        logger.error(f"Erro interno na geração CNH - User ID: {session.get('user_id')}, Erro: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@cnh_bp.route('/my-cnhs', methods=['GET'])
@require_auth
def get_my_cnhs():
    """
    Endpoint para listar CNHs do usuário.
    Verifica automaticamente CNHs pendentes com timeout de 15 segundos.
    
    Query params opcionais:
    - page: página (default 1)
    - per_page: itens por página (default 10)
    - status: filtrar por status
    """
    try:
        user_id = session['user_id']
        
        # VERIFICAR E CORRIGIR CNHs PENDENTES ANTES DE RETORNAR DADOS
        check_and_fix_pending_cnhs()
        
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 10, type=int), 50)  # Máximo 50
        status_filter = request.args.get('status')
        
        # Query base
        query = CNHRequest.query.filter_by(user_id=user_id)
        
        # Filtro por status
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        # Ordenar por data (mais recentes primeiro)
        query = query.order_by(CNHRequest.created_at.desc())
        
        # Paginação
        pagination = query.paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        cnhs = pagination.items
        
        # Estatísticas do usuário
        stats = get_user_cnh_stats(user_id)
        
        return jsonify({
            'success': True,
            'cnhs': [cnh.to_dict() for cnh in cnhs],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            },
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar CNHs - User ID: {session.get('user_id')}, Erro: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@cnh_bp.route('/details/<int:cnh_id>', methods=['GET'])
@require_auth
def get_cnh_details(cnh_id):
    """
    Endpoint para obter detalhes completos da CNH para exibição no modal.
    """
    try:
        user_id = session['user_id']
        
        # Buscar CNH
        cnh_request = CNHRequest.query.filter_by(
            id=cnh_id, 
            user_id=user_id
        ).first()
        
        if not cnh_request:
            return jsonify({'error': 'CNH não encontrada'}), 404
        
        # Converter para dict com todos os campos
        cnh_data = cnh_request.to_dict()
        
        # Adicionar informações de status legível
        status_map = {
            'pending': 'Pendente',
            'processing': 'Processando',
            'completed': 'Concluída',
            'failed': 'Falhou'
        }
        cnh_data['status_display'] = status_map.get(cnh_request.status, 'Desconhecido')
        
        # Verificar se pode baixar e se tem imagem
        can_download = cnh_request.can_download()
        cnh_data['can_download'] = can_download
        
        if can_download and cnh_request.generated_image_path:
            # Gerar URL para visualização da imagem
            cnh_data['image_url'] = f'/api/cnh/download/{cnh_id}'
        else:
            cnh_data['image_url'] = None
        
        # Log da visualização
        logger.info(f"Detalhes CNH visualizados - User: {session.get('username')}, CNH ID: {cnh_id}")
        
        return jsonify({
            'success': True,
            'cnh': cnh_data
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes CNH - CNH ID: {cnh_id}, User ID: {session.get('user_id')}, Erro: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500


@cnh_bp.route('/download/<int:cnh_id>', methods=['GET'])
@require_auth
def download_cnh(cnh_id):
    """
    Endpoint para download da imagem CNH.
    """
    try:
        user_id = session['user_id']
        
        # Buscar CNH
        cnh_request = CNHRequest.query.filter_by(
            id=cnh_id, 
            user_id=user_id
        ).first()
        
        if not cnh_request:
            return jsonify({'error': 'CNH não encontrada'}), 404
        
        if not cnh_request.can_download():
            return jsonify({'error': 'CNH não está disponível para download'}), 400
        
        # Verificar se arquivo existe
        if not os.path.exists(cnh_request.generated_image_path):
            logger.error(f"Arquivo CNH não encontrado - ID: {cnh_id}, Path: {cnh_request.generated_image_path}")
            return jsonify({'error': 'Arquivo não encontrado'}), 404
        
        # Log do download
        logger.info(f"Download CNH - User: {session.get('username')}, CNH ID: {cnh_id}")
        
        # Enviar arquivo
        return send_file(
            cnh_request.generated_image_path,
            as_attachment=True,
            download_name=f"CNH_{cnh_request.nome_completo.replace(' ', '_')}_{cnh_id}.png",
            mimetype='image/png'
        )
        
    except Exception as e:
        logger.error(f"Erro no download - CNH ID: {cnh_id}, User ID: {session.get('user_id')}, Erro: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@cnh_bp.route('/status/<int:cnh_id>', methods=['GET'])
@require_auth
def get_cnh_status(cnh_id):
    """
    Endpoint para verificar status de uma CNH específica.
    """
    try:
        user_id = session['user_id']
        
        # Buscar CNH
        cnh_request = CNHRequest.query.filter_by(
            id=cnh_id, 
            user_id=user_id
        ).first()
        
        if not cnh_request:
            return jsonify({'error': 'CNH não encontrada'}), 404
        
        return jsonify({
            'success': True,
            'cnh': cnh_request.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao verificar status - CNH ID: {cnh_id}, User ID: {session.get('user_id')}, Erro: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# ==================== ENDPOINTS ADMINISTRATIVOS ====================

@cnh_bp.route('/stats', methods=['GET'])
@require_auth
def get_user_stats():
    """
    Endpoint para estatísticas detalhadas do usuário.
    """
    try:
        user_id = session['user_id']
        stats = get_user_cnh_stats(user_id)
        
        # Estatísticas adicionais
        today = datetime.now().date()
        this_month_start = today.replace(day=1)
        
        # CNHs este mês
        monthly_cnhs = CNHRequest.query.filter(
            CNHRequest.user_id == user_id,
            CNHRequest.created_at >= this_month_start
        ).count()
        
        # Próxima CNH disponível (se atingiu limite diário)
        can_generate, count_today, limit_msg = CNHRequest.pode_gerar_cnh(user_id)
        
        stats.update({
            'monthly': monthly_cnhs,
            'can_generate_today': can_generate,
            'daily_count': count_today,
            'daily_limit': CNHRequest.MAX_CNH_POR_DIA,
            'cost_per_cnh': CNHRequest.CUSTO_PADRAO
        })
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas - User ID: {session.get('user_id')}, Erro: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@cnh_bp.route('/validate', methods=['POST'])
@require_auth
def validate_cnh_data():
    """
    Endpoint para validar dados antes de criar CNH.
    """
    try:
        dados = request.get_json()
        
        if not dados:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Validar dados
        is_valid, validated_data, errors = CNHRequest.validar_dados_completos(dados)
        
        return jsonify({
            'valid': is_valid,
            'errors': errors,
            'validated_data': validated_data if is_valid else None
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na validação - User ID: {session.get('user_id')}, Erro: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

# ==================== FUNÇÕES AUXILIARES ====================

def check_and_fix_pending_cnhs():
    """
    Verifica CNHs pendentes e corrige automaticamente se arquivo existe.
    Timeout de 15 segundos para liberar download.
    """
    try:
        from __init__ import db
        
        # Buscar CNHs pendentes ou em processamento há mais de 15 segundos
        timeout_time = datetime.utcnow() - timedelta(seconds=15)
        
        stuck_cnhs = CNHRequest.query.filter(
            CNHRequest.status.in_(['pending', 'processing']),
            CNHRequest.created_at <= timeout_time
        ).all()
        
        for cnh in stuck_cnhs:
            logger.info(f"Verificando CNH {cnh.id} em timeout (status: {cnh.status})")
            
            # Verificar se arquivo foi gerado
            generated_dir = "static/generated_cnhs"
            expected_files = []
            
            if os.path.exists(generated_dir):
                files = os.listdir(generated_dir)
                for file in files:
                    if f"cnh_{cnh.id:06d}_" in file and file.endswith('.png') and not file.endswith('_thumb.png'):
                        expected_files.append(os.path.join(generated_dir, file))
            
            if expected_files:
                # Arquivo existe, marcar como completa
                latest_file = sorted(expected_files)[-1]
                cnh.status = 'completed'
                cnh.generated_image_path = latest_file
                cnh.error_message = None
                
                logger.info(f"CNH {cnh.id} corrigida automaticamente: {latest_file}")
            else:
                # Arquivo não existe, marcar como falha
                cnh.status = 'failed'
                cnh.error_message = 'Timeout na geração (15 segundos)'
                
                logger.warning(f"CNH {cnh.id} marcada como falha por timeout")
            
            db.session.commit()
            
    except Exception as e:
        logger.error(f"Erro ao verificar CNHs pendentes: {str(e)}")
        try:
            from __init__ import db
            db.session.rollback()
        except:
            pass

def get_user_cnh_stats(user_id):
    """
    Calcula estatísticas de CNH do usuário.
    
    Args:
        user_id (int): ID do usuário
        
    Returns:
        dict: Estatísticas
    """
    try:
        # Data atual
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = today_start + timedelta(days=1)
        
        # Query base
        base_query = CNHRequest.query.filter_by(user_id=user_id)
        
        # Total de CNHs
        total = base_query.count()
        
        # CNHs por status
        completed = base_query.filter_by(status=CNHRequest.STATUS_COMPLETED).count()
        processing = base_query.filter_by(status=CNHRequest.STATUS_PROCESSING).count()
        failed = base_query.filter_by(status=CNHRequest.STATUS_FAILED).count()
        pending = base_query.filter_by(status=CNHRequest.STATUS_PENDING).count()
        
        # CNHs de hoje
        today_count = base_query.filter(
            CNHRequest.created_at >= today_start,
            CNHRequest.created_at < today_end
        ).count()
        
        return {
            'total': total,
            'completed': completed,
            'processing': processing,
            'failed': failed,
            'pending': pending,
            'today': today_count
        }
        
    except Exception as e:
        logger.error(f"Erro ao calcular estatísticas - User ID: {user_id}, Erro: {str(e)}")
        return {
            'total': 0,
            'completed': 0,
            'processing': 0,
            'failed': 0,
            'pending': 0,
            'today': 0
        }

# ==================== HANDLERS DE ERRO ====================

@cnh_bp.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@cnh_bp.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Método não permitido'}), 405

@cnh_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro interno 500 - {str(error)}")
    return jsonify({'error': 'Erro interno do servidor'}), 500

# ==================== MIDDLEWARE DE LOG ====================

@cnh_bp.before_request
def log_request():
    """Log de todas as requisições para endpoints CNH."""
    if request.endpoint and 'cnh' in request.endpoint:
        logger.info(f"CNH API - {request.method} {request.path} - User: {session.get('username', 'N/A')}")

@cnh_bp.after_request
def log_response(response):
    """Log de respostas dos endpoints CNH."""
    if request.endpoint and 'cnh' in request.endpoint:
        logger.info(f"CNH API Response - {request.method} {request.path} - Status: {response.status_code}")
    return response 