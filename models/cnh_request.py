# models/cnh_request.py
from . import db
from datetime import datetime, date
import re
import logging
import os

logger = logging.getLogger(__name__)

class CNHRequest(db.Model):
    """
    Modelo para pedidos de geração de CNH.
    Integra com sistema de créditos e controla todo o fluxo de geração.
    """
    __tablename__ = 'cnh_requests'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Dados pessoais básicos (opcionais para testes)
    nome_completo = db.Column(db.String(100))
    cpf = db.Column(db.String(14))  # Com formatação XXX.XXX.XXX-XX
    data_nascimento = db.Column(db.Date)
    local_nascimento = db.Column(db.String(100))
    uf_nascimento = db.Column(db.String(2))
    nacionalidade = db.Column(db.String(50))
    nome_pai = db.Column(db.String(100))
    nome_mae = db.Column(db.String(100))
    sexo_condutor = db.Column(db.String(1))  # M/F
    
    # Documento de identidade
    doc_identidade_numero = db.Column(db.String(20))
    doc_identidade_orgao = db.Column(db.String(10))
    doc_identidade_uf = db.Column(db.String(2))
    
    # Datas da CNH
    primeira_habilitacao = db.Column(db.Date)
    data_emissao = db.Column(db.Date)
    validade = db.Column(db.Date)
    
    # Configurações da CNH
    categoria_habilitacao = db.Column(db.String(10), default='B')  # A, B, C, AB, etc.
    acc = db.Column(db.String(3), default='NAO')  # SIM/NAO
    uf_cnh = db.Column(db.String(2))
    
    # Números de controle
    numero_registro = db.Column(db.String(20))
    numero_espelho = db.Column(db.String(20))
    codigo_validacao = db.Column(db.String(20))
    numero_renach = db.Column(db.String(20))
    
    # Local da habilitação
    local_municipio = db.Column(db.String(100))
    local_uf = db.Column(db.String(2))
    
    # Categorias adicionais (JSON string)
    categorias_adicionais = db.Column(db.Text)  # JSON das categorias com datas
    
    # Observações
    observacoes = db.Column(db.Text)
    
    # Arquivos
    foto_3x4_path = db.Column(db.String(255))
    assinatura_path = db.Column(db.String(255))
    custo = db.Column(db.Float, default=5.0, nullable=False)
    
    # Controle do processo
    status = db.Column(db.String(20), default='pending', nullable=False)
    # Status possíveis: 'pending', 'processing', 'completed', 'failed'
    
    generated_image_path = db.Column(db.String(255))
    error_message = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime)
    
    # Relacionamento
    user = db.relationship('User', backref=db.backref('cnh_requests', lazy=True, order_by='CNHRequest.created_at.desc()'))
    
    # ==================== CONSTANTES ====================
    
    CATEGORIAS_VALIDAS = ['A', 'B', 'C', 'D', 'E', 'AB', 'AC', 'AD', 'AE']
    CUSTO_PADRAO = 5.0
    MAX_CNH_POR_DIA = 999  # Sem limite prático
    IDADE_MINIMA = 18
    IDADE_MAXIMA = 80
    
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'
    
    # ==================== VALIDAÇÕES ESTÁTICAS ====================
    
    @staticmethod
    def validar_cpf(cpf):
        """
        Valida formato e dígitos verificadores do CPF (opcional para testes).
        
        Args:
            cpf (str): CPF no formato XXX.XXX.XXX-XX ou apenas números
            
        Returns:
            tuple: (is_valid: bool, formatted_cpf: str, error_message: str)
        """
        if not cpf:
            return True, "", ""  # Opcional para testes
        
        # Remove caracteres não numéricos
        cpf_numbers = re.sub(r'[^0-9]', '', cpf)
        
        # Verifica se tem 11 dígitos
        if len(cpf_numbers) != 11:
            return False, "", "CPF deve ter 11 dígitos"
        
        # Verifica se não são todos iguais (111.111.111-11, etc.)
        if cpf_numbers == cpf_numbers[0] * 11:
            return False, "", "CPF inválido"
        
        # Calcula dígitos verificadores
        def calcular_digito(cpf_parcial):
            peso = len(cpf_parcial) + 1
            soma = sum(int(cpf_parcial[i]) * (peso - i) for i in range(len(cpf_parcial)))
            resto = soma % 11
            return 0 if resto < 2 else 11 - resto
        
        # Valida primeiro dígito
        primeiro_digito = calcular_digito(cpf_numbers[:9])
        if primeiro_digito != int(cpf_numbers[9]):
            return False, "", "CPF inválido - primeiro dígito"
        
        # Valida segundo dígito
        segundo_digito = calcular_digito(cpf_numbers[:10])
        if segundo_digito != int(cpf_numbers[10]):
            return False, "", "CPF inválido - segundo dígito"
        
        # Formata CPF
        cpf_formatado = f"{cpf_numbers[:3]}.{cpf_numbers[3:6]}.{cpf_numbers[6:9]}-{cpf_numbers[9:]}"
        
        return True, cpf_formatado, ""
    
    # Removido validar_rg - campo não existe mais
    
    @staticmethod
    def validar_nome(nome):
        """
        Valida nome completo (opcional para testes).
        
        Args:
            nome (str): Nome completo
            
        Returns:
            tuple: (is_valid: bool, formatted_name: str, error_message: str)
        """
        if not nome:
            return True, "", ""  # Opcional para testes
        
        nome_clean = nome.strip().title()
        
        if len(nome_clean) < 10:
            return False, "", "Nome deve ter pelo menos 10 caracteres"
        
        if len(nome_clean) > 100:
            return False, "", "Nome muito longo (máx 100 caracteres)"
        
        # Verifica se tem pelo menos nome e sobrenome
        palavras = nome_clean.split()
        if len(palavras) < 2:
            return False, "", "Informe nome e sobrenome"
        
        # Verifica caracteres válidos (letras, espaços, acentos)
        if not re.match(r'^[A-Za-zÀ-ÿ\s]+$', nome_clean):
            return False, "", "Nome deve conter apenas letras e espaços"
        
        return True, nome_clean, ""
    
    @staticmethod
    def validar_data_nascimento(data_nasc):
        """
        Valida data de nascimento (opcional para testes).
        
        Args:
            data_nasc (date or str): Data de nascimento
            
        Returns:
            tuple: (is_valid: bool, date_obj: date, idade: int, error_message: str)
        """
        if not data_nasc:
            return True, None, 0, ""  # Opcional para testes
        
        # Converte string para date se necessário
        if isinstance(data_nasc, str):
            try:
                data_nasc = datetime.strptime(data_nasc, '%Y-%m-%d').date()
            except ValueError:
                return False, None, 0, "Data inválida. Use formato AAAA-MM-DD"
        
        # Calcula idade
        hoje = date.today()
        idade = hoje.year - data_nasc.year
        
        # Ajusta se ainda não fez aniversário este ano
        if hoje.month < data_nasc.month or (hoje.month == data_nasc.month and hoje.day < data_nasc.day):
            idade -= 1
        
        # Validações de idade removidas para testes
        
        # Verifica se data não é futura
        if data_nasc > hoje:
            return False, data_nasc, idade, "Data de nascimento não pode ser futura"
        
        return True, data_nasc, idade, ""
    
    @staticmethod
    def validar_categoria(categoria):
        """
        Valida categoria da CNH (opcional para testes).
        
        Args:
            categoria (str): Categoria (A, B, C, etc.)
            
        Returns:
            tuple: (is_valid: bool, categoria: str, error_message: str)
        """
        if not categoria:
            return True, 'B', ""  # Padrão opcional
        
        categoria = categoria.upper().strip()
        
        # Para testes, aceita qualquer categoria
        return True, categoria, ""
    
    # ==================== MÉTODOS DE VALIDAÇÃO COMPLETA ====================
    
    @classmethod
    def validar_dados_completos(cls, dados):
        """
        Valida todos os dados do formulário CNH (campos opcionais para testes).
        
        Args:
            dados (dict): Dados do formulário
            
        Returns:
            tuple: (is_valid: bool, validated_data: dict, errors: dict)
        """
        validated_data = {}
        errors = {}
        
        # Campos de texto simples (todos opcionais)
        campos_texto = [
            'nome_completo', 'local_nascimento', 'uf_nascimento', 'nacionalidade',
            'nome_pai', 'nome_mae', 'doc_identidade_numero', 'doc_identidade_orgao',
            'doc_identidade_uf', 'sexo_condutor', 'uf_cnh', 'numero_registro',
            'numero_espelho', 'codigo_validacao', 'numero_renach', 'local_municipio',
            'local_uf', 'categoria_habilitacao', 'acc', 'observacoes', 'categorias_adicionais'
        ]
        
        for campo in campos_texto:
            valor = dados.get(campo)
            if valor:
                validated_data[campo] = valor.strip()
        
        # Validar CPF se fornecido
        cpf_valido, cpf_formatado, cpf_erro = cls.validar_cpf(dados.get('cpf'))
        if cpf_valido and cpf_formatado:
            validated_data['cpf'] = cpf_formatado
        elif not cpf_valido:
            errors['cpf'] = cpf_erro
        
        # Validar nome se fornecido
        nome_valido, nome_formatado, nome_erro = cls.validar_nome(dados.get('nome_completo'))
        if nome_valido and nome_formatado:
            validated_data['nome_completo'] = nome_formatado
        elif not nome_valido:
            errors['nome_completo'] = nome_erro
        
        # Validar datas se fornecidas
        campos_data = ['data_nascimento', 'primeira_habilitacao', 'data_emissao', 'validade']
        for campo in campos_data:
            data_str = dados.get(campo)
            if data_str:
                try:
                    data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
                    validated_data[campo] = data_obj
                except ValueError:
                    errors[campo] = f"Data inválida para {campo}"
        
        # Validar categoria se fornecida
        cat_valida, categoria, cat_erro = cls.validar_categoria(dados.get('categoria_habilitacao'))
        if cat_valida and categoria:
            validated_data['categoria_habilitacao'] = categoria
        elif not cat_valida:
            errors['categoria_habilitacao'] = cat_erro
        
        is_valid = len(errors) == 0
        return is_valid, validated_data, errors
    
    # ==================== MÉTODOS DE NEGÓCIO ====================
    
    @classmethod
    def pode_gerar_cnh(cls, user_id):
        """
        Verifica se usuário pode gerar uma nova CNH hoje.
        
        Args:
            user_id (int): ID do usuário
            
        Returns:
            tuple: (can_generate: bool, count_today: int, error_message: str)
        """
        from datetime import datetime, timedelta
        
        # Contar CNHs geradas hoje
        hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_fim = hoje_inicio + timedelta(days=1)
        
        count_hoje = cls.query.filter(
            cls.user_id == user_id,
            cls.created_at >= hoje_inicio,
            cls.created_at < hoje_fim
        ).count()
        
        if count_hoje >= cls.MAX_CNH_POR_DIA:
            return False, count_hoje, f"Limite diário excedido ({cls.MAX_CNH_POR_DIA} CNHs por dia)"
        
        return True, count_hoje, ""
    
    @classmethod
    def criar_cnh_request(cls, user_id, dados_validados):
        """
        Cria um novo pedido de CNH após validações.
        
        Args:
            user_id (int): ID do usuário
            dados_validados (dict): Dados já validados
            
        Returns:
            tuple: (success: bool, cnh_request: CNHRequest, error_message: str)
        """
        try:
            # Verificar limite diário
            pode_gerar, count_hoje, limite_erro = cls.pode_gerar_cnh(user_id)
            if not pode_gerar:
                return False, None, limite_erro
            
            # Verificar se usuário tem créditos suficientes
            from .user import User
            user = User.query.get(user_id)
            if not user:
                return False, None, "Usuário não encontrado"
            
            if not user.has_sufficient_credits(cls.CUSTO_PADRAO):
                return False, None, f"Créditos insuficientes. Necessário: {cls.CUSTO_PADRAO}, Atual: {user.credits:.2f}"
            
            # Criar CNH request
            cnh_request = cls(
                user_id=user_id,
                custo=cls.CUSTO_PADRAO,
                status=cls.STATUS_PENDING
            )
            
            # Adicionar todos os campos validados
            for campo, valor in dados_validados.items():
                if hasattr(cnh_request, campo):
                    setattr(cnh_request, campo, valor)
            
            db.session.add(cnh_request)
            db.session.flush()  # Para obter o ID
            
            # Debitar créditos
            nome_desc = dados_validados.get('nome_completo', 'Sem nome')
            user.debit_credits(
                amount=cls.CUSTO_PADRAO,
                transaction_type='cnh_generation',
                description=f'Geração de CNH #{cnh_request.id} - {nome_desc}'
            )
            
            db.session.commit()
            
            logger.info(f"CNH request criada - ID: {cnh_request.id}, User: {user.username}")
            return True, cnh_request, ""
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar CNH request - User ID: {user_id}, Erro: {str(e)}")
            return False, None, f"Erro interno: {str(e)}"
    
    # ==================== MÉTODOS DE INSTÂNCIA ====================
    
    def marcar_como_processando(self):
        """Marca CNH como sendo processada."""
        self.status = self.STATUS_PROCESSING
        db.session.commit()
    
    def marcar_como_completa(self, image_path):
        """
        Marca CNH como completa e salva caminho da imagem.
        
        Args:
            image_path (str): Caminho da imagem gerada
        """
        self.status = self.STATUS_COMPLETED
        self.generated_image_path = image_path
        self.completed_at = datetime.utcnow()
        self.error_message = None
        db.session.commit()
        
        logger.info(f"CNH completa - ID: {self.id}, Imagem: {image_path}")
    
    def marcar_como_falha(self, error_message):
        """
        Marca CNH como falha e registra erro.
        
        Args:
            error_message (str): Mensagem de erro
        """
        self.status = self.STATUS_FAILED
        self.error_message = error_message
        db.session.commit()
        
        logger.error(f"CNH falhou - ID: {self.id}, Erro: {error_message}")
        
        # Tentar estornar créditos
        try:
            self.user.add_credits(
                amount=self.custo,
                transaction_type='refund',
                description=f'Estorno CNH #{self.id} - Falha na geração'
            )
            logger.info(f"Créditos estornados para CNH falha - ID: {self.id}")
        except Exception as e:
            logger.error(f"Erro ao estornar créditos - CNH ID: {self.id}, Erro: {str(e)}")
    
    def get_image_url(self):
        """
        Retorna URL pública da imagem gerada.
        
        Returns:
            str: URL da imagem ou None
        """
        if not self.generated_image_path:
            return None
        
        # Remove static/ do início se existir e adiciona /static/
        path = self.generated_image_path
        if path.startswith('static/'):
            path = path[7:]  # Remove 'static/'
        
        return f'/static/{path}'
    
    def get_filename(self):
        """
        Retorna nome do arquivo da imagem.
        
        Returns:
            str: Nome do arquivo
        """
        if not self.generated_image_path:
            return None
        
        return os.path.basename(self.generated_image_path)
    
    def can_download(self):
        """
        Verifica se CNH pode ser baixada.
        
        Returns:
            bool: True se pode baixar
        """
        return (self.status == self.STATUS_COMPLETED and 
                self.generated_image_path and 
                os.path.exists(self.generated_image_path))
    
    def get_status_display(self):
        """
        Retorna status em português.
        
        Returns:
            str: Status em português
        """
        status_map = {
            self.STATUS_PENDING: 'Pendente',
            self.STATUS_PROCESSING: 'Processando',
            self.STATUS_COMPLETED: 'Concluída',
            self.STATUS_FAILED: 'Falha'
        }
        return status_map.get(self.status, self.status)
    
    def get_idade(self):
        """
        Calcula idade atual baseada na data de nascimento.
        
        Returns:
            int: Idade em anos ou 0 se não houver data
        """
        if not self.data_nascimento:
            return 0
            
        hoje = date.today()
        idade = hoje.year - self.data_nascimento.year
        
        if hoje.month < self.data_nascimento.month or (hoje.month == self.data_nascimento.month and hoje.day < self.data_nascimento.day):
            idade -= 1
        
        return idade
    
    def to_dict(self):
        """
        Converte CNH request para dicionário.
        
        Returns:
            dict: Dados da CNH
        """
        return {
            'id': self.id,
            'nome_completo': self.nome_completo or '',
            'cpf': self.cpf or '',
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'categoria_habilitacao': self.categoria_habilitacao or 'B',
            'categoria': self.categoria_habilitacao or 'B',  # Compatibilidade com frontend
            'numero_registro': self.numero_registro or '',
            'numero_espelho': self.numero_espelho or '',
            'uf_cnh': self.uf_cnh or 'SP',
            'doc_identidade_numero': self.doc_identidade_numero or '',
            'doc_identidade_orgao': self.doc_identidade_orgao or '',
            'doc_identidade_uf': self.doc_identidade_uf or '',
            'nacionalidade': self.nacionalidade or '',
            'local_nascimento': self.local_nascimento or '',
            'uf_nascimento': self.uf_nascimento or '',
            'nome_pai': self.nome_pai or '',
            'nome_mae': self.nome_mae or '',
            'sexo_condutor': self.sexo_condutor or '',
            'primeira_habilitacao': self.primeira_habilitacao.isoformat() if self.primeira_habilitacao else None,
            'data_emissao': self.data_emissao.isoformat() if self.data_emissao else None,
            'validade': self.validade.isoformat() if self.validade else None,
            'acc': self.acc or 'NAO',
            'local_municipio': self.local_municipio or '',
            'local_uf': self.local_uf or '',
            'observacoes': self.observacoes or '',
            'custo': self.custo,
            'status': self.status,
            'status_display': self.get_status_display(),
            'generated_image_path': self.generated_image_path,
            'image_url': self.get_image_url(),
            'can_download': self.can_download(),
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def __repr__(self):
        return f'<CNHRequest {self.id}: {self.nome_completo} - {self.status}>' 