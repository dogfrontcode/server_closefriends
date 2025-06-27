#!/usr/bin/env python3

import sqlite3
import os
from __init__ import app
from models.user import User
from models import db

def view_database():
    """Visualiza o conteúdo do banco de dados de forma organizada"""
    
    db_path = "instance/app.db"
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado!")
        return
    
    print("=" * 60)
    print("🗄️  VISUALIZAÇÃO DO BANCO DE DADOS")
    print("=" * 60)
    
    # Conecta ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Lista todas as tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📊 TABELAS ENCONTRADAS: {len(tables)}")
        for table in tables:
            print(f"   • {table[0]}")
        
        print("\n" + "-" * 60)
        
        # Visualiza tabela users
        if ('users',) in tables:
            print("👤 USUÁRIOS CADASTRADOS:")
            print("-" * 60)
            
            cursor.execute("SELECT id, username, phone_number FROM users;")
            users = cursor.fetchall()
            
            if users:
                print(f"{'ID':<5} {'USERNAME':<15} {'TELEFONE':<15}")
                print("-" * 40)
                for user in users:
                    print(f"{user[0]:<5} {user[1]:<15} {user[2]:<15}")
                
                print(f"\n📈 Total de usuários: {len(users)}")
            else:
                print("   Nenhum usuário encontrado.")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Erro ao ler banco de dados: {e}")
    finally:
        conn.close()

def reset_user_password():
    """Redefine a senha de um usuário"""
    with app.app_context():
        username = input("\n🔑 Digite o username para redefinir senha: ")
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"❌ Usuário '{username}' não encontrado!")
            return
        
        new_password = input(f"🔒 Digite a nova senha para '{username}': ")
        user.set_password(new_password)
        
        try:
            db.session.commit()
            print(f"✅ Senha alterada com sucesso!")
            print(f"   👤 Usuário: {username}")
            print(f"   🔑 Nova senha: {new_password}")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro: {e}")

def main_menu():
    """Menu principal"""
    while True:
        print("\n" + "=" * 40)
        print("🛠️  GERENCIADOR DE BANCO DE DADOS")
        print("=" * 40)
        print("1. 👀 Visualizar banco de dados")
        print("2. 🔑 Redefinir senha de usuário")
        print("3. 🚪 Sair")
        print("-" * 40)
        
        choice = input("Escolha uma opção (1-3): ").strip()
        
        if choice == '1':
            view_database()
        elif choice == '2':
            reset_user_password()
        elif choice == '3':
            print("👋 Até mais!")
            break
        else:
            print("❌ Opção inválida!")

if __name__ == '__main__':
    main_menu() 