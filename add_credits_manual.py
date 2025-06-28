#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script para adicionar créditos manualmente a usuários
Uso: python3 add_credits_manual.py <username> <valor> [descrição]

Exemplos:
python3 add_credits_manual.py tidos 50.00 "Crédito promocional"
python3 add_credits_manual.py joao 25.00 "Compensação por erro"
python3 add_credits_manual.py maria 100.00
"""

import sys
import argparse
from models.user import User
from models import db
from __init__ import create_app

def add_credits_to_user(username, amount, description=None):
    """
    Adiciona créditos a um usuário específico
    
    Args:
        username (str): Nome do usuário
        amount (float): Valor a ser adicionado
        description (str): Descrição opcional
    
    Returns:
        tuple: (success, message)
    """
    app = create_app()
    
    with app.app_context():
        try:
            # Buscar usuário
            user = User.query.filter_by(username=username).first()
            
            if not user:
                return False, f"❌ Usuário '{username}' não encontrado"
            
            # Validar valor
            if amount <= 0:
                return False, f"❌ Valor deve ser positivo: {amount}"
            
            # Saldo anterior
            old_balance = user.credits
            
            # Descrição padrão
            if not description:
                description = f"Crédito manual - R$ {amount:.2f}"
            
            # Adicionar créditos usando método seguro
            transaction = user.add_credits(
                amount=amount,
                transaction_type='manual_credit',
                description=description
            )
            
            return True, {
                'user_id': user.id,
                'username': user.username,
                'amount_added': amount,
                'old_balance': old_balance,
                'new_balance': user.credits,
                'transaction_id': transaction.id,
                'description': description
            }
            
        except Exception as e:
            return False, f"❌ Erro: {str(e)}"

def list_users(limit=10):
    """Lista usuários disponíveis"""
    app = create_app()
    
    with app.app_context():
        try:
            users = User.query.limit(limit).all()
            
            if not users:
                print("❌ Nenhum usuário encontrado")
                return
            
            print(f"\n📋 Usuários disponíveis (mostrando {len(users)}):")
            print("-" * 60)
            print(f"{'ID':<5} {'Username':<15} {'Saldo':<15} {'Criado em':<20}")
            print("-" * 60)
            
            for user in users:
                created = user.created_at.strftime('%d/%m/%Y %H:%M') if user.created_at else 'N/A'
                print(f"{user.id:<5} {user.username:<15} R$ {user.credits:<11.2f} {created:<20}")
            
            print("-" * 60)
            
        except Exception as e:
            print(f"❌ Erro ao listar usuários: {str(e)}")

def main():
    parser = argparse.ArgumentParser(
        description="Adicionar créditos manualmente a usuários",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python3 add_credits_manual.py tidos 50.00 "Crédito promocional"
  python3 add_credits_manual.py joao 25.00 "Compensação por erro"
  python3 add_credits_manual.py maria 100.00
  python3 add_credits_manual.py --list-users

Para ver usuários disponíveis:
  python3 add_credits_manual.py --list-users
        """
    )
    
    parser.add_argument('username', nargs='?', help='Nome do usuário')
    parser.add_argument('amount', nargs='?', type=float, help='Valor a ser adicionado (ex: 50.00)')
    parser.add_argument('description', nargs='?', help='Descrição opcional (ex: "Crédito promocional")')
    parser.add_argument('--list-users', '-l', action='store_true', help='Listar usuários disponíveis')
    
    args = parser.parse_args()
    
    # Mostrar ajuda se nenhum argumento
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Listar usuários
    if args.list_users:
        list_users()
        return
    
    # Validar argumentos obrigatórios
    if not args.username or args.amount is None:
        print("❌ Erro: Username e valor são obrigatórios")
        print("\nUso: python3 add_credits_manual.py <username> <valor> [descrição]")
        print("Exemplo: python3 add_credits_manual.py tidos 50.00 'Crédito promocional'")
        print("\nPara ver usuários: python3 add_credits_manual.py --list-users")
        return
    
    # Executar adição de créditos
    print(f"💳 Adicionando R$ {args.amount:.2f} para o usuário '{args.username}'...")
    
    success, result = add_credits_to_user(args.username, args.amount, args.description)
    
    if success:
        print("\n✅ CRÉDITOS ADICIONADOS COM SUCESSO!")
        print("=" * 50)
        print(f"👤 Usuário: {result['username']} (ID: {result['user_id']})")
        print(f"💰 Valor adicionado: R$ {result['amount_added']:.2f}")
        print(f"📊 Saldo anterior: R$ {result['old_balance']:.2f}")
        print(f"📈 Novo saldo: R$ {result['new_balance']:.2f}")
        print(f"🆔 ID da transação: {result['transaction_id']}")
        print(f"📝 Descrição: {result['description']}")
        print("=" * 50)
    else:
        print(f"\n{result}")

if __name__ == "__main__":
    main() 