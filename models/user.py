# models/user.py
from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging

# Configurar logging
logger = logging.getLogger(__name__)

class User(db.Model):
    """
    Modelo que representa um usuário no banco de dados.
    Inclui sistema de créditos integrado.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    credits = db.Column(db.Float, default=0.0, nullable=False)  # Saldo de créditos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password):
        """
        Define a senha do usuário armazenando-a como hash.
        :param password: senha em texto plano
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifica se a senha fornecida confere com o hash armazenado.
        :param password: senha em texto plano
        :return: True se a senha estiver correta; False caso contrário.
        """
        return check_password_hash(self.password_hash, password)
    
    # ==================== SISTEMA DE CRÉDITOS ====================
    
    def add_credits(self, amount, transaction_type, description=None):
        """
        Adiciona créditos ao usuário de forma segura.
        
        Args:
            amount (float): Valor a ser adicionado (deve ser positivo)
            transaction_type (str): Tipo da transação
            description (str, optional): Descrição da transação
            
        Returns:
            CreditTransaction: Objeto da transação criada
            
        Raises:
            ValueError: Se amount for <= 0
            Exception: Erro na transação do banco de dados
        """
        if amount <= 0:
            raise ValueError("Valor deve ser positivo para adicionar créditos")
        
        try:
            # Atualiza saldo
            old_balance = self.credits
            self.credits += amount
            
            # Registra transação
            from .credit_transaction import CreditTransaction
            transaction = CreditTransaction.create_transaction(
                user_id=self.id,
                amount=amount,
                transaction_type=transaction_type,
                description=description,
                balance_before=old_balance,
                balance_after=self.credits
            )
            
            # Commit da transação
            db.session.commit()
            
            logger.info(f"Créditos adicionados - User: {self.username}, Valor: {amount}, Novo saldo: {self.credits}")
            return transaction
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao adicionar créditos - User: {self.username}, Erro: {str(e)}")
            raise e
    
    def debit_credits(self, amount, transaction_type, description=None, allow_negative=False):
        """
        Debita créditos do usuário de forma segura.
        
        Args:
            amount (float): Valor a ser debitado (deve ser positivo)
            transaction_type (str): Tipo da transação
            description (str, optional): Descrição da transação
            allow_negative (bool): Permite saldo negativo
            
        Returns:
            CreditTransaction: Objeto da transação criada
            
        Raises:
            ValueError: Se amount <= 0 ou saldo insuficiente
            Exception: Erro na transação do banco de dados
        """
        if amount <= 0:
            raise ValueError("Valor deve ser positivo para debitar créditos")
        
        if not allow_negative and self.credits < amount:
            raise ValueError(f"Saldo insuficiente. Saldo atual: {self.credits:.2f}, Tentativa: {amount:.2f}")
        
        try:
            # Atualiza saldo
            old_balance = self.credits
            self.credits -= amount
            
            # Registra transação (negativo para débito)
            from .credit_transaction import CreditTransaction
            transaction = CreditTransaction.create_transaction(
                user_id=self.id,
                amount=-amount,
                transaction_type=transaction_type,
                description=description,
                balance_before=old_balance,
                balance_after=self.credits
            )
            
            # Commit da transação
            db.session.commit()
            
            logger.info(f"Créditos debitados - User: {self.username}, Valor: {amount}, Novo saldo: {self.credits}")
            return transaction
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao debitar créditos - User: {self.username}, Erro: {str(e)}")
            raise e
    
    def has_sufficient_credits(self, amount):
        """
        Verifica se o usuário tem créditos suficientes.
        
        Args:
            amount (float): Valor a ser verificado
            
        Returns:
            bool: True se tem saldo suficiente
        """
        return self.credits >= amount
    
    def get_credit_balance(self):
        """
        Retorna o saldo atual de créditos formatado.
        
        Returns:
            dict: Informações do saldo
        """
        return {
            'balance': round(self.credits, 2),
            'formatted': f"{self.credits:.2f}",
            'last_updated': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def get_credit_history(self, limit=10, offset=0):
        """
        Retorna o histórico de transações de crédito.
        
        Args:
            limit (int): Número máximo de transações
            offset (int): Offset para paginação
            
        Returns:
            list: Lista de transações ordenadas por data
        """
        return self.credit_transactions.order_by(
            db.desc('created_at')
        ).offset(offset).limit(limit).all()
    
    def __repr__(self):
        return f'<User {self.username} - {self.credits:.2f} créditos>'
