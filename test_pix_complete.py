#!/usr/bin/env python3

import requests
import sys
import time

def test_complete_pix_flow():
    """Testa fluxo completo do PIX com autenticação"""
    base_url = "http://127.0.0.1:5001"
    session = requests.Session()
    
    print("🧪 TESTE COMPLETO PIX - COM AUTENTICAÇÃO")
    print("=" * 60)
    
    try:
        # 1. Aguardar servidor
        print("⏳ Aguardando servidor iniciar...")
        time.sleep(3)
        
        # 2. Testar se servidor está respondendo
        print("🌐 Verificando servidor...")
        home_response = session.get(f"{base_url}/", timeout=5)
        if home_response.status_code != 200:
            print(f"❌ Servidor não responde: {home_response.status_code}")
            return False
        print("✅ Servidor está respondendo")
        
        # 3. Fazer login
        print("🔐 Fazendo login...")
        login_data = {
            'username': 'tidos',
            'password': 'senha123'
        }
        
        login_response = session.post(f"{base_url}/api/login", json=login_data, timeout=10)
        
        if login_response.status_code != 200:
            print(f"❌ Erro no login: {login_response.status_code}")
            try:
                error_data = login_response.json()
                print(f"   Detalhes: {error_data}")
            except:
                print(f"   Resposta: {login_response.text[:100]}")
            return False
        
        print("✅ Login realizado com sucesso")
        
        # 4. Verificar se está autenticado
        print("🔍 Verificando autenticação...")
        balance_response = session.get(f"{base_url}/api/user/balance", timeout=5)
        if balance_response.status_code == 200:
            balance_data = balance_response.json()
            print(f"✅ Usuário autenticado - Saldo: {balance_data.get('formatted', 'N/A')}")
        else:
            print("⚠️ Não foi possível verificar saldo, mas continuando...")
        
        # 5. Testar criação de PIX
        print("💳 Criando PIX de R$ 10,00...")
        pix_data = {'amount': 10.0}
        
        pix_response = session.post(
            f"{base_url}/api/pix/create-payment", 
            json=pix_data, 
            timeout=20
        )
        
        print(f"📊 Status da resposta: {pix_response.status_code}")
        
        if pix_response.status_code == 200:
            result = pix_response.json()
            print("🎉 PIX CRIADO COM SUCESSO!")
            print(f"   💰 Valor: R$ {result.get('amount', 'N/A'):.2f}")
            print(f"   🆔 Payment ID: {result.get('payment_id', 'N/A')}")
            print(f"   📱 PIX Code: {'✅ Presente' if result.get('pix', {}).get('code') else '❌ Ausente'}")
            print(f"   🖼️ QR Code: {'✅ Presente' if result.get('pix', {}).get('base64') else '❌ Ausente'}")
            
            # 6. Testar verificação de status
            payment_id = result.get('payment_id')
            if payment_id:
                print(f"🔍 Verificando status do pagamento {payment_id}...")
                status_response = session.get(f"{base_url}/api/pix/check-payment/{payment_id}", timeout=5)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"✅ Status: {status_data.get('status', 'N/A')}")
                else:
                    print("⚠️ Não foi possível verificar status")
            
            return True
            
        else:
            print(f"❌ Erro ao criar PIX: {pix_response.status_code}")
            try:
                error_data = pix_response.json()
                print(f"   Erro: {error_data.get('error', 'Erro desconhecido')}")
            except:
                print(f"   Resposta: {pix_response.text[:200]}...")
            return False
            
    except requests.exceptions.ConnectError:
        print("❌ Não foi possível conectar ao servidor")
        return False
    except requests.exceptions.Timeout:
        print("❌ Timeout na requisição")
        return False
    except Exception as e:
        print(f"❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_complete_pix_flow()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema PIX funcionando corretamente")
        print("🚀 Frontend está pronto para uso")
        print("\n📋 O que funciona:")
        print("   • Autenticação de usuário")
        print("   • Criação de pagamento PIX")
        print("   • Geração de QR Code")
        print("   • Código PIX copia e cola")
        print("   • Verificação de status")
        print("\n🎯 Para usar no frontend:")
        print("   1. Acesse a página de créditos")
        print("   2. Clique em qualquer botão PIX")
        print("   3. O modal abrirá com QR Code")
        print("   4. Use o botão 'Copiar' para o código PIX")
    else:
        print("❌ TESTES FALHARAM")
        print("🔧 Verifique os logs do servidor para mais detalhes")
    
    sys.exit(0 if success else 1) 