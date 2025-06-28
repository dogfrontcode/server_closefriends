# models/credit_transaction.py
from . import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class CreditTransaction(db.Model):
    """
    Modelo para registrar todas as transações de crédito dos usuários.
    Mantém histórico completo para auditoria e controle financeiro.
    """
    __tablename__ = 'credit_transactions'
    
    # Campos principais
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # + para crédito, - para débito
    transaction_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    
    # Controle de saldo
    balance_before = db.Column(db.Float, nullable=False)  # Saldo antes da transação
    balance_after = db.Column(db.Float, nullable=False)   # Saldo após a transação
    
    # PIX/Pagamento - Campo adicionado para suportar referências externas
    reference_id = db.Column(db.String(100), nullable=True, index=True)  # ID externo (PIX, cartão, etc.)
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    ip_address = db.Column(db.String(45))  # IPv4/IPv6
    user_agent = db.Column(db.String(255))
    
    # Status da transação
    status = db.Column(db.String(20), default='completed', nullable=False)
    # Valores possíveis: 'completed', 'pending', 'failed', 'reversed'
    
    # Relacionamento com User
    user = db.relationship('User', backref=db.backref('credit_transactions', lazy=True, order_by='CreditTransaction.created_at.desc()'))
    
    # ==================== TIPOS DE TRANSAÇÃO ====================
    TRANSACTION_TYPES = {
        'pix_pending': 'PIX - Aguardando Pagamento',
        'pix_confirmed': 'PIX - Pagamento Confirmado', 
        'pix_failed': 'PIX - Pagamento Falhou',
        'pix_recharge': 'Recarga via PIX',
        'cnh_generation': 'Geração de CNH',
        'email_service': 'Serviço de Email',
        'sms_service': 'Serviço de SMS',
        'admin_adjustment': 'Ajuste Administrativo',
        'bonus': 'Bônus',
        'refund': 'Reembolso',
        'penalty': 'Penalidade',
        'welcome_bonus': 'Bônus de Boas-Vindas',
        'manual_add': 'Adição Manual'
    }
    
    # ==================== MÉTODOS ESTÁTICOS ====================
    
    @staticmethod
    def create_transaction(user_id, amount, transaction_type, description=None, 
                         balance_before=0, balance_after=0, ip_address=None, user_agent=None, reference_id=None):
        """
        Cria uma nova transação de crédito de forma padronizada.
        
        Args:
            user_id (int): ID do usuário
            amount (float): Valor da transação (+ crédito, - débito)
            transaction_type (str): Tipo da transação
            description (str, optional): Descrição detalhada
            balance_before (float): Saldo antes da transação
            balance_after (float): Saldo após a transação
            ip_address (str, optional): IP do usuário
            user_agent (str, optional): User agent do navegador
            reference_id (str, optional): ID de referência externa (PIX, etc.)
            
        Returns:
            CreditTransaction: Objeto da transação criada
        """
        try:
            transaction = CreditTransaction(
                user_id=user_id,
                amount=amount,
                transaction_type=transaction_type,
                description=description or CreditTransaction.TRANSACTION_TYPES.get(transaction_type, 'Transação'),
                balance_before=balance_before,
                balance_after=balance_after,
                ip_address=ip_address,
                user_agent=user_agent,
                reference_id=reference_id
            )
            
            db.session.add(transaction)
            
            logger.info(f"Transação criada - User ID: {user_id}, Tipo: {transaction_type}, Valor: {amount}")
            return transaction
            
        except Exception as e:
            logger.error(f"Erro ao criar transação - User ID: {user_id}, Erro: {str(e)}")
            raise e
    
    @staticmethod
    def get_user_transactions(user_id, limit=50, offset=0, transaction_type=None):
        """
        Busca transações de um usuário específico.
        
        Args:
            user_id (int): ID do usuário
            limit (int): Limite de resultados
            offset (int): Offset para paginação
            transaction_type (str, optional): Filtrar por tipo
            
        Returns:
            list: Lista de transações
        """
        query = CreditTransaction.query.filter_by(user_id=user_id)
        
        if transaction_type:
            query = query.filter_by(transaction_type=transaction_type)
        
        return query.order_by(CreditTransaction.created_at.desc()).offset(offset).limit(limit).all()
    
    @staticmethod
    def get_total_credits_added(user_id, days=None):
        """
        Calcula total de créditos adicionados para um usuário.
        
        Args:
            user_id (int): ID do usuário
            days (int, optional): Últimos X dias
            
        Returns:
            float: Total de créditos adicionados
        """
        query = CreditTransaction.query.filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.amount > 0
        )
        
        if days:
            from datetime import timedelta
            since_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(CreditTransaction.created_at >= since_date)
        
        result = query.with_entities(db.func.sum(CreditTransaction.amount)).scalar()
        return result or 0.0
    
    @staticmethod
    def get_total_credits_spent(user_id, days=None):
        """
        Calcula total de créditos gastos para um usuário.
        
        Args:
            user_id (int): ID do usuário
            days (int, optional): Últimos X dias
            
        Returns:
            float: Total de créditos gastos (valor absoluto)
        """
        query = CreditTransaction.query.filter(
            CreditTransaction.user_id == user_id,
            CreditTransaction.amount < 0
        )
        
        if days:
            from datetime import timedelta
            since_date = datetime.utcnow() - timedelta(days=days)
            query = query.filter(CreditTransaction.created_at >= since_date)
        
        result = query.with_entities(db.func.sum(CreditTransaction.amount)).scalar()
        return abs(result) if result else 0.0
    
    # ==================== MÉTODOS DE INSTÂNCIA ====================
    
    def get_transaction_info(self):
        """
        Retorna informações formatadas da transação.
        
        Returns:
            dict: Dados da transação formatados
        """
        return {
            'id': self.id,
            'amount': self.amount,
            'amount_formatted': f"{self.amount:+.2f}",
            'type': self.transaction_type,
            'type_description': self.TRANSACTION_TYPES.get(self.transaction_type, self.transaction_type),
            'description': self.description,
            'balance_before': self.balance_before,
            'balance_after': self.balance_after,
            'date': self.created_at.isoformat(),
            'date_formatted': self.created_at.strftime('%d/%m/%Y %H:%M'),
            'status': self.status,
            'is_credit': self.amount > 0,
            'is_debit': self.amount < 0,
            'reference_id': self.reference_id
        }
    
    def reverse_transaction(self, reason="Transação revertida"):
        """
        Reverte uma transação criando uma transação oposta.
        
        Args:
            reason (str): Motivo da reversão
            
        Returns:
            CreditTransaction: Nova transação de reversão
        """
        if self.status == 'reversed':
            raise ValueError("Transação já foi revertida")
        
        try:
            # Marca transação atual como revertida
            self.status = 'reversed'
            
            # Cria transação oposta
            reverse_transaction = CreditTransaction.create_transaction(
                user_id=self.user_id,
                amount=-self.amount,  # Valor oposto
                transaction_type='refund',
                description=f"Reversão: {reason}",
                balance_before=self.user.credits,
                balance_after=self.user.credits - self.amount
            )
            
            # Atualiza saldo do usuário
            self.user.credits -= self.amount
            
            db.session.commit()
            
            logger.info(f"Transação revertida - ID: {self.id}, Motivo: {reason}")
            return reverse_transaction
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao reverter transação - ID: {self.id}, Erro: {str(e)}")
            raise e
    
    def __repr__(self):
        signal = "+" if self.amount > 0 else ""
        return f'<CreditTransaction {self.id}: {signal}{self.amount:.2f} - {self.transaction_type}>' 