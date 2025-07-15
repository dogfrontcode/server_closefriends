# controllers/cnh.py
from flask import Blueprint, request, jsonify, session, send_file
from models.cnh_request import CNHRequest
from models.user import User
from models import db
from services.cnh_generator import gerar_cnh_basica
from datetime import datetime, timedelta
import threading
import logging
import os
import random
import string

logger = logging.getLogger(__name__)

# Blueprint para rotas CNH
cnh_bp = Blueprint('cnh', __name__, url_prefix='/api/cnh')

# ==================== FUNÇÕES AUXILIARES PARA DADOS ALEATÓRIOS ====================

def gerar_cpf_aleatorio():
    """Gera um CPF válido aleatório."""
    def calcular_digito(cpf, peso):
        soma = sum(int(cpf[i]) * peso[i] for i in range(len(peso)))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    
    # Gera 9 primeiros dígitos
    cpf = [random.randint(0, 9) for _ in range(9)]
    
    # Calcula os dígitos verificadores
    cpf.append(calcular_digito(cpf, [10, 9, 8, 7, 6, 5, 4, 3, 2]))
    cpf.append(calcular_digito(cpf, [11, 10, 9, 8, 7, 6, 5, 4, 3, 2]))
    
    return ''.join(map(str, cpf))

def gerar_rg_aleatorio():
    """Gera um RG aleatório."""
    return ''.join([str(random.randint(0, 9)) for _ in range(9)])

def gerar_nome_aleatorio():
    """Gera um nome completo aleatório."""
    nomes = [
        'João', 'Maria', 'Pedro', 'Ana', 'Carlos', 'Mariana', 'Lucas', 'Juliana',
        'Bruno', 'Fernanda', 'Rafael', 'Camila', 'Gustavo', 'Beatriz', 'Felipe',
        'Larissa', 'Diego', 'Amanda', 'Thiago', 'Carla', 'Vinicius', 'Renata',
        'Rodrigo', 'Patricia', 'Marcelo', 'Daniela', 'André', 'Vanessa', 'Gabriel',
        'Priscila', 'Leonardo', 'Tatiana', 'Fabio', 'Monica', 'Ricardo', 'Sandra'
    ]
    
    sobrenomes = [
        'Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves',
        'Pereira', 'Lima', 'Gomes', 'Ribeiro', 'Carvalho', 'Almeida', 'Lopes',
        'Monteiro', 'Araújo', 'Fernandes', 'Rocha', 'Dias', 'Moreira', 'Nunes',
        'Mendes', 'Ramos', 'Vieira', 'Rezende', 'Barbosa', 'Martins', 'Nascimento',
        'Costa', 'Pinto', 'Moura', 'Cavalcanti', 'Teixeira', 'Correia', 'Farias'
    ]
    
    nome = random.choice(nomes)
    sobrenome1 = random.choice(sobrenomes)
    sobrenome2 = random.choice(sobrenomes)
    
    return f"{nome} {sobrenome1} {sobrenome2}"

def gerar_data_nascimento_aleatoria():
    """Gera uma data de nascimento aleatória (idade entre 18 e 80 anos)."""
    hoje = datetime.now()
    idade_min = 18
    idade_max = 80
    
    ano_nascimento = hoje.year - random.randint(idade_min, idade_max)
    mes = random.randint(1, 12)
    dia = random.randint(1, 28)  # Evita problemas com dias inválidos
    
    return datetime(ano_nascimento, mes, dia).date()

