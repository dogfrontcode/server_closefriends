# -*- coding: utf-8 -*-
# controllers/cnh.py
from flask import Blueprint, request, jsonify, session, send_file
from models.cnh_request import CNHRequest
from models.user import User
from models import db
from services.cnh_generator import gerar_cnh_basica
from security.rate_limiter import rate_limit_decorator, rate_limiter
from security.validators import SecurityValidator
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
    
    # Gerar números de controle da CNH
    def gerar_numero_registro():
        """Gera número de registro da CNH (11 dígitos)"""
        return ''.join([str(random.randint(0, 9)) for _ in range(11)])
    
    def gerar_numero_espelho():
        """Gera número do espelho da CNH (11 dígitos)"""
        return ''.join([str(random.randint(0, 9)) for _ in range(11)])
    
    def gerar_codigo_validacao():
        """Gera código de validação da CNH (10 dígitos)"""
        return ''.join([str(random.randint(0, 9)) for _ in range(10)])
    
    def gerar_numero_renach(uf):
        """Gera número RENACH (formato UFXXXXXXXXX)"""
        numero = ''.join([str(random.randint(0, 9)) for _ in range(9)])
        return f"{uf}{numero}"
    
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
        'categoria_habilitacao': 'D',  # FORÇANDO CATEGORIA A PARA TESTE
        'primeira_habilitacao': data_nascimento.replace(year=data_nascimento.year + random.randint(18, 25)),
        'nome_mae': random.choice(nomes_mae),
        'nome_pai': random.choice(nomes_pai) if random.random() < 0.8 else None,  # 80% chance de ter pai
        'nacionalidade': 'BRASILEIRA',
        'uf_cnh': uf_escolhida,
        'local_municipio': cidade_escolhida,
        'local_uf': uf_escolhida,
        'acc': random.choice(['SIM', 'NAO']),
        # 🆕 NÚMEROS DE CONTROLE OBRIGATÓRIOS
        'numero_registro': gerar_numero_registro(),
        'numero_espelho': gerar_numero_espelho(),
        'codigo_validacao': gerar_codigo_validacao(),
        'numero_renach': gerar_numero_renach(uf_escolhida)
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
        
        # Capturar o app atual para usar na thread
        from flask import current_app
        app_context = current_app._get_current_object()
        
        # Gerar imagem em background (assíncrono)
        def generate_async():
            try:
                with app_context.app_context():
                    # Obter instância fresh do banco para a thread
                    cnh_fresh = db.session.get(CNHRequest, cnh_request.id)
                    
                    success, paths_dict, error = gerar_cnh_basica(cnh_fresh)
                    if not success:
                        logger.error(f"Falha na geração assíncrona - CNH ID: {cnh_fresh.id}, Erro: {error}")
                    else:
                        front_path = paths_dict["front_path"] if paths_dict else "N/A"
                        logger.info(f"Geração assíncrona bem-sucedida - CNH ID: {cnh_fresh.id}, Frente: {front_path}")
            except Exception as e:
                logger.error(f"Erro na geração assíncrona - CNH ID: {cnh_request.id}, Erro: {str(e)}")
                import traceback
                traceback.print_exc()
        
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
    Verifica automaticamente CNHs pendentes com timeout de 30 segundos.
    
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


