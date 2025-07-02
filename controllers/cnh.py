# -*- coding: utf-8 -*-
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
        'Larissa', 'Diego', 'Amanda', 'Thiago', 'Carla', 'Vinícius', 'Renata',
        'Rodrigo', 'Patrícia', 'Marcelo', 'Daniela', 'André', 'Vanessa', 'Gabriel',
        'Priscila', 'Leonardo', 'Tatiana', 'Fábio', 'Mônica', 'Ricardo', 'Sandra',
        'José', 'Antônio', 'Francisco', 'Luís', 'Paulo', 'César', 'Ângela', 'Cláudia',
        'Adriana', 'Aline', 'Álvaro', 'Ângelo', 'Antônia', 'Bárbara', 'Bruna', 'Caio',
        'Cátia', 'Célia', 'Cristóvão', 'Débora', 'Édson', 'Érica', 'Fabrícia', 'Fátima',
        'Gérson', 'Gláucia', 'Hélio', 'Inês', 'Íris', 'Jéssica', 'Jônatas', 'Júlia',
        'Lúcio', 'Márcio', 'Mônica', 'Nádia', 'Óscar', 'Patrícia', 'Raúl', 'Sônia',
        'Tânia', 'Válter', 'Vítor', 'Yágara', 'Zélia'
    ]
    
    sobrenomes = [
        'Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves',
        'Pereira', 'Lima', 'Gomes', 'Ribeiro', 'Carvalho', 'Almeida', 'Lopes',
        'Monteiro', 'Araújo', 'Fernandes', 'Rocha', 'Dias', 'Moreira', 'Nunes',
        'Mendes', 'Ramos', 'Vieira', 'Rezende', 'Barbosa', 'Martins', 'Nascimento',
        'Costa', 'Pinto', 'Moura', 'Cavalcanti', 'Teixeira', 'Correia', 'Farias',
        'Gonçalves', 'Conceição', 'Gusmão', 'Espíndola', 'Gusmão', 'Brandão',
        'Leão', 'Magalhães', 'Sebastião', 'Ângelo', 'Cristóvão', 'Estêvão'
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
        'Maria Silva Santos', 'Ana Oliveira Costa', 'Francisca Lima Souza', 'Antônia Ferreira Alves',
        'Conceição Pereira Gomes', 'Rosa Santos Lima', 'Josefa Rodrigues Silva', 'Helena Costa Oliveira',
        'Isabel Souza Ferreira', 'Carmen Alves Pereira', 'Lúcia Santos Gomes', 'Terezinha Lima Costa',
        'Aparecida Silva Souza', 'Margarida Oliveira Santos', 'Sebastiana Costa Lima', 'Cláudia Martins Rocha',
        'Inês Gonçalves Silva', 'Ângela Magalhães Costa', 'Fátima Brandão Santos', 'Sônia Araújo Lima',
        'Tânia Conceição Oliveira', 'Nádia Espíndola Souza', 'Débora Gusmão Silva', 'Cátia Leão Pereira'
    ]
    
    nomes_pai = [
        'João Silva Santos', 'Carlos Oliveira Costa', 'Antônio Lima Souza', 'José Ferreira Alves',
        'Francisco Pereira Gomes', 'Manuel Santos Lima', 'Pedro Rodrigues Silva', 'Paulo Costa Oliveira',
        'Luís Souza Ferreira', 'Roberto Alves Pereira', 'Eduardo Santos Gomes', 'Ricardo Lima Costa',
        'Fernando Silva Souza', 'Marcos Oliveira Santos', 'Alexandre Costa Lima', 'César Barbosa Fernandes',
        'Álvaro Gonçalves Silva', 'Édson Magalhães Costa', 'Hélio Brandão Santos', 'Márcio Araújo Lima',
        'Vítor Conceição Oliveira', 'Raúl Espíndola Souza', 'Lúcio Gusmão Silva', 'Óscar Leão Pereira'
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
        'nome_pai': random.choice(nomes_pai) if random.random() < 0.8 else None,  # 80% chance de ter pai
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
    Endpoint para gerar nova CNH com suporte a upload de arquivos.
    
    Aceita tanto JSON quanto FormData com arquivos.
    
    Form Data ou JSON:
    {
        "nome_completo": "João Silva",
        "cpf": "123.456.789-09", 
        "data_nascimento": "1990-01-01",
        "categoria": "B",
        "foto_3x4": (arquivo),
        "assinatura": (arquivo)
    }
    """
    try:
        user_id = session['user_id']
        
        # Verificar se é FormData (com arquivos) ou JSON
        logger.info(f"Content-Type recebido: {request.content_type}")
        
        if request.content_type and 'multipart/form-data' in request.content_type:
            # FormData com possíveis arquivos
            dados = request.form.to_dict()
            files = request.files
            logger.info(f"✅ FormData detectado - User ID: {user_id}")
            logger.info(f"📄 Dados do form: {list(dados.keys())}")
            logger.info(f"📁 Arquivos recebidos: {list(files.keys())}")
            for filename, file_obj in files.items():
                logger.info(f"   📷 {filename}: {file_obj.filename} ({file_obj.content_type})")
        else:
            # JSON tradicional
            dados = request.get_json()
            files = {}
            logger.info(f"📝 JSON tradicional detectado - User ID: {user_id}")
            
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
        
        # Processar arquivos uploadados
        upload_success, upload_error = _process_uploaded_files(cnh_request, files)
        if not upload_success:
            logger.warning(f"Erro no upload de arquivos - CNH ID: {cnh_request.id}, Erro: {upload_error}")
            # Continuar mesmo com erro no upload (arquivos são opcionais)
        
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

# ==================== FUNÇÕES AUXILIARES ====================

def _process_uploaded_files(cnh_request, files):
    """
    Processa arquivos uploadados (foto 3x4 e assinatura) e salva no sistema.
    
    Args:
        cnh_request: Objeto CNHRequest
        files: Dicionário de arquivos do request.files
        
    Returns:
        tuple: (success: bool, error_message: str)
    """
    try:
        import uuid
        from werkzeug.utils import secure_filename
        
        # Diretório para uploads
        upload_dir = os.path.join('static', 'uploads', 'cnh', str(cnh_request.id))
        os.makedirs(upload_dir, exist_ok=True)
        
        # Extensões permitidas para imagens
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        
        def is_allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
        
        files_processed = 0
        
        # Processar foto 3x4 (RG)
        if 'foto_3x4' in files and files['foto_3x4'].filename:
            foto_file = files['foto_3x4']
            
            if is_allowed_file(foto_file.filename):
                # Gerar nome único para o arquivo
                filename = secure_filename(foto_file.filename)
                extension = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"foto_3x4_{uuid.uuid4().hex[:8]}.{extension}"
                
                # Salvar arquivo
                foto_path = os.path.join(upload_dir, unique_filename)
                foto_file.save(foto_path)
                
                # Atualizar CNH request com caminho da foto
                cnh_request.foto_3x4_path = foto_path
                files_processed += 1
                
                logger.info(f"Foto 3x4 salva - CNH ID: {cnh_request.id}, Arquivo: {foto_path}")
            else:
                logger.warning(f"Arquivo de foto 3x4 inválido - CNH ID: {cnh_request.id}, Arquivo: {foto_file.filename}")
        
        # Processar assinatura
        if 'assinatura' in files and files['assinatura'].filename:
            assinatura_file = files['assinatura']
            
            if is_allowed_file(assinatura_file.filename):
                # Gerar nome único para o arquivo
                filename = secure_filename(assinatura_file.filename)
                extension = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"assinatura_{uuid.uuid4().hex[:8]}.{extension}"
                
                # Salvar arquivo
                assinatura_path = os.path.join(upload_dir, unique_filename)
                assinatura_file.save(assinatura_path)
                
                # Atualizar CNH request com caminho da assinatura
                cnh_request.assinatura_path = assinatura_path
                files_processed += 1
                
                logger.info(f"Assinatura salva - CNH ID: {cnh_request.id}, Arquivo: {assinatura_path}")
            else:
                logger.warning(f"Arquivo de assinatura inválido - CNH ID: {cnh_request.id}, Arquivo: {assinatura_file.filename}")
        
        # Salvar alterações no banco
        if files_processed > 0:
            db.session.commit()
            logger.info(f"Arquivos processados com sucesso - CNH ID: {cnh_request.id}, Total: {files_processed}")
        
        return True, f"{files_processed} arquivo(s) processado(s)"
        
    except Exception as e:
        logger.error(f"Erro ao processar arquivos uploadados - CNH ID: {cnh_request.id}, Erro: {str(e)}")
        return False, f"Erro no upload: {str(e)}" 