def gerar_dados_cnh_aleatorios():
    """Gera um conjunto completo de dados aleatórios para CNH."""
    cidades_brasileiras = [
        'São Paulo', 'Rio de Janeiro', 'Belo Horizonte', 'Salvador', 'Fortaleza',
        'Brasília', 'Curitiba', 'Recife', 'Porto Alegre', 'Manaus', 'Belém',
        'Goiânia', 'Guarulhos', 'Campinas', 'São Luís', 'São Gonçalo', 'Maceió',
        'Duque de Caxias', 'Natal', 'Teresina', 'Campo Grande', 'Nova Iguaçu',
        'São Bernardo do Campo', 'João Pessoa', 'Santo André', 'Osasco'
    ]
    
    ufs = ['SP', 'RJ', 'MG', 'BA', 'SC', 'RS', 'PR', 'GO', 'PE', 'CE', 'AM', 'PA', 'MA', 'PB', 'ES', 'MT', 'MS', 'AL', 'RN', 'PI', 'SE', 'RO', 'AC', 'AP', 'RR', 'TO', 'DF']
    
    categorias = ['A', 'B', 'C', 'D', 'E', 'AB', 'AC', 'AD', 'AE']
    
    nomes_mae = [
        'Maria Silva Santos', 'Ana Oliveira Costa', 'Francisca Lima Souza', 'Antonia Ferreira Alves',
        'Conceição Pereira Gomes', 'Rosa Santos Lima', 'Josefa Rodrigues Silva', 'Helena Costa Oliveira',
        'Isabel Souza Ferreira', 'Carmen Alves Pereira', 'Lucia Santos Gomes', 'Terezinha Lima Costa',
        'Aparecida Silva Souza', 'Margarida Oliveira Santos', 'Sebastiana Costa Lima'
    ]
    
    data_nascimento = gerar_data_nascimento_aleatoria()
    uf_escolhida = random.choice(ufs)
    cidade_escolhida = random.choice(cidades_brasileiras)
    
    return {
        'nome_completo': gerar_nome_aleatorio(),
        'cpf': gerar_cpf_aleatorio(),
        'doc_identidade_numero': gerar_rg_aleatorio(),
        'doc_identidade_orgao': 'SSP',
        'doc_identidade_uf': uf_escolhida,
        'data_nascimento': data_nascimento,
        'local_nascimento': cidade_escolhida,
        'uf_nascimento': uf_escolhida,
        'sexo_condutor': random.choice(['M', 'F']),
        'categoria_habilitacao': random.choice(categorias),
        'primeira_habilitacao': data_nascimento.replace(year=data_nascimento.year + random.randint(18, 25)),
        'nome_mae': random.choice(nomes_mae),
        'nacionalidade': 'BRASILEIRA',
        'uf_cnh': uf_escolhida,
        'local_municipio': cidade_escolhida,
        'local_uf': uf_escolhida,
        'acc': random.choice(['SIM', 'NAO'])
    }

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
        per_page = min(request.args.get('per_page', 20, type=int), 50)  # Padrão 20, máximo 50
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

# ==================== ENDPOINT PÚBLICO ====================