@cnh_bp.route('/update/<int:cnh_id>', methods=['PUT'])
@require_auth
def update_cnh(cnh_id):
    """
    Endpoint para atualizar dados da CNH.
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
        
        # Obter dados do request
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados inválidos'}), 400
        
        # Lista de campos que podem ser atualizados
        updateable_fields = [
            'nome_completo', 'cpf', 'data_nascimento', 'sexo_condutor',
            'local_nascimento', 'uf_nascimento', 'nome_pai', 'nome_mae',
            'doc_identidade_numero', 'doc_identidade_orgao', 'doc_identidade_uf',
            'categoria_habilitacao', 'uf_cnh', 'acc', 'local_municipio', 'local_uf',
            'primeira_habilitacao', 'data_emissao', 'validade',
            'numero_registro', 'numero_espelho', 'codigo_validacao', 'numero_renach',
            'observacoes'
        ]
        
        # Atualizar campos
        updated_fields = []
        for field in updateable_fields:
            if field in data:
                old_value = getattr(cnh_request, field)
                new_value = data[field]
                
                # Tratar valores vazios
                if new_value == '':
                    new_value = None
                
                # Converter datas se necessário
                if field in ['data_nascimento', 'primeira_habilitacao', 'data_emissao', 'validade'] and new_value:
                    try:
                        new_value = datetime.strptime(new_value, '%Y-%m-%d').date()
                    except ValueError:
                        return jsonify({'error': f'Data inválida para o campo {field}'}), 400
                
                # Só atualizar se houve mudança
                if old_value != new_value:
                    setattr(cnh_request, field, new_value)
                    updated_fields.append(field)
        
        if not updated_fields:
            return jsonify({'success': True, 'message': 'Nenhuma alteração detectada'}), 200
        
        # Salvar no banco
        db.session.commit()
        
        # Log da atualização
        logger.info(f"CNH atualizada - User: {session.get('username')}, CNH ID: {cnh_id}, Campos: {', '.join(updated_fields)}")
        
        return jsonify({
            'success': True,
            'message': f'CNH atualizada com sucesso. Campos alterados: {", ".join(updated_fields)}',
            'updated_fields': updated_fields
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar CNH - CNH ID: {cnh_id}, User ID: {session.get('user_id')}, Erro: {str(e)}")
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
    Timeout de 30 segundos para liberar download.
    """
    try:
        from __init__ import db
        
        # Buscar CNHs pendentes ou em processamento há mais de 30 segundos
        timeout_time = datetime.utcnow() - timedelta(seconds=30)
        
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
                cnh.error_message = 'Timeout na geração (30 segundos)'
                
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
def get_cnh_info(cnh_id):
    """
    🚀 API OTIMIZADA PARA APPS MÓVEIS - Consulta informações da CNH
    
    Endpoint público otimizado para aplicativos móveis/externos com:
    - Estrutura de dados limpa e organizada
    - Campos formatados para exibição
    - URLs completas para imagens  
    - Campos calculados (idade, tempo de habilitação)
    - Status em português claro
    
    Usage: GET /api/cnh/info/222
    
    Response:
    {
        "success": true,
        "cnh": {
            "id": 222,
            "dados_pessoais": {...},
            "documento": {...},
            "habilitacao": {...},
            "controle": {...},
            "arquivos": {...}
        }
    }
    """
    try:
        # Buscar CNH no banco
        cnh_request = CNHRequest.query.filter_by(id=cnh_id).first()
        
        if not cnh_request:
            return jsonify({
                'success': False,
                'error': 'CNH não encontrada',
                'message': f'Nenhuma CNH encontrada com ID {cnh_id}',
                'id_consultado': cnh_id
            }), 404
        
        # Função auxiliar para formatação de datas
        def format_date(date_obj):
            if not date_obj:
                return None
            return date_obj.strftime('%d/%m/%Y')
        
        def format_iso_date(date_obj):
            if not date_obj:
                return None
            return date_obj.isoformat()
        
        # Calcular idade atual
        idade = cnh_request.get_idade() if hasattr(cnh_request, 'get_idade') else None
        
        # Calcular tempo de habilitação
        tempo_habilitacao = None
        if cnh_request.primeira_habilitacao:
            from datetime import date
            hoje = date.today()
            diff = hoje - cnh_request.primeira_habilitacao
            anos = diff.days // 365
            tempo_habilitacao = f"{anos} ano{'s' if anos != 1 else ''}"
        
        # Status em português claro
        status_map = {
            'pending': 'Aguardando Processamento',
            'processing': 'Processando',
            'completed': 'Concluída',
            'failed': 'Falha na Geração'
        }
        status_display = status_map.get(cnh_request.status, cnh_request.status)
        
        # Estrutura organizada de dados
        response_data = {
            'success': True,
            'message': 'CNH encontrada com sucesso',
            'id_consultado': cnh_id,
            'timestamp_consulta': datetime.utcnow().isoformat(),
            
            'cnh': {
                # Identificação básica
                'id': cnh_request.id,
                'status': cnh_request.status,
                'status_display': status_display,
                'custo': f"R$ {cnh_request.custo:.2f}" if cnh_request.custo else "R$ 0,00",
                
                # 👤 Dados Pessoais
                'dados_pessoais': {
                    'nome_completo': cnh_request.nome_completo or '',
                    'cpf': cnh_request.cpf or '',
                    'data_nascimento': format_date(cnh_request.data_nascimento),
                    'data_nascimento_iso': format_iso_date(cnh_request.data_nascimento),
                    'idade': idade,
                    'sexo': cnh_request.sexo_condutor,
                    'sexo_display': 'Masculino' if cnh_request.sexo_condutor == 'M' else 'Feminino' if cnh_request.sexo_condutor == 'F' else '',
                    'nacionalidade': cnh_request.nacionalidade or 'Brasileiro(a)',
                    'local_nascimento': cnh_request.local_nascimento or '',
                    'uf_nascimento': cnh_request.uf_nascimento or '',
                    'local_nascimento_completo': f"{cnh_request.local_nascimento or ''}/{cnh_request.uf_nascimento or ''}".strip('/'),
                    'nome_pai': cnh_request.nome_pai or '',
                    'nome_mae': cnh_request.nome_mae or ''
                },
                
                # 📄 Documento de Identidade
                'documento': {
                    'numero': cnh_request.doc_identidade_numero or '',
                    'orgao_emissor': cnh_request.doc_identidade_orgao or '',
                    'uf': cnh_request.doc_identidade_uf or '',
                    'documento_completo': f"{cnh_request.doc_identidade_numero or ''} {cnh_request.doc_identidade_orgao or ''}/{cnh_request.doc_identidade_uf or ''}".strip()
                },
                
                # 🚗 Informações da Habilitação
                'habilitacao': {
                    'categoria': cnh_request.categoria_habilitacao or 'B',
                    'primeira_habilitacao': format_date(cnh_request.primeira_habilitacao),
                    'primeira_habilitacao_iso': format_iso_date(cnh_request.primeira_habilitacao),
                    'tempo_habilitacao': tempo_habilitacao,
                    'data_emissao': format_date(cnh_request.data_emissao),
                    'data_emissao_iso': format_iso_date(cnh_request.data_emissao),
                    'validade': format_date(cnh_request.validade),
                    'validade_iso': format_iso_date(cnh_request.validade),
                    'acc': cnh_request.acc or 'NAO',
                    'acc_display': 'Sim' if cnh_request.acc == 'SIM' else 'Não',
                    'uf_cnh': cnh_request.uf_cnh or '',
                    'local_municipio': cnh_request.local_municipio or '',
                    'local_uf': cnh_request.local_uf or '',
                    'local_habilitacao': f"{cnh_request.local_municipio or ''}/{cnh_request.local_uf or ''}".strip('/'),
                    'observacoes': cnh_request.observacoes or ''
                },
                
                # 🔢 Números de Controle
                'controle': {
                    'numero_registro': cnh_request.numero_registro or '',
                    'numero_espelho': cnh_request.numero_espelho or '',
                    'codigo_validacao': cnh_request.codigo_validacao or '',
                    'numero_renach': cnh_request.numero_renach or '',
                    'categorias_adicionais': cnh_request.categorias_adicionais or ''
                },
                
                # 📁 Arquivos e Imagens
                'arquivos': {
                    'foto_3x4_disponivel': bool(cnh_request.foto_3x4_path),
                    'assinatura_disponivel': bool(cnh_request.assinatura_path),
                    'cnh_gerada': bool(cnh_request.generated_image_path and cnh_request.status == 'completed'),
                    'cnh_image_url': f"/api/cnh/view/{cnh_id}" if cnh_request.generated_image_path and cnh_request.status == 'completed' else None,
                    'download_url': f"/api/cnh/download/{cnh_id}" if cnh_request.generated_image_path and cnh_request.status == 'completed' else None
                },
                
                # ⏰ Timestamps
                'datas_sistema': {
                    'criada_em': format_date(cnh_request.created_at),
                    'criada_em_iso': format_iso_date(cnh_request.created_at),
                    'concluida_em': format_date(cnh_request.completed_at),
                    'concluida_em_iso': format_iso_date(cnh_request.completed_at),
                    'tempo_processamento': None
                }
            }
        }
        
        # Calcular tempo de processamento se concluída
        if cnh_request.completed_at and cnh_request.created_at:
            diff = cnh_request.completed_at - cnh_request.created_at
            segundos = diff.total_seconds()
            if segundos < 60:
                tempo_proc = f"{int(segundos)} segundos"
            elif segundos < 3600:
                tempo_proc = f"{int(segundos//60)} minutos"
            else:
                tempo_proc = f"{int(segundos//3600)} horas"
            response_data['cnh']['datas_sistema']['tempo_processamento'] = tempo_proc
        
        # Log da consulta
        logger.info(f"📱 API Info consultada - CNH ID: {cnh_id}, Nome: {cnh_request.nome_completo}, Status: {status_display}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Erro na API Info - CNH ID: {cnh_id}, Erro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'message': 'Erro ao consultar informações da CNH',
            'id_consultado': cnh_id,
            'timestamp_erro': datetime.utcnow().isoformat()
        }), 500

