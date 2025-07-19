#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
💪 FORÇA CRIAÇÃO DO CAMPO CNH_PASSWORD
====================================

Script que força a criação da coluna cnh_password diretamente no SQLite,
contornando problemas de cache do SQLAlchemy.

Usage:
    python force_create_cnh_password.py
"""

import sys
import os
import sqlite3
from datetime import datetime

# Adicionar o diretório do projeto ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from __init__ import app

def get_database_path():
    """Obtém o caminho do banco de dados."""
    with app.app_context():
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        if db_uri.startswith('sqlite:///'):
            return db_uri.replace('sqlite:///', '')
        else:
            # Para URLs absolutas
            return db_uri.replace('sqlite://', '')

def check_table_structure():
    """Verifica a estrutura atual da tabela cnh_requests."""
    try:
        db_path = get_database_path()
        
        if not os.path.exists(db_path):
            print("❌ Banco de dados não encontrado!")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a tabela existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cnh_requests'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ Tabela cnh_requests não existe!")
            conn.close()
            return False
        
        # Verificar colunas existentes
        cursor.execute("PRAGMA table_info(cnh_requests)")
        columns = cursor.fetchall()
        
        print(f"🔍 Estrutura da tabela cnh_requests ({len(columns)} colunas):")
        column_names = []
        for col in columns:
            col_id, col_name, col_type, not_null, default_val, pk = col
            print(f"   {col_name}: {col_type}")
            column_names.append(col_name)
        
        # Verificar se cnh_password existe
        has_password_field = 'cnh_password' in column_names
        print(f"\n🔐 Campo cnh_password: {'✅ EXISTE' if has_password_field else '❌ NÃO EXISTE'}")
        
        conn.close()
        return has_password_field
        
    except Exception as e:
        print(f"❌ Erro ao verificar estrutura: {str(e)}")
        return False

def force_add_cnh_password_column():
    """Força a adição da coluna cnh_password."""
    try:
        db_path = get_database_path()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("💪 Forçando criação da coluna cnh_password...")
        
        # Tentar adicionar a coluna
        cursor.execute("ALTER TABLE cnh_requests ADD COLUMN cnh_password VARCHAR(4)")
        conn.commit()
        
        print("✅ Coluna cnh_password adicionada com sucesso!")
        
        # Verificar se foi criada
        cursor.execute("PRAGMA table_info(cnh_requests)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'cnh_password' in columns:
            print("✓ Verificação: Coluna existe na tabela")
            conn.close()
            return True
        else:
            print("❌ Erro: Coluna não foi criada")
            conn.close()
            return False
            
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✅ Coluna cnh_password já existe!")
            conn.close()
            return True
        else:
            print(f"❌ Erro SQLite: {str(e)}")
            conn.close()
            return False
    except Exception as e:
        print(f"❌ Erro geral: {str(e)}")
        if 'conn' in locals():
            conn.close()
        return False

def populate_existing_cnhs():
    """Popula senhas para CNHs existentes que não têm senha."""
    try:
        print("🔄 Populando senhas para CNHs existentes...")
        
        # Importar modelos APÓS garantir que a coluna existe
        from models import db
        from models.cnh_request import CNHRequest
        
        with app.app_context():
            # Buscar CNHs sem senha
            cnhs_sem_senha = CNHRequest.query.filter(
                (CNHRequest.cnh_password == None) | (CNHRequest.cnh_password == '')
            ).all()
            
            if not cnhs_sem_senha:
                print("✅ Todas as CNHs já possuem senha!")
                return True
            
            print(f"📊 Encontradas {len(cnhs_sem_senha)} CNH(s) sem senha")
            
            cnhs_atualizadas = 0
            for cnh in cnhs_sem_senha:
                try:
                    # Gerar senha
                    if cnh.data_nascimento:
                        senha = f"{cnh.data_nascimento.day:02d}{cnh.data_nascimento.month:02d}"
                        print(f"  🔑 CNH {cnh.id}: Senha {senha} (data: {cnh.data_nascimento.strftime('%d/%m/%Y')})")
                    else:
                        senha = "0101"
                        print(f"  📅 CNH {cnh.id}: Senha padrão {senha} (sem data)")
                    
                    cnh.cnh_password = senha
                    cnhs_atualizadas += 1
                    
                except Exception as e:
                    print(f"  ❌ Erro na CNH {cnh.id}: {str(e)}")
            
            # Salvar no banco
            if cnhs_atualizadas > 0:
                db.session.commit()
                print(f"💾 {cnhs_atualizadas} senha(s) salva(s) com sucesso!")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao popular senhas: {str(e)}")
        return False

def create_test_user_and_cnh():
    """Cria usuário e CNH de teste se não existirem."""
    try:
        print("👤 Verificando usuário de teste...")
        
        from models import db
        from models.user import User
        from models.cnh_request import CNHRequest
        from datetime import date
        
        with app.app_context():
            # Verificar se admin existe
            admin = User.query.filter_by(username='admin').first()
            
            if not admin:
                print("🆕 Criando usuário admin...")
                admin = User(
                    username='admin',
                    phone_number='11999999999',
                    credits=1000.0
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                print("✅ Usuário admin criado!")
            else:
                print("✅ Usuário admin já existe")
            
            # Verificar se tem CNH de teste
            test_cnh = CNHRequest.query.filter_by(user_id=admin.id).first()
            
            if not test_cnh:
                print("🆕 Criando CNH de teste...")
                test_cnh = CNHRequest(
                    user_id=admin.id,
                    nome_completo="João Silva Santos",
                    cpf="123.456.789-00",
                    data_nascimento=date(1990, 3, 15),  # 15/03 → senha: 1503
                    local_nascimento="São Paulo",
                    uf_nascimento="SP",
                    nacionalidade="Brasileiro",
                    sexo_condutor="M",
                    categoria_habilitacao="B",
                    custo=5.0,
                    status="completed"
                )
                
                # Definir senha manualmente (já que a coluna agora existe)
                test_cnh.cnh_password = "1503"  # 15/03
                
                db.session.add(test_cnh)
                db.session.commit()
                
                print("✅ CNH de teste criada:")
                print(f"   🆔 ID: {test_cnh.id}")
                print(f"   📄 CPF: {test_cnh.cpf}")
                print(f"   🔐 Senha: {test_cnh.cnh_password}")
            else:
                print("✅ CNH de teste já existe")
                print(f"   🆔 ID: {test_cnh.id}")
                print(f"   📄 CPF: {test_cnh.cpf}")
                print(f"   🔐 Senha: {test_cnh.cnh_password}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao criar dados de teste: {str(e)}")
        return False

def test_api_login():
    """Testa a API de login CNH."""
    try:
        print("\n🧪 Testando API de login CNH...")
        
        from models.cnh_request import CNHRequest
        
        with app.app_context():
            # Buscar uma CNH para testar
            test_cnh = CNHRequest.query.first()
            
            if not test_cnh:
                print("❌ Nenhuma CNH encontrada para teste")
                return False
            
            print(f"🔍 Testando CNH ID {test_cnh.id}:")
            print(f"   📄 CPF: {test_cnh.cpf}")
            print(f"   🔐 Senha: {test_cnh.cnh_password}")
            
            # Testar método de validação
            if test_cnh.validar_senha_cnh(test_cnh.cnh_password):
                print("✅ Validação de senha OK!")
            else:
                print("❌ Validação de senha FALHOU!")
                return False
            
            # Mostrar comando para teste manual
            cpf = test_cnh.cpf or "123.456.789-00"
            senha = test_cnh.cnh_password or "1503"
            
            print(f"\n🧪 Teste manual da API:")
            print(f"curl \"http://localhost:5001/api/cnh/consultar/login?cpf={cpf}&senha={senha}\"")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        return False

def main():
    """Função principal."""
    print("💪 FORÇA CRIAÇÃO DO CAMPO CNH_PASSWORD")
    print("=" * 50)
    
    try:
        # PASSO 1: Verificar estrutura atual
        print("PASSO 1: Verificando estrutura da tabela...")
        has_password = check_table_structure()
        
        # PASSO 2: Forçar criação da coluna se necessário
        if not has_password:
            print("\nPASSO 2: Forçando criação da coluna...")
            if not force_add_cnh_password_column():
                print("💥 ERRO: Não foi possível criar a coluna!")
                return False
        else:
            print("\n✅ Campo cnh_password já existe!")
        
        # PASSO 3: Popular CNHs existentes
        print("\nPASSO 3: Populando senhas...")
        if not populate_existing_cnhs():
            print("⚠️  Erro ao popular senhas")
        
        # PASSO 4: Criar dados de teste
        print("\nPASSO 4: Criando dados de teste...")
        if not create_test_user_and_cnh():
            print("⚠️  Erro ao criar dados de teste")
        
        # PASSO 5: Testar funcionalidade
        if not test_api_login():
            print("⚠️  Erro nos testes")
        
        print("\n🎉 PROCESSO CONCLUÍDO!")
        print("\n📞 PRÓXIMOS PASSOS:")
        print("  1. python run.py")
        print("  2. Login: admin / admin123")
        print("  3. Criar nova CNH pelo formulário")
        print("  4. Testar API de login")
        
        return True
        
    except Exception as e:
        print(f"\n💥 ERRO CRÍTICO: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 