@cnh_bp.route('/view/<int:cnh_id>', methods=['GET'])
def view_cnh_public(cnh_id):
    """
    Endpoint público para visualizar CNH sem autenticação.
    
    Usage: GET /api/cnh/view/123
    """
    try:
        # Buscar CNH por ID (sem filtrar por user_id)
        cnh_request = CNHRequest.query.filter_by(id=cnh_id).first()
        
        if not cnh_request:
            return jsonify({'error': 'CNH não encontrada'}), 404
        
        # Verificar se a CNH foi gerada com sucesso
        if not cnh_request.can_download():
            return jsonify({'error': 'CNH não está disponível'}), 400
        
        # Verificar se arquivo existe
        if not os.path.exists(cnh_request.generated_image_path):
            logger.error(f"Arquivo CNH não encontrado - ID: {cnh_id}, Path: {cnh_request.generated_image_path}")
            return jsonify({'error': 'Arquivo da CNH não encontrado'}), 404
        
        # Log da visualização pública
        logger.info(f"Visualização pública CNH - ID: {cnh_id}, Nome: {cnh_request.nome_completo}")
        
        # Retornar arquivo da CNH diretamente
        return send_file(
            cnh_request.generated_image_path,
            mimetype='image/png',
            as_attachment=False,  # Para exibir no navegador
            download_name=f"CNH_{cnh_id}.png"
        )
        
    except Exception as e:
        logger.error(f"Erro na visualização pública - CNH ID: {cnh_id}, Erro: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@cnh_bp.route('/info/<int:cnh_id>', methods=['GET'])
def get_cnh_info_public(cnh_id):
    """
    Endpoint público para obter informações básicas da CNH sem autenticação.
    
    Usage: GET /api/cnh/info/123
    """
    try:
        # Buscar CNH por ID
        cnh_request = CNHRequest.query.filter_by(id=cnh_id).first()
        
        if not cnh_request:
            return jsonify({'error': 'CNH não encontrada'}), 404
        
        # Retornar apenas informações básicas (sem dados sensíveis)
        cnh_info = {
            'id': cnh_request.id,
            'nome_completo': cnh_request.nome_completo,
            'categoria_habilitacao': cnh_request.categoria_habilitacao,
            'status': cnh_request.status,
            'data_criacao': cnh_request.created_at.strftime('%d/%m/%Y %H:%M:%S'),
            'can_view': cnh_request.can_download(),
            'image_url': f'/api/cnh/view/{cnh_id}' if cnh_request.can_download() else None
        }
        
        # Log da consulta
        logger.info(f"Consulta pública CNH info - ID: {cnh_id}")
        
        return jsonify({
            'success': True,
            'cnh': cnh_info
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na consulta pública - CNH ID: {cnh_id}, Erro: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@cnh_bp.route('/query/<int:cnh_id>', methods=['GET'])
def query_cnh_database(cnh_id):
    """
    Endpoint público para consultar TODOS os dados da CNH diretamente no banco.
    Retorna todos os campos do formulário original sem filtros.
    
    Usage: GET /api/cnh/query/222
    """

    
    try:
        # Buscar CNH por ID diretamente no banco
        cnh_request = CNHRequest.query.filter_by(id=cnh_id).first()
        
        if not cnh_request:
            return jsonify({
                'success': False,
                'error': 'CNH não encontrada no banco de dados',
                'id_consultado': cnh_id
            }), 404
        
        # Retornar TODOS os dados do formulário/banco
        dados_completos = {
            'id': cnh_request.id,
            'user_id': cnh_request.user_id,
            
            # Dados pessoais básicos
            'nome_completo': cnh_request.nome_completo,
            'cpf': cnh_request.cpf,
            'data_nascimento': cnh_request.data_nascimento.isoformat() if cnh_request.data_nascimento else None,
            'local_nascimento': cnh_request.local_nascimento,
            'uf_nascimento': cnh_request.uf_nascimento,
            'nacionalidade': cnh_request.nacionalidade,
            'nome_pai': cnh_request.nome_pai,
            'nome_mae': cnh_request.nome_mae,
            'sexo_condutor': cnh_request.sexo_condutor,
            
            # Documento de identidade
            'doc_identidade_numero': cnh_request.doc_identidade_numero,
            'doc_identidade_orgao': cnh_request.doc_identidade_orgao,
            'doc_identidade_uf': cnh_request.doc_identidade_uf,
            
            # Datas da CNH
            'primeira_habilitacao': cnh_request.primeira_habilitacao.isoformat() if cnh_request.primeira_habilitacao else None,
            'data_emissao': cnh_request.data_emissao.isoformat() if cnh_request.data_emissao else None,
            'validade': cnh_request.validade.isoformat() if cnh_request.validade else None,
            
            # Configurações da CNH
            'categoria_habilitacao': cnh_request.categoria_habilitacao,
            'acc': cnh_request.acc,
            'uf_cnh': cnh_request.uf_cnh,
            
            # Números de controle
            'numero_registro': cnh_request.numero_registro,
            'numero_espelho': cnh_request.numero_espelho,
            'codigo_validacao': cnh_request.codigo_validacao,
            'numero_renach': cnh_request.numero_renach,
            
            # Local da habilitação
            'local_municipio': cnh_request.local_municipio,
            'local_uf': cnh_request.local_uf,
            
            # Outras informações
            'categorias_adicionais': cnh_request.categorias_adicionais,
            'observacoes': cnh_request.observacoes,
            
            # Caminhos dos arquivos
            'foto_3x4_path': cnh_request.foto_3x4_path,
            'assinatura_path': cnh_request.assinatura_path,
            'generated_image_path': cnh_request.generated_image_path,
            
            # Controle do sistema
            'status': cnh_request.status,
            'custo': cnh_request.custo,
            'error_message': cnh_request.error_message,
            'created_at': cnh_request.created_at.isoformat() if cnh_request.created_at else None,
            'completed_at': cnh_request.completed_at.isoformat() if cnh_request.completed_at else None,
            
            # URLs e informações úteis
            'image_url': f'/api/cnh/view/{cnh_id}' if cnh_request.can_download() else None,
            'can_download': cnh_request.can_download(),
            'status_display': cnh_request.get_status_display() if hasattr(cnh_request, 'get_status_display') else cnh_request.status
        }
        
        # Log da consulta
        logger.info(f"Consulta completa no banco - CNH ID: {cnh_id}, Nome: {cnh_request.nome_completo}")
        
        return jsonify({
            'success': True,
            'message': 'Dados obtidos diretamente do banco de dados',
            'id_consultado': cnh_id,
            'dados_formulario': dados_completos
        }), 200
        
    except Exception as e:
        logger.error(f"Erro na consulta do banco - CNH ID: {cnh_id}, Erro: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}',
            'id_consultado': cnh_id
        }), 500

@cnh_bp.route('/generate-random', methods=['GET'])
def generate_random_cnh():
    """
    Endpoint público para gerar CNH automaticamente com dados aleatórios (versão assíncrona).
    
    Usage: GET /api/cnh/generate-random
    """
    return _generate_random_cnh_internal(async_generation=True)

@cnh_bp.route('/generate-random-sync', methods=['GET'])
def generate_random_cnh_sync():
    """
    Endpoint público para gerar CNH automaticamente com dados aleatórios (versão síncrona).
    
    Usage: GET /api/cnh/generate-random-sync
    
    Aguarda a geração completa antes de retornar.
    """
    return _generate_random_cnh_internal(async_generation=False)

def _generate_random_cnh_internal(async_generation=True):
    """
    Endpoint público para gerar CNH automaticamente com dados aleatórios.
    
    Usage: GET /api/cnh/generate-random
    
    Retorna:
    - success: Se a geração foi bem-sucedida
    - cnh_id: ID da CNH gerada
    - image_url: URL para visualizar a CNH
    - info_url: URL para obter informações da CNH
    """
    try:
        # Gerar dados aleatórios
        dados_aleatorios = gerar_dados_cnh_aleatorios()
        
        logger.info(f"Gerando CNH com dados aleatórios - Nome: {dados_aleatorios['nome_completo']}")
        
        # Criar usuário fictício ou usar um padrão para CNHs aleatórias
        # Vamos usar user_id = 1 como padrão para CNHs públicas aleatórias
        user_id_publico = 1
        
        # Verificar se o usuário existe, se não, criar um usuário padrão
        user = User.query.get(user_id_publico)
        if not user:
            # Criar usuário padrão para CNHs públicas
            user = User(
                username='public_generator',
                email='public@cnh.generator',
                credits=999999  # Créditos ilimitados para geração pública
            )
            user.set_password('public123')
            db.session.add(user)
            db.session.commit()
            logger.info("Usuário público criado para CNHs aleatórias")
        
        # Criar registro de CNH com dados aleatórios
        cnh_request = CNHRequest(
            user_id=user_id_publico,
            nome_completo=dados_aleatorios['nome_completo'],
            cpf=dados_aleatorios['cpf'],
            doc_identidade_numero=dados_aleatorios['doc_identidade_numero'],
            doc_identidade_orgao=dados_aleatorios['doc_identidade_orgao'],
            doc_identidade_uf=dados_aleatorios['doc_identidade_uf'],
            data_nascimento=dados_aleatorios['data_nascimento'],
            local_nascimento=dados_aleatorios['local_nascimento'],
            uf_nascimento=dados_aleatorios['uf_nascimento'],
            sexo_condutor=dados_aleatorios['sexo_condutor'],
            categoria_habilitacao=dados_aleatorios['categoria_habilitacao'],
            primeira_habilitacao=dados_aleatorios['primeira_habilitacao'],
            nome_mae=dados_aleatorios['nome_mae'],
            nacionalidade=dados_aleatorios['nacionalidade'],
            uf_cnh=dados_aleatorios['uf_cnh'],
            local_municipio=dados_aleatorios['local_municipio'],
            local_uf=dados_aleatorios['local_uf'],
            acc=dados_aleatorios['acc']
        )
        
        # Salvar no banco
        db.session.add(cnh_request)
        db.session.commit()
        
        logger.info(f"CNH aleatória criada no banco - ID: {cnh_request.id}")
        
        if async_generation:
            # Gerar a imagem da CNH em background
            def gerar_cnh_async():
                from flask import current_app
                try:
                    with current_app.app_context():
                        sucesso, caminho_imagem, erro = gerar_cnh_basica(cnh_request)
                        if sucesso:
                            logger.info(f"CNH aleatória gerada com sucesso - ID: {cnh_request.id}, Arquivo: {caminho_imagem}")
                        else:
                            logger.error(f"Erro na geração da CNH aleatória - ID: {cnh_request.id}, Erro: {erro}")
                except Exception as e:
                    logger.error(f"Erro na thread de geração - ID: {cnh_request.id}, Erro: {str(e)}")
            
            # Iniciar geração em background
            thread = threading.Thread(target=gerar_cnh_async)
            thread.daemon = True
            thread.start()
            
            # Retornar resposta imediata com URLs
            return jsonify({
                'success': True,
                'message': 'CNH aleatória criada! A imagem está sendo gerada...',
                'cnh_id': cnh_request.id,
                'nome_completo': cnh_request.nome_completo,
                'cpf': cnh_request.cpf,
                'categoria': cnh_request.categoria_habilitacao,
                'image_url': f'/api/cnh/view/{cnh_request.id}',
                'info_url': f'/api/cnh/info/{cnh_request.id}',
                'status_check_url': f'/api/cnh/status/{cnh_request.id}',
                'note': 'A imagem estará disponível em alguns segundos. Use image_url para visualizar.'
            }), 201
        else:
            # Gerar a imagem sincronamente
            try:
                sucesso, caminho_imagem, erro = gerar_cnh_basica(cnh_request)
                if sucesso:
                    logger.info(f"CNH aleatória gerada com sucesso (sync) - ID: {cnh_request.id}, Arquivo: {caminho_imagem}")
                    return jsonify({
                        'success': True,
                        'message': 'CNH aleatória gerada com sucesso!',
                        'cnh_id': cnh_request.id,
                        'nome_completo': cnh_request.nome_completo,
                        'cpf': cnh_request.cpf,
                        'categoria': cnh_request.categoria_habilitacao,
                        'image_url': f'/api/cnh/view/{cnh_request.id}',
                        'info_url': f'/api/cnh/info/{cnh_request.id}',
                        'status': 'completed',
                        'note': 'A imagem está pronta para visualização!'
                    }), 201
                else:
                    logger.error(f"Erro na geração síncrona da CNH - ID: {cnh_request.id}, Erro: {erro}")
                    return jsonify({'error': f'Erro na geração: {erro}'}), 500
            except Exception as e:
                logger.error(f"Erro na geração síncrona - ID: {cnh_request.id}, Erro: {str(e)}")
                return jsonify({'error': f'Erro interno: {str(e)}'}), 500
        
    except Exception as e:
        logger.error(f"Erro na geração de CNH aleatória: {str(e)}")
        return jsonify({'error': f'Erro interno: {str(e)}'}), 500 