@cnh_bp.route('/info/<int:cnh_id>/summary', methods=['GET'])
def get_cnh_summary(cnh_id):
    """
    📋 API RESUMIDA - Informações essenciais da CNH
    
    Endpoint super leve para consultas rápidas (ideal para listas e previews)
    
    Usage: GET /api/cnh/info/222/summary
    """
    try:
        cnh_request = CNHRequest.query.filter_by(id=cnh_id).first()
        
        if not cnh_request:
            return jsonify({
                'success': False,
                'error': 'CNH não encontrada',
                'id_consultado': cnh_id
            }), 404
        
        # Status em português
        status_map = {
            'pending': 'Aguardando',
            'processing': 'Processando', 
            'completed': 'Pronta',
            'failed': 'Erro'
        }
        
        summary = {
            'success': True,
            'cnh': {
                'id': cnh_request.id,
                'nome': cnh_request.nome_completo or 'Nome não informado',
                'cpf': cnh_request.cpf or '',
                'categoria': cnh_request.categoria_habilitacao or 'B',
                'status': cnh_request.status,
                'status_display': status_map.get(cnh_request.status, cnh_request.status),
                'data_criacao': cnh_request.created_at.strftime('%d/%m/%Y') if cnh_request.created_at else '',
                'imagem_disponivel': bool(cnh_request.generated_image_path and cnh_request.status == 'completed'),
                'download_url': f"/api/cnh/view/{cnh_id}" if cnh_request.generated_image_path and cnh_request.status == 'completed' else None
            }
        }
        
        return jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"❌ Erro na API Summary - CNH ID: {cnh_id}, Erro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno',
            'id_consultado': cnh_id
        }), 500

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
            
            # Arquivos
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
            nome_pai=dados_aleatorios.get('nome_pai'),  # Pode ser None
            nacionalidade=dados_aleatorios['nacionalidade'],
            uf_cnh=dados_aleatorios['uf_cnh'],
            local_municipio=dados_aleatorios['local_municipio'],
            local_uf=dados_aleatorios['local_uf'],
            acc=dados_aleatorios['acc'],
            # 🆕 CAMPOS DE CONTROLE QUE ESTAVAM FALTANDO
            numero_registro=dados_aleatorios['numero_registro'],
            numero_espelho=dados_aleatorios['numero_espelho'],
            codigo_validacao=dados_aleatorios['codigo_validacao'],
            numero_renach=dados_aleatorios['numero_renach']
        )
        
        # 🆕 Definir senha CNH baseada na data de nascimento
        cnh_request.set_senha_cnh()
        
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
                        # Obter instância fresh do banco para a thread
                        cnh_fresh = db.session.get(CNHRequest, cnh_request.id)
                        
                        sucesso, paths_dict, erro = gerar_cnh_basica(cnh_fresh)
                        if sucesso:
                            front_path = paths_dict["front_path"] if paths_dict else "N/A"
                            logger.info(f"CNH aleatória gerada com sucesso - ID: {cnh_fresh.id}, Frente: {front_path}")
                        else:
                            logger.error(f"Erro na geração da CNH aleatória - ID: {cnh_fresh.id}, Erro: {erro}")
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
                sucesso, paths_dict, erro = gerar_cnh_basica(cnh_request)
                if sucesso:
                    front_path = paths_dict["front_path"] if paths_dict else "N/A"
                    logger.info(f"CNH aleatória gerada com sucesso (sync) - ID: {cnh_request.id}, Frente: {front_path}")
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
                        'paths': {
                            'front': paths_dict["front_relative"],
                            'back': paths_dict["back_relative"], 
                            'qrcode': paths_dict["qrcode_relative"]
                        },
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
        from services.path_manager import CNHPathManager
        
        # Usar estrutura de diretórios correta por CPF - pasta uploads
        paths = CNHPathManager.create_cnh_paths(cnh_request)
        upload_dir = paths.uploads_folder
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

