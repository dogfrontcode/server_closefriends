#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 INICIALIZAÇÃO DO BANCO DE DADOS - Nova Arquitetura CNH
========================================================

Script para inicializar o banco de dados com todas as tabelas atualizadas,
incluindo o campo cnh_password.

Usage:
    python init_database.py
"""

import sys
import os
from datetime import datetime

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from __init__ import app
from models import db
from models.user import User
from models.credit_transaction import CreditTransaction
from models.cnh_request import CNHRequest

def backup_existing_database():
    """
    Faz backup do banco existente se houver dados importantes.
    """
    try:
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        if os.path.exists(db_path) and os.path.getsize(db_path) > 0:
            backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            import shutil
            shutil.copy2(db_path, backup_path)
            print(f"📋 Backup criado: {backup_path}")
            return True
        else:
            print("📋 Banco vazio - backup não necessário")
            return False
    except Exception as e:
        print(f"⚠️  Erro no backup: {str(e)} - Continuando sem backup...")
        return False

def delete_empty_database():
    """
    Remove banco de dados vazio para recriar do zero.
    """
    try:
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            print(f"📊 Tamanho do banco atual: {file_size} bytes")
            
            if file_size == 0:
                os.remove(db_path)
                print("🗑️  Banco vazio removido")
                return True
            else:
                print("⚠️  Banco contém dados - não será removido automaticamente")
                print("   Se quiser recriar, delete manualmente o arquivo app.db")
                return False
        else:
            print("📄 Nenhum banco existente encontrado")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao remover banco: {str(e)}")
        return False

def create_all_tables():
    """
    Cria todas as tabelas com a estrutura mais recente.
    """
    print("🏗️  Criando todas as tabelas...")
    
    with app.app_context():
        try:
            # Criar todas as tabelas
            db.create_all()
            
            # Verificar se as tabelas foram criadas
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print(f"✅ Tabelas criadas: {', '.join(tables)}")
            
            # Verificar especificamente a tabela cnh_requests
            if 'cnh_requests' in tables:
                columns = [col['name'] for col in inspector.get_columns('cnh_requests')]
                print(f"🔍 Colunas da tabela cnh_requests: {len(columns)} colunas")
                
                if 'cnh_password' in columns:
                    print("✅ Campo cnh_password criado com sucesso!")
                    return True
                else:
                    print("❌ Campo cnh_password NÃO foi criado")
                    return False
            else:
                print("❌ Tabela cnh_requests não foi criada")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao criar tabelas: {str(e)}")
            return False

def create_admin_user():
    """
    Cria um usuário administrador padrão para testes.
    """
    print("👤 Criando usuário administrador...")
    
    with app.app_context():
        try:
            # Verificar se já existe um admin
            admin = User.query.filter_by(username='admin').first()
            
            if admin:
                print("✅ Usuário admin já existe")
                return True
            
            # Criar usuário admin
            admin = User(
                username='admin',
                phone_number='11999999999',
                credits=1000.0  # 1000 créditos iniciais
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Usuário admin criado:")
            print("   👤 Username: admin")
            print("   🔐 Senha: admin123")
            print("   💰 Créditos: 1000.0")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar usuário admin: {str(e)}")
            return False

def create_sample_cnh():
    """
    Cria uma CNH de exemplo para testes.
    """
    print("🆔 Criando CNH de exemplo...")
    
    with app.app_context():
        try:
            # Buscar usuário admin
            admin = User.query.filter_by(username='admin').first()
            
            if not admin:
                print("❌ Usuário admin não encontrado")
                return False
            
            # Verificar se já existe uma CNH de exemplo
            existing_cnh = CNHRequest.query.filter_by(user_id=admin.id).first()
            
            if existing_cnh:
                print("✅ CNH de exemplo já existe")
                return True
            
            from datetime import date
            
            # Criar CNH de exemplo
            sample_cnh = CNHRequest(
                user_id=admin.id,
                nome_completo="João Silva Santos",
                cpf="123.456.789-00",
                data_nascimento=date(1990, 3, 15),  # 15/03/1990 → senha: 1503
                local_nascimento="São Paulo",
                uf_nascimento="SP",
                nacionalidade="Brasileiro",
                nome_pai="José Santos",
                nome_mae="Maria Silva",
                sexo_condutor="M",
                doc_identidade_numero="123456789",
                doc_identidade_orgao="SSP",
                doc_identidade_uf="SP",
                categoria_habilitacao="B",
                uf_cnh="SP",
                numero_registro="12345678901",
                local_municipio="São Paulo",
                local_uf="SP",
                custo=5.0,
                status="completed"
            )
            
            # Gerar senha automaticamente
            sample_cnh.set_senha_cnh()
            
            db.session.add(sample_cnh)
            db.session.commit()
            
            print("✅ CNH de exemplo criada:")
            print(f"   🆔 ID: {sample_cnh.id}")
            print(f"   👤 Nome: {sample_cnh.nome_completo}")
            print(f"   📄 CPF: {sample_cnh.cpf}")
            print(f"   📅 Data nascimento: {sample_cnh.data_nascimento.strftime('%d/%m/%Y')}")
            print(f"   🔐 Senha: {sample_cnh.cnh_password}")
            print(f"   🧪 Teste: curl \"http://localhost:5001/api/cnh/consultar/login?cpf={sample_cnh.cpf}&senha={sample_cnh.cnh_password}\"")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro ao criar CNH de exemplo: {str(e)}")
            return False

def verify_database():
    """
    Verifica se o banco foi criado corretamente.
    """
    print("\n🔍 Verificando banco de dados...")
    
    with app.app_context():
        try:
            # Contar registros
            users_count = User.query.count()
            cnhs_count = CNHRequest.query.count()
            transactions_count = CreditTransaction.query.count()
            
            print(f"📊 ESTATÍSTICAS:")
            print(f"   👥 Usuários: {users_count}")
            print(f"   🆔 CNHs: {cnhs_count}")
            print(f"   💰 Transações: {transactions_count}")
            
            # Testar uma consulta específica da nova coluna
            cnhs_with_password = CNHRequest.query.filter(CNHRequest.cnh_password != None).count()
            print(f"   🔐 CNHs com senha: {cnhs_with_password}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro na verificação: {str(e)}")
            return False

if __name__ == "__main__":
    """
    Executa a inicialização completa do banco de dados.
    """
    print("🚀 INICIALIZAÇÃO DO BANCO DE DADOS - NOVA ARQUITETURA")
    print("=" * 60)
    
    try:
        # PASSO 1: Backup (se necessário)
        backup_existing_database()
        
        # PASSO 2: Remover banco vazio
        if not delete_empty_database():
            print("⚠️  Banco não foi removido - verifique manualmente")
        
        # PASSO 3: Criar todas as tabelas
        if not create_all_tables():
            print("💥 ERRO: Falha na criação das tabelas")
            sys.exit(1)
        
        # PASSO 4: Criar usuário admin
        if not create_admin_user():
            print("⚠️  Usuário admin não foi criado - faça login manual")
        
        # PASSO 5: Criar CNH de exemplo
        if not create_sample_cnh():
            print("⚠️  CNH de exemplo não foi criada")
        
        # PASSO 6: Verificar tudo
        if verify_database():
            print("\n🎉 INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!")
            
            print(f"\n📞 PRÓXIMOS PASSOS:")
            print(f"  1. python run.py")
            print(f"  2. Acessar: http://localhost:5001")
            print(f"  3. Login: admin / admin123")
            print(f"  4. Testar criação de nova CNH")
            print(f"  5. Testar API de login CNH")
        else:
            print("\n⚠️  INICIALIZAÇÃO INCOMPLETA - Verificar logs")
            
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO: {str(e)}")
        print("Verifique se todas as dependências estão instaladas.")
        sys.exit(1) 