# -*- coding: utf-8 -*-
"""
🔄 Migração - Adicionar campos QR code na tabela cnh_requests

Script para adicionar os novos campos qr_code_url e qr_code_path na tabela existente.
"""

import sys
import os
import logging

# Adicionar diretório raiz ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate_qr_fields():
    """Adiciona campos QR code na tabela cnh_requests."""
    try:
        from __init__ import app, db
        
        logger.info("🔄 Iniciando migração dos campos QR code...")
        
        with app.app_context():
            # Executar ALTER TABLE para adicionar novos campos
            with db.engine.connect() as conn:
                try:
                    # Adicionar campo qr_code_url
                    conn.execute(db.text("""
                        ALTER TABLE cnh_requests 
                        ADD COLUMN qr_code_url VARCHAR(500)
                    """))
                    logger.info("✅ Campo qr_code_url adicionado")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        logger.info("ℹ️ Campo qr_code_url já existe")
                    else:
                        logger.error(f"❌ Erro ao adicionar qr_code_url: {e}")
                
                try:
                    # Adicionar campo qr_code_path
                    conn.execute(db.text("""
                        ALTER TABLE cnh_requests 
                        ADD COLUMN qr_code_path VARCHAR(255)
                    """))
                    logger.info("✅ Campo qr_code_path adicionado")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        logger.info("ℹ️ Campo qr_code_path já existe")
                    else:
                        logger.error(f"❌ Erro ao adicionar qr_code_path: {e}")
                
                # Commit das mudanças
                conn.commit()
            
            logger.info("🎉 Migração concluída com sucesso!")
            return True
            
    except Exception as e:
        logger.error(f"💥 Erro na migração: {str(e)}")
        return False

if __name__ == "__main__":
    success = migrate_qr_fields()
    if success:
        print("✅ Migração executada com sucesso!")
    else:
        print("❌ Falha na migração!")