@cnh_bp.route('/consultar/<cpf>', methods=['GET'])
def consultar_cnh_por_cpf(cpf):
    """
    🔍 API CONSULTA POR CPF - Busca CNH pelo CPF (como na vida real)
    
    Endpoint para consultar CNH pelo CPF do portador (sem autenticação).
    Retorna a CNH mais recente se houver múltiplas.
    
    Usage: GET /api/cnh/consultar/123.456.789-00
           GET /api/cnh/consultar/12345678900
    
    Response:
    {
        "success": true,
        "cpf_consultado": "123.456.789-00",
        "cnhs_encontradas": 1,
        "cnh": { dados completos da CNH mais recente }
    }
    """
    try:
        # Limpar e formatar CPF (remover pontos e hífens)
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        # Validar CPF básico (11 dígitos)
        if len(cpf_limpo) != 11:
            return jsonify({
                'success': False,
                'error': 'CPF inválido',
                'message': 'CPF deve conter 11 dígitos',
                'cpf_consultado': cpf
            }), 400
        
        # Formatar CPF para busca (pode estar armazenado formatado ou não)
        cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        
        # Buscar CNHs por CPF (tanto formatado quanto não formatado)
        cnhs_formatado = CNHRequest.query.filter_by(cpf=cpf_formatado).all()
        cnhs_limpo = CNHRequest.query.filter_by(cpf=cpf_limpo).all()
        
        # Combinar resultados e remover duplicatas
        cnhs_encontradas = list({cnh.id: cnh for cnh in (cnhs_formatado + cnhs_limpo)}.values())
        
        if not cnhs_encontradas:
            return jsonify({
                'success': False,
                'error': 'CNH não encontrada',
                'message': f'Nenhuma CNH encontrada para o CPF {cpf_formatado}',
                'cpf_consultado': cpf_formatado,
                'cnhs_encontradas': 0
            }), 404
        
        # Ordenar por data de criação (mais recente primeiro)
        cnhs_encontradas.sort(key=lambda x: x.created_at, reverse=True)
        cnh_mais_recente = cnhs_encontradas[0]
        
        # Função auxiliar para formatação de datas
        def format_date(date_obj):
            if not date_obj:
                return None
            return date_obj.strftime('%d/%m/%Y')
        
        def format_iso_date(date_obj):
            if not date_obj:
                return None
            return date_obj.isoformat()
        
        # Calcular idade atual
        idade = cnh_mais_recente.get_idade() if hasattr(cnh_mais_recente, 'get_idade') else None
        
        # Calcular tempo de habilitação
        tempo_habilitacao = None
        if cnh_mais_recente.primeira_habilitacao:
            from datetime import date
            hoje = date.today()
            diff = hoje - cnh_mais_recente.primeira_habilitacao
            anos = diff.days // 365
            tempo_habilitacao = f"{anos} ano{'s' if anos != 1 else ''}"
        
        # Status em português claro
        status_map = {
            'pending': 'Aguardando Processamento',
            'processing': 'Processando',
            'completed': 'Concluída',
            'failed': 'Falha na Geração'
        }
        status_display = status_map.get(cnh_mais_recente.status, cnh_mais_recente.status)
        
        # Estrutura organizada de dados
        response_data = {
            'success': True,
            'message': f'CNH encontrada para CPF {cpf_formatado}',
            'cpf_consultado': cpf_formatado,
            'cnhs_encontradas': len(cnhs_encontradas),
            'timestamp_consulta': datetime.utcnow().isoformat(),
            
            'cnh': {
                # Identificação básica
                'id': cnh_mais_recente.id,
                'status': cnh_mais_recente.status,
                'status_display': status_display,
                'custo': f"R$ {cnh_mais_recente.custo:.2f}" if cnh_mais_recente.custo else "R$ 0,00",
                
                # 👤 Dados Pessoais
                'dados_pessoais': {
                    'nome_completo': cnh_mais_recente.nome_completo or '',
                    'cpf': cpf_formatado,
                    'data_nascimento': format_date(cnh_mais_recente.data_nascimento),
                    'data_nascimento_iso': format_iso_date(cnh_mais_recente.data_nascimento),
                    'idade': idade,
                    'sexo': cnh_mais_recente.sexo_condutor,
                    'sexo_display': 'Masculino' if cnh_mais_recente.sexo_condutor == 'M' else 'Feminino' if cnh_mais_recente.sexo_condutor == 'F' else '',
                    'nacionalidade': cnh_mais_recente.nacionalidade or 'Brasileiro(a)',
                    'local_nascimento': cnh_mais_recente.local_nascimento or '',
                    'uf_nascimento': cnh_mais_recente.uf_nascimento or '',
                    'local_nascimento_completo': f"{cnh_mais_recente.local_nascimento or ''}/{cnh_mais_recente.uf_nascimento or ''}".strip('/'),
                    'nome_pai': cnh_mais_recente.nome_pai or '',
                    'nome_mae': cnh_mais_recente.nome_mae or ''
                },
                
                # 📄 Documento de Identidade
                'documento': {
                    'numero': cnh_mais_recente.doc_identidade_numero or '',
                    'orgao_emissor': cnh_mais_recente.doc_identidade_orgao or '',
                    'uf': cnh_mais_recente.doc_identidade_uf or '',
                    'documento_completo': f"{cnh_mais_recente.doc_identidade_numero or ''} {cnh_mais_recente.doc_identidade_orgao or ''}/{cnh_mais_recente.doc_identidade_uf or ''}".strip()
                },
                
                # 🚗 Informações da Habilitação
                'habilitacao': {
                    'categoria': cnh_mais_recente.categoria_habilitacao or 'B',
                    'primeira_habilitacao': format_date(cnh_mais_recente.primeira_habilitacao),
                    'primeira_habilitacao_iso': format_iso_date(cnh_mais_recente.primeira_habilitacao),
                    'tempo_habilitacao': tempo_habilitacao,
                    'data_emissao': format_date(cnh_mais_recente.data_emissao),
                    'data_emissao_iso': format_iso_date(cnh_mais_recente.data_emissao),
                    'validade': format_date(cnh_mais_recente.validade),
                    'validade_iso': format_iso_date(cnh_mais_recente.validade),
                    'acc': cnh_mais_recente.acc or 'NAO',
                    'acc_display': 'Sim' if cnh_mais_recente.acc == 'SIM' else 'Não',
                    'uf_cnh': cnh_mais_recente.uf_cnh or '',
                    'local_municipio': cnh_mais_recente.local_municipio or '',
                    'local_uf': cnh_mais_recente.local_uf or '',
                    'local_habilitacao': f"{cnh_mais_recente.local_municipio or ''}/{cnh_mais_recente.local_uf or ''}".strip('/'),
                    'observacoes': cnh_mais_recente.observacoes or ''
                },
                
                # 🔢 Números de Controle
                'controle': {
                    'numero_registro': cnh_mais_recente.numero_registro or '',
                    'numero_espelho': cnh_mais_recente.numero_espelho or '',
                    'codigo_validacao': cnh_mais_recente.codigo_validacao or '',
                    'numero_renach': cnh_mais_recente.numero_renach or '',
                    'categorias_adicionais': cnh_mais_recente.categorias_adicionais or ''
                },
                
                # 📁 Arquivos e Imagens
                'arquivos': {
                    'foto_3x4_disponivel': bool(cnh_mais_recente.foto_3x4_path),
                    'assinatura_disponivel': bool(cnh_mais_recente.assinatura_path),
                    'cnh_gerada': bool(cnh_mais_recente.generated_image_path and cnh_mais_recente.status == 'completed'),
                    'cnh_image_url': f"/api/cnh/view/{cnh_mais_recente.id}" if cnh_mais_recente.generated_image_path and cnh_mais_recente.status == 'completed' else None,
                    'download_url': f"/api/cnh/download/{cnh_mais_recente.id}" if cnh_mais_recente.generated_image_path and cnh_mais_recente.status == 'completed' else None
                },
                
                # ⏰ Timestamps
                'datas_sistema': {
                    'criada_em': format_date(cnh_mais_recente.created_at),
                    'criada_em_iso': format_iso_date(cnh_mais_recente.created_at),
                    'concluida_em': format_date(cnh_mais_recente.completed_at),
                    'concluida_em_iso': format_iso_date(cnh_mais_recente.completed_at),
                    'tempo_processamento': None
                }
            }
        }
        
        # Calcular tempo de processamento se concluída
        if cnh_mais_recente.completed_at and cnh_mais_recente.created_at:
            diff = cnh_mais_recente.completed_at - cnh_mais_recente.created_at
            segundos = diff.total_seconds()
            if segundos < 60:
                tempo_proc = f"{int(segundos)} segundos"
            elif segundos < 3600:
                tempo_proc = f"{int(segundos//60)} minutos"
            else:
                tempo_proc = f"{int(segundos//3600)} horas"
            response_data['cnh']['datas_sistema']['tempo_processamento'] = tempo_proc
        
        # Adicionar informações sobre múltiplas CNHs se existirem
        if len(cnhs_encontradas) > 1:
            response_data['aviso'] = f'Encontradas {len(cnhs_encontradas)} CNHs para este CPF. Retornando a mais recente.'
            response_data['outras_cnhs'] = [
                {
                    'id': cnh.id,
                    'criada_em': format_date(cnh.created_at),
                    'status': status_map.get(cnh.status, cnh.status)
                }
                for cnh in cnhs_encontradas[1:]  # Pular a primeira (mais recente)
            ]
        
        # Log da consulta
        logger.info(f"🔍 Consulta por CPF - CPF: {cpf_formatado}, CNHs encontradas: {len(cnhs_encontradas)}, ID retornado: {cnh_mais_recente.id}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Erro na consulta por CPF - CPF: {cpf}, Erro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor',
            'message': 'Erro ao consultar CNH por CPF',
            'cpf_consultado': cpf,
            'timestamp_erro': datetime.utcnow().isoformat()
        }), 500

