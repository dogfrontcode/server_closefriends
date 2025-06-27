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
    
    # Dados pessoais
    nome_completo = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), nullable=False)  # Com formatação XXX.XXX.XXX-XX
    rg = db.Column(db.String(20), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    
    # Configurações da CNH
    categoria = db.Column(db.String(5), default='B', nullable=False)
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
        Valida formato e dígitos verificadores do CPF.
        
        Args:
            cpf (str): CPF no formato XXX.XXX.XXX-XX ou apenas números
            
        Returns:
            tuple: (is_valid: bool, formatted_cpf: str, error_message: str)
        """
        if not cpf:
            return False, "", "CPF é obrigatório"
        
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
    
    @staticmethod
    def validar_rg(rg):
        """
        Valida formato do RG.
        
        Args:
            rg (str): RG com ou sem formatação
            
        Returns:
            tuple: (is_valid: bool, formatted_rg: str, error_message: str)
        """
        if not rg:
            return False, "", "RG é obrigatório"
        
        # Remove espaços e converte para maiúsculo
        rg_clean = rg.strip().upper()
        
        # Verifica se tem formato válido (números e opcionalmente uma letra no final)
        if not re.match(r'^[0-9]{4,15}[A-Z]?$', re.sub(r'[.\-\s]', '', rg_clean)):
            return False, "", "RG deve ter entre 4-15 números e opcionalmente uma letra"
        
        # Verifica tamanho mínimo
        rg_numbers = re.sub(r'[^0-9A-Z]', '', rg_clean)
        if len(rg_numbers) < 4:
            return False, "", "RG muito curto"
        
        return True, rg_clean, ""
    
    @staticmethod
    def validar_nome(nome):
        """
        Valida nome completo.
        
        Args:
            nome (str): Nome completo
            
        Returns:
            tuple: (is_valid: bool, formatted_name: str, error_message: str)
        """
        if not nome:
            return False, "", "Nome é obrigatório"
        
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
        Valida data de nascimento e calcula idade.
        
        Args:
            data_nasc (date or str): Data de nascimento
            
        Returns:
            tuple: (is_valid: bool, date_obj: date, idade: int, error_message: str)
        """
        if not data_nasc:
            return False, None, 0, "Data de nascimento é obrigatória"
        
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
        
        # Valida idade
        if idade < CNHRequest.IDADE_MINIMA:
            return False, data_nasc, idade, f"Idade mínima: {CNHRequest.IDADE_MINIMA} anos"
        
        if idade > CNHRequest.IDADE_MAXIMA:
            return False, data_nasc, idade, f"Idade máxima: {CNHRequest.IDADE_MAXIMA} anos"
        
        # Verifica se data não é futura
        if data_nasc > hoje:
            return False, data_nasc, idade, "Data de nascimento não pode ser futura"
        
        return True, data_nasc, idade, ""
    
    @staticmethod
    def validar_categoria(categoria):
        """
        Valida categoria da CNH.
        
        Args:
            categoria (str): Categoria (A, B, C, etc.)
            
        Returns:
            tuple: (is_valid: bool, categoria: str, error_message: str)
        """
        if not categoria:
            categoria = 'B'  # Padrão
        
        categoria = categoria.upper().strip()
        
        if categoria not in CNHRequest.CATEGORIAS_VALIDAS:
            return False, categoria, f"Categoria inválida. Válidas: {', '.join(CNHRequest.CATEGORIAS_VALIDAS)}"
        
        return True, categoria, ""
    
    # ==================== MÉTODOS DE VALIDAÇÃO COMPLETA ====================
    
    @classmethod
    def validar_dados_completos(cls, dados):
        """
        Valida todos os dados do formulário CNH.
        
        Args:
            dados (dict): Dados do formulário
            
        Returns:
            tuple: (is_valid: bool, validated_data: dict, errors: dict)
        """
        validated_data = {}
        errors = {}
        
        # Validar nome
        nome_valido, nome_formatado, nome_erro = cls.validar_nome(dados.get('nome_completo'))
        if nome_valido:
            validated_data['nome_completo'] = nome_formatado
        else:
            errors['nome_completo'] = nome_erro
        
        # Validar CPF
        cpf_valido, cpf_formatado, cpf_erro = cls.validar_cpf(dados.get('cpf'))
        if cpf_valido:
            validated_data['cpf'] = cpf_formatado
        else:
            errors['cpf'] = cpf_erro
        
        # Validar RG
        rg_valido, rg_formatado, rg_erro = cls.validar_rg(dados.get('rg'))
        if rg_valido:
            validated_data['rg'] = rg_formatado
        else:
            errors['rg'] = rg_erro
        
        # Validar data de nascimento
        data_valida, data_obj, idade, data_erro = cls.validar_data_nascimento(dados.get('data_nascimento'))
        if data_valida:
            validated_data['data_nascimento'] = data_obj
            validated_data['idade'] = idade
        else:
            errors['data_nascimento'] = data_erro
        
        # Validar categoria
        cat_valida, categoria, cat_erro = cls.validar_categoria(dados.get('categoria'))
        if cat_valida:
            validated_data['categoria'] = categoria
        else:
            errors['categoria'] = cat_erro
        
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
                nome_completo=dados_validados['nome_completo'],
                cpf=dados_validados['cpf'],
                rg=dados_validados['rg'],
                data_nascimento=dados_validados['data_nascimento'],
                categoria=dados_validados['categoria'],
                custo=cls.CUSTO_PADRAO,
                status=cls.STATUS_PENDING
            )
            
            db.session.add(cnh_request)
            db.session.flush()  # Para obter o ID
            
            # Debitar créditos
            user.debit_credits(
                amount=cls.CUSTO_PADRAO,
                transaction_type='cnh_generation',
                description=f'Geração de CNH #{cnh_request.id} - {dados_validados["nome_completo"]}'
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
            int: Idade em anos
        """
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
            'nome_completo': self.nome_completo,
            'cpf': self.cpf,
            'rg': self.rg,
            'data_nascimento': self.data_nascimento.isoformat() if self.data_nascimento else None,
            'categoria': self.categoria,
            'custo': self.custo,
            'status': self.status,
            'status_display': self.get_status_display(),
            'generated_image_path': self.generated_image_path,
            'image_url': self.get_image_url(),
            'can_download': self.can_download(),
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'idade': self.get_idade()
        }
    
    def __repr__(self):
        return f'<CNHRequest {self.id}: {self.nome_completo} - {self.status}>' 