@cnh_bp.route('/consultar/<cpf>/todas', methods=['GET'])
def consultar_todas_cnhs_por_cpf(cpf):
    """
    📋 API CONSULTA MÚLTIPLAS - Lista todas as CNHs de um CPF
    
    Retorna todas as CNHs encontradas para um CPF específico.
    
    Usage: GET /api/cnh/consultar/123.456.789-00/todas
    """
    try:
        # Limpar e validar CPF
        cpf_limpo = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf_limpo) != 11:
            return jsonify({
                'success': False,
                'error': 'CPF inválido',
                'cpf_consultado': cpf
            }), 400
        
        cpf_formatado = f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
        
        # Buscar todas as CNHs
        cnhs_formatado = CNHRequest.query.filter_by(cpf=cpf_formatado).all()
        cnhs_limpo = CNHRequest.query.filter_by(cpf=cpf_limpo).all()
        cnhs_encontradas = list({cnh.id: cnh for cnh in (cnhs_formatado + cnhs_limpo)}.values())
        
        if not cnhs_encontradas:
            return jsonify({
                'success': False,
                'error': 'Nenhuma CNH encontrada',
                'cpf_consultado': cpf_formatado,
                'total': 0
            }), 404
        
        # Ordenar por data de criação (mais recente primeiro)
        cnhs_encontradas.sort(key=lambda x: x.created_at, reverse=True)
        
        # Status em português
        status_map = {
            'pending': 'Aguardando',
            'processing': 'Processando',
            'completed': 'Pronta',
            'failed': 'Erro'
        }
        
        # Montar lista resumida
        cnhs_lista = []
        for cnh in cnhs_encontradas:
            cnhs_lista.append({
                'id': cnh.id,
                'nome': cnh.nome_completo or 'Nome não informado',
                'categoria': cnh.categoria_habilitacao or 'B',
                'status': cnh.status,
                'status_display': status_map.get(cnh.status, cnh.status),
                'data_criacao': cnh.created_at.strftime('%d/%m/%Y') if cnh.created_at else '',
                'data_criacao_iso': cnh.created_at.isoformat() if cnh.created_at else '',
                'imagem_disponivel': bool(cnh.generated_image_path and cnh.status == 'completed'),
                'download_url': f"/api/cnh/view/{cnh.id}" if cnh.generated_image_path and cnh.status == 'completed' else None
            })
        
        response = {
            'success': True,
            'message': f'Encontradas {len(cnhs_encontradas)} CNH(s) para o CPF {cpf_formatado}',
            'cpf_consultado': cpf_formatado,
            'total': len(cnhs_encontradas),
            'cnhs': cnhs_lista
        }
        
        logger.info(f"📋 Lista completa por CPF - CPF: {cpf_formatado}, Total: {len(cnhs_encontradas)}")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Erro na lista por CPF - CPF: {cpf}, Erro: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Erro interno',
            'cpf_consultado': cpf
        }), 500 

# ==================== FUNÇÕES AUXILIARES PARA PATHS ====================

def _get_cnh_back_path(cnh_request):
    """Retorna o path do verso da CNH baseado na estrutura organizada por CPF."""
    if not cnh_request.generated_image_path:
        return None
    
    import os
    front_path = cnh_request.generated_image_path
    
    # Nova estrutura por CPF: static/uploads/cnh/CPF/front/ID.png -> static/uploads/cnh/CPF/back/ID.png
    if '/front/' in front_path:
        back_path = front_path.replace('/front/', '/back/')
        return back_path if os.path.exists(back_path) else None
    
    # Fallback para estrutura user_X: static/uploads/cnh/user_X/front/ID.png -> static/uploads/cnh/user_X/back/ID.png
    if '/user_' in front_path and '/front/' in front_path:
        back_path = front_path.replace('/front/', '/back/')
        return back_path if os.path.exists(back_path) else None
    
    # Fallback para estrutura antiga (compatibilidade)
    if 'cnh_front_' in front_path:
        back_path = front_path.replace('cnh_front_', 'cnh_back_')
        return back_path if os.path.exists(back_path) else None
    
    return None

def _get_qr_code_path(cnh_request):
    """
    Retorna o path do QR code da CNH usando nova estrutura user_id + cpf.
    Utiliza métodos atualizados do modelo CNHRequest.
    """
    try:
        # Usar método atualizado do modelo CNHRequest
        if hasattr(cnh_request, 'qr_code_path') and cnh_request.qr_code_path:
            import os
            if os.path.exists(cnh_request.qr_code_path):
                return cnh_request.qr_code_path
        
        # Fallback: construir path usando nova estrutura user_id + cpf
        if cnh_request.generated_image_path and '/front/' in cnh_request.generated_image_path:
            qr_path = cnh_request.generated_image_path.replace('/front/', '/qrcode/')
            import os
            return qr_path if os.path.exists(qr_path) else None
        
        return None
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao obter path do QR code para CNH {cnh_request.id}: {str(e)}")
        return None

def _check_cnh_back_exists(cnh_request):
    """Verifica se o arquivo do verso existe."""
    back_path = _get_cnh_back_path(cnh_request)
    return bool(back_path)

@cnh_bp.route('/consultar/login', methods=['POST'])
@rate_limit_decorator(max_attempts=3, window_seconds=300, block_seconds=900)
def consultar_cnh_login():
    """
    🔐 API LOGIN CNH - Endpoint para Servidor B consultar CNH via CPF + Senha
    
    Endpoint público para o Servidor B validar acesso à CNH usando CPF + senha de 4 dígitos.
    Retorna dados completos da CNH se credenciais estiverem corretas.
    
    SEGURANÇA: Aceita apenas POST para evitar exposição de credenciais na URL
    
    Usage: 
        POST /api/cnh/consultar/login 
        Content-Type: application/json
        Body: {"cpf": "123.456.789-00", "senha": "1503"}
    
    Response:
    {
        "success": true,
        "authenticated": true,
        "cpf_consultado": "123.456.789-00",
        "cnh": {
            "dados_pessoais": {...},
            "documento": {...},
            "habilitacao": {...},
            "arquivos": {
                "foto_3x4_url": "/static/uploads/...",
                "assinatura_url": "..."
            }
        }
    }
    """
    try:
        # Obter dados JSON do POST
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados JSON não fornecidos',
                'message': 'Esta API aceita apenas requisições POST com JSON'
            }), 400
        
        cpf = data.get('cpf')
        senha = data.get('senha')
        
        # Validar parâmetros obrigatórios
        if not cpf or not senha:
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'CPF e senha são obrigatórios'
            }), 400
        
        # 🔒 VALIDAÇÃO DE SEGURANÇA APRIMORADA
        
        # Detectar requisições suspeitas
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        is_suspicious, reason = SecurityValidator.is_suspicious_request(data, client_ip)
        if is_suspicious:
            logger.warning(f"🚨 Requisição suspeita bloqueada - IP: {client_ip}, Motivo: {reason}")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'Requisição inválida'
            }), 400
        
        # Validar CPF com verificadores
        cpf_valido, cpf_limpo, erro_cpf = SecurityValidator.validate_cpf(cpf)
        if not cpf_valido:
            logger.warning(f"🚨 CPF inválido tentativa - IP: {client_ip}, Erro: {erro_cpf}")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'CPF inválido'
            }), 400
        
        # Validar senha
        senha_valida, erro_senha = SecurityValidator.validate_password(senha, 4, 4)
        if not senha_valida:
            logger.warning(f"🚨 Senha inválida tentativa - IP: {client_ip}, Erro: {erro_senha}")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'Senha inválida'
            }), 400
        
        cpf_formatado = SecurityValidator.format_cpf(cpf_limpo)
        
        # Buscar CNH por CPF (formatado e não formatado)
        cnhs_formatado = CNHRequest.query.filter_by(cpf=cpf_formatado).all()
        cnhs_limpo = CNHRequest.query.filter_by(cpf=cpf_limpo).all()
        cnhs_encontradas = list({cnh.id: cnh for cnh in (cnhs_formatado + cnhs_limpo)}.values())
        
        if not cnhs_encontradas:
            # 🔒 Não vazar informações sobre existência de CPFs
            logger.warning(f"🚨 Tentativa de acesso a CPF inexistente - IP: {client_ip}, CPF: {cpf_limpo[:3]}***")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'Credenciais inválidas'
            }), 401
        
        # Ordenar por data de criação (mais recente primeiro)
        cnhs_encontradas.sort(key=lambda x: x.created_at, reverse=True)
        
        # Tentar autenticar com cada CNH encontrada
        cnh_autenticada = None
        for cnh in cnhs_encontradas:
            if cnh.validar_senha_cnh(senha):
                cnh_autenticada = cnh
                break
        
        if not cnh_autenticada:
            logger.warning(f"🚫 Tentativa de login CNH falhada - IP: {client_ip}, CPF: {cpf_limpo[:3]}***")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'Credenciais inválidas'
            }), 401
        
        # ✅ AUTENTICAÇÃO BEM-SUCEDIDA - Preparar dados para retorno
        
        # Funções auxiliares para formatação
        def format_date(date_obj):
            if not date_obj:
                return None
            return date_obj.strftime('%d/%m/%Y')
        
        def format_iso_date(date_obj):
            if not date_obj:
                return None
            return date_obj.isoformat()
        
        # ⚠️ CONVERSÃO PARA BASE64 (Opcional - pode ser pesado)
        def convert_image_to_base64(file_path):
            """
            ⚠️ ATENÇÃO: Base64 pode ser PESADO!
            Uma foto de 100KB vira ~133KB em base64
            Use apenas se Servidor B precisar ser totalmente independente
            """
            if not file_path or not os.path.exists(file_path):
                return None
                
            try:
                import base64
                with open(file_path, 'rb') as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    # Detectar tipo de imagem
                    extension = file_path.lower().split('.')[-1]
                    mime_type = 'image/jpeg' if extension in ['jpg', 'jpeg'] else f'image/{extension}'
                    
                    return f"data:{mime_type};base64,{encoded_string}"
            except Exception as e:
                logger.error(f"Erro ao converter imagem para base64: {file_path}, Erro: {str(e)}")
                return None
        
        # Calcular idade e tempo de habilitação
        idade = cnh_autenticada.get_idade() if hasattr(cnh_autenticada, 'get_idade') else None
        
        tempo_habilitacao = None
        if cnh_autenticada.primeira_habilitacao:
            from datetime import date
            hoje = date.today()
            diff = hoje - cnh_autenticada.primeira_habilitacao
            anos = diff.days // 365
            tempo_habilitacao = f"{anos} ano{'s' if anos != 1 else ''}"
        
        # Status em português
        status_map = {
            'pending': 'Aguardando Processamento',
            'processing': 'Processando',
            'completed': 'Concluída',
            'failed': 'Falha na Geração'
        }
        status_display = status_map.get(cnh_autenticada.status, cnh_autenticada.status)
        
        # Estrutura completa de dados da CNH
        cnh_data = {
            # Identificação básica
            'id': cnh_autenticada.id,
            'status': cnh_autenticada.status,
            'status_display': status_display,
            'custo': f"R$ {cnh_autenticada.custo:.2f}" if cnh_autenticada.custo else "R$ 0,00",
            
            # 👤 Dados Pessoais
            'dados_pessoais': {
                'nome_completo': cnh_autenticada.nome_completo or '',
                'cpf': cpf_formatado,
                'data_nascimento': format_date(cnh_autenticada.data_nascimento),
                'data_nascimento_iso': format_iso_date(cnh_autenticada.data_nascimento),
                'idade': idade,
                'sexo': cnh_autenticada.sexo_condutor,
                'sexo_display': 'Masculino' if cnh_autenticada.sexo_condutor == 'M' else 'Feminino' if cnh_autenticada.sexo_condutor == 'F' else '',
                'nacionalidade': cnh_autenticada.nacionalidade or 'Brasileiro(a)',
                'local_nascimento': cnh_autenticada.local_nascimento or '',
                'uf_nascimento': cnh_autenticada.uf_nascimento or '',
                'local_nascimento_completo': f"{cnh_autenticada.local_nascimento or ''}/{cnh_autenticada.uf_nascimento or ''}".strip('/'),
                'nome_pai': cnh_autenticada.nome_pai or '',
                'nome_mae': cnh_autenticada.nome_mae or ''
            },
            
            # 📄 Documento de Identidade
            'documento': {
                'numero': cnh_autenticada.doc_identidade_numero or '',
                'orgao_emissor': cnh_autenticada.doc_identidade_orgao or '',
                'uf': cnh_autenticada.doc_identidade_uf or '',
                'documento_completo': f"{cnh_autenticada.doc_identidade_numero or ''} {cnh_autenticada.doc_identidade_orgao or ''}/{cnh_autenticada.doc_identidade_uf or ''}".strip()
            },
            
            # 🚗 Informações da Habilitação
            'habilitacao': {
                'categoria': cnh_autenticada.categoria_habilitacao or 'B',
                'primeira_habilitacao': format_date(cnh_autenticada.primeira_habilitacao),
                'primeira_habilitacao_iso': format_iso_date(cnh_autenticada.primeira_habilitacao),
                'tempo_habilitacao': tempo_habilitacao,
                'data_emissao': format_date(cnh_autenticada.data_emissao),
                'data_emissao_iso': format_iso_date(cnh_autenticada.data_emissao),
                'validade': format_date(cnh_autenticada.validade),
                'validade_iso': format_iso_date(cnh_autenticada.validade),
                'acc': cnh_autenticada.acc or 'NAO',
                'acc_display': 'Sim' if cnh_autenticada.acc == 'SIM' else 'Não',
                'uf_cnh': cnh_autenticada.uf_cnh or '',
                'local_municipio': cnh_autenticada.local_municipio or '',
                'local_uf': cnh_autenticada.local_uf or '',
                'local_habilitacao': f"{cnh_autenticada.local_municipio or ''}/{cnh_autenticada.local_uf or ''}".strip('/'),
                'observacoes': cnh_autenticada.observacoes or ''
            },
            
            # 🔢 Números de Controle
            'controle': {
                'numero_registro': cnh_autenticada.numero_registro or '',
                'numero_espelho': cnh_autenticada.numero_espelho or '',
                'codigo_validacao': cnh_autenticada.codigo_validacao or '',
                'numero_renach': cnh_autenticada.numero_renach or '',
                'categorias_adicionais': cnh_autenticada.categorias_adicionais or ''
            },
            
            # 📁 Arquivos e Imagens da CNH (NOVA ESTRUTURA)
            'arquivos': {
                # 🎯 PATHS DAS IMAGENS DA CNH (nova estrutura em uploads/cnh/user_{id}/{cpf}/)
                'cnh_front_path': cnh_autenticada.generated_image_path,
                'cnh_back_path': _get_cnh_back_path(cnh_autenticada),
                'qr_code_path': _get_qr_code_path(cnh_autenticada),
                
                # 🌐 URLs PÚBLICAS para acesso direto (nova estrutura user_id + cpf)
                'cnh_front_url': cnh_autenticada.get_image_url() if hasattr(cnh_autenticada, 'get_image_url') else None,
                'qr_code_url': cnh_autenticada.get_qrcode_url() if hasattr(cnh_autenticada, 'get_qrcode_url') else None,
                
                # 📷 Arquivos de upload do usuário
                'foto_3x4_path': cnh_autenticada.foto_3x4_path,
                'assinatura_path': cnh_autenticada.assinatura_path,
                
                # ✅ Disponibilidade dos arquivos
                'cnh_front_disponivel': bool(cnh_autenticada.generated_image_path),
                'cnh_back_disponivel': _check_cnh_back_exists(cnh_autenticada),
                'qr_code_disponivel': cnh_autenticada.has_qrcode() if hasattr(cnh_autenticada, 'has_qrcode') else bool(_get_qr_code_path(cnh_autenticada)),
                'foto_3x4_disponivel': bool(cnh_autenticada.foto_3x4_path),
                'assinatura_disponivel': bool(cnh_autenticada.assinatura_path)
            },
            
            # ⏰ Timestamps
            'datas_sistema': {
                'criada_em': format_date(cnh_autenticada.created_at),
                'criada_em_iso': format_iso_date(cnh_autenticada.created_at),
                'concluida_em': format_date(cnh_autenticada.completed_at),
                'concluida_em_iso': format_iso_date(cnh_autenticada.completed_at)
            }
        }
        
        # Resposta de sucesso
        response_data = {
            'success': True,
            'authenticated': True,
            'message': 'Login CNH realizado com sucesso',
            'cpf_consultado': cpf_formatado,
            'timestamp_consulta': datetime.utcnow().isoformat(),
            'cnh': cnh_data
        }
        
        # Log de sucesso
        logger.info(f"✅ Login CNH bem-sucedido - CPF: {cpf_formatado}, CNH ID: {cnh_autenticada.id}, Nome: {cnh_autenticada.nome_completo}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Erro no login CNH - CPF: {cpf if 'cpf' in locals() else 'N/A'}, Erro: {str(e)}")
        return jsonify({
            'success': False,
            'authenticated': False,
            'error': 'Erro interno do servidor',
            'message': 'Erro ao processar login da CNH',
            'timestamp_erro': datetime.utcnow().isoformat()
        }), 500


@cnh_bp.route('/api/cnh/consultar/login-simple', methods=['POST'])
@rate_limit_decorator(max_attempts=30, window_seconds=60)  # Rate limiting para segurança
def consultar_cnh_login_simple():
    """
    🔐 API LOGIN CNH - Versão Simplificada
    
    Valida credenciais e retorna apenas dados essenciais + URLs dos arquivos.
    Ideal para quando geração é feita no mesmo servidor.
    
    POST /api/cnh/consultar/login-simple
    Content-Type: application/json
    Body: {"cpf": "020.889.310-58", "senha": "0101"}
    
    Response (Simplificada):
    {
        "success": true,
        "authenticated": true,
        "cnh": {
            "id": 90,
            "nome_completo": "Jorge Andre Silva",
            "cpf": "020.889.310-58",
            "categoria": "B",
            "status": "completed",
            "arquivos": {
                "cnh_front_url": "/static/uploads/cnh/user_1/02088931058/front/90.png",
                "cnh_back_url": "/static/uploads/cnh/user_1/02088931058/back/90.png",
                "qr_code_url": "/static/uploads/cnh/user_1/02088931058/qrcode/90.png",
                "disponibilidade": {...}
            }
        }
    }
    """
    try:
        # Obter dados JSON do POST
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Dados JSON não fornecidos',
                'message': 'Esta API aceita apenas requisições POST com JSON'
            }), 400
        
        cpf = data.get('cpf')
        senha = data.get('senha')
        
        # Validar parâmetros obrigatórios
        if not cpf or not senha:
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'CPF e senha são obrigatórios'
            }), 400
        
        # 🔒 VALIDAÇÕES DE SEGURANÇA (mesmas da API completa)
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
        
        is_suspicious, reason = SecurityValidator.is_suspicious_request(data, client_ip)
        if is_suspicious:
            logger.warning(f"🚨 Requisição suspeita bloqueada (simple) - IP: {client_ip}, Motivo: {reason}")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'Requisição inválida'
            }), 400
        
        # Validar CPF
        cpf_valido, cpf_limpo, erro_cpf = SecurityValidator.validate_cpf(cpf)
        if not cpf_valido:
            logger.warning(f"🚨 CPF inválido tentativa (simple) - IP: {client_ip}, Erro: {erro_cpf}")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'CPF inválido'
            }), 400
        
        # Validar senha
        senha_valida, erro_senha = SecurityValidator.validate_password(senha, 4, 4)
        if not senha_valida:
            logger.warning(f"🚨 Senha inválida tentativa (simple) - IP: {client_ip}, Erro: {erro_senha}")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'Senha inválida'
            }), 400
        
        cpf_formatado = SecurityValidator.format_cpf(cpf_limpo)
        
        # Buscar CNH por CPF
        cnhs_formatado = CNHRequest.query.filter_by(cpf=cpf_formatado).all()
        cnhs_limpo = CNHRequest.query.filter_by(cpf=cpf_limpo).all()
        cnhs_encontradas = list({cnh.id: cnh for cnh in (cnhs_formatado + cnhs_limpo)}.values())
        
        if not cnhs_encontradas:
            logger.warning(f"🚨 Tentativa de acesso a CPF inexistente (simple) - IP: {client_ip}, CPF: {cpf_limpo[:3]}***")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'Credenciais inválidas'
            }), 401
        
        # Ordenar por data de criação (mais recente primeiro)
        cnhs_encontradas.sort(key=lambda x: x.created_at, reverse=True)
        
        # Tentar autenticar
        cnh_autenticada = None
        for cnh in cnhs_encontradas:
            if cnh.validar_senha_cnh(senha):
                cnh_autenticada = cnh
                break
        
        if not cnh_autenticada:
            logger.warning(f"🚫 Tentativa de login CNH falhada (simple) - IP: {client_ip}, CPF: {cpf_limpo[:3]}***")
            return jsonify({
                'success': False,
                'authenticated': False,
                'error': 'Credenciais inválidas'
            }), 401
        
        # ✅ RESPOSTA SIMPLIFICADA
        
        # Funções auxiliares para URLs
        def get_back_url():
            back_path = _get_cnh_back_path(cnh_autenticada)
            if back_path and '/user_' in back_path:
                return back_path.replace('static/', '/')
            return None
        
        def get_foto_url():
            if cnh_autenticada.foto_3x4_path:
                return f"/{cnh_autenticada.foto_3x4_path}"
            return None
        
        def get_assinatura_url():
            if cnh_autenticada.assinatura_path:
                return f"/{cnh_autenticada.assinatura_path}"
            return None
        
        response_data = {
            'success': True,
            'authenticated': True,
            'message': 'Login CNH realizado com sucesso',
            'cnh': {
                # Dados básicos essenciais
                'id': cnh_autenticada.id,
                'nome_completo': cnh_autenticada.nome_completo or '',
                'cpf': cpf_formatado,
                'categoria': cnh_autenticada.categoria_habilitacao or 'B',
                'status': cnh_autenticada.status,
                'status_display': {
                    'pending': 'Aguardando Processamento',
                    'processing': 'Processando',
                    'completed': 'Concluída',
                    'failed': 'Falha na Geração'
                }.get(cnh_autenticada.status, cnh_autenticada.status),
                
                # URLs dos arquivos (funcionalidade principal)
                'arquivos': {
                    # URLs públicas para acesso direto
                    'cnh_front_url': cnh_autenticada.get_image_url(),
                    'cnh_back_url': get_back_url(),
                    'qr_code_url': cnh_autenticada.get_qrcode_url(),
                    'foto_3x4_url': get_foto_url(),
                    'assinatura_url': get_assinatura_url(),
                    
                    # Status de disponibilidade
                    'disponibilidade': {
                        'cnh_front': bool(cnh_autenticada.generated_image_path),
                        'cnh_back': _check_cnh_back_exists(cnh_autenticada),
                        'qr_code': cnh_autenticada.has_qrcode() if hasattr(cnh_autenticada, 'has_qrcode') else bool(_get_qr_code_path(cnh_autenticada)),
                        'foto_3x4': bool(cnh_autenticada.foto_3x4_path),
                        'assinatura': bool(cnh_autenticada.assinatura_path)
                    }
                },
                
                # Data de criação
                'criada_em': cnh_autenticada.created_at.strftime('%d/%m/%Y') if cnh_autenticada.created_at else None,
                'custo': f"R$ {cnh_autenticada.custo:.2f}" if cnh_autenticada.custo else "R$ 0,00"
            },
            'timestamp_consulta': datetime.utcnow().isoformat()
        }
        
        # Log de sucesso
        logger.info(f"✅ Login CNH simples bem-sucedido - CPF: {cpf_formatado}, CNH ID: {cnh_autenticada.id}, Nome: {cnh_autenticada.nome_completo}")
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"❌ Erro no login CNH simples - CPF: {cpf if 'cpf' in locals() else 'N/A'}, Erro: {str(e)}")
        return jsonify({
            'success': False,
            'authenticated': False,
            'error': 'Erro interno do servidor',
            'message': 'Erro ao processar login da CNH',
            'timestamp_erro': datetime.utcnow().isoformat()
        }), 500