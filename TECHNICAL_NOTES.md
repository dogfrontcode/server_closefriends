# 🔧 Notas Técnicas - OnlyMonkeys

Informações técnicas específicas para desenvolvedores que precisam modificar ou estender o sistema.

## 📋 Configurações Atuais do Sistema

### Versões das Dependências
- **Python**: 3.8+ (testado com 3.11)
- **Flask**: 2.3.0+
- **SQLAlchemy**: 1.4+
- **Requests**: 2.31.0
- **Pillow**: Para manipulação de imagens

### Configurações de Sessão
```python
PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
SESSION_REFRESH_EACH_REQUEST = True
SECRET_KEY = "your-secret-key"
```

### Configurações PIX Flucsus
```python
FLUCSUS_PUBLIC_KEY = "galinhada_aktclpxexbzghhx1"
FLUCSUS_SECRET_KEY = "4fq962d1pgzdfomyoy7exrifu8kmom73o16yrco5sj4p0zti8gizrj4xk6zivwue"
FLUCSUS_API_URL = "https://app.flucsus.com.br/api/v1"
```

## 🗃️ Estrutura do Banco de Dados

### Tabela `user`
- `id` (PK)
- `username` (unique)
- `password_hash`
- `credits` (decimal)
- `created_at`

### Tabela `credit_transaction`
- `id` (PK)
- `user_id` (FK)
- `amount` (decimal)
- `transaction_type` (string)
- `description` (string)
- `balance_before` (decimal)
- `balance_after` (decimal)
- `reference_id` (string, indexed)
- `created_at`

### Tabela `cnh_request`
- `id` (PK)
- `user_id` (FK)
- `full_name` (string)
- `cpf` (string)
- `rg` (string)
- `birth_date` (date)
- `mother_name` (string)
- `father_name` (string)
- `registration_number` (string)
- `category` (string)
- `issue_date` (date)
- `expiry_date` (date)
- `image_path` (string)
- `thumb_path` (string)
- `status` (string)
- `created_at`

## 🔗 Endpoints Críticos

### Sistema PIX
- **Criação**: `POST /api/pix/create-payment`
- **Status**: `GET /api/pix/check-payment/<id>`
- **Webhook**: `POST /api/pix/webhook`
- **Confirmação**: `POST /api/pix/confirm-payment`

### Autenticação
- **Login**: `POST /login`
- **Registro**: `POST /register`
- **Logout**: `POST /logout`
- **Verificação de Sessão**: `GET /api/session/check`

## 🛠️ Modificações Comuns

### Adicionar Novo Valor PIX
1. Editar `templates/home.html` (botões PIX)
2. Modificar validação em `controllers/pix_payment.py`
3. Atualizar frontend JavaScript

### Modificar Template de CNH
1. Alterar `services/cnh_generator.py`
2. Ajustar posições de texto e imagens
3. Testar com dados de exemplo

### Adicionar Novo Campo na CNH
1. Migrar banco: adicionar campo em `cnh_request`
2. Atualizar formulário em `templates/home.html`
3. Modificar `controllers/cnh.py` (validação e salvamento)
4. Ajustar `services/cnh_generator.py` (renderização)

## 🔒 Segurança

### Validações Importantes
```python
# Sempre validar usuário logado
if 'user_id' not in session:
    return redirect(url_for('auth.login'))

# Verificar créditos antes de operações
if user.credits < required_credits:
    return jsonify({'error': 'Créditos insuficientes'})

# Validar dados de entrada
if not all([name, cpf, rg]):
    return jsonify({'error': 'Campos obrigatórios'})
```

### Headers de Segurança
```python
# Em produção, configure:
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True  # No JS access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
```

## 📊 Logs e Monitoramento

### Estrutura de Logs
```python
logger.info(f"Operação realizada - User: {username}, Valor: {amount}")
logger.warning(f"Tentativa falhou - Razão: {error}")
logger.error(f"Erro crítico - {exception}")
```

### Locais dos Logs
- Console do servidor (run.py)
- Logs específicos por módulo
- Transações salvas no banco

## 🔄 Webhook PIX

### Estrutura Esperada
```json
{
  "eventType": "TRANSACTION_PAID",
  "data": {
    "transactionId": "cmcggl9i70whv11gnto0c0rhf",
    "status": "PAID",
    "amount": 10.00
  }
}
```

### Processo de Confirmação
1. Webhook recebe evento
2. Valida transactionId no banco
3. Consulta status na Flucsus
4. Atualiza transação local
5. Adiciona créditos ao usuário

## 📦 Deploy e Produção

### Variáveis de Ambiente Recomendadas
```bash
export FLASK_ENV=production
export SECRET_KEY="production-secret-key"
export FLUCSUS_PUBLIC_KEY="prod-public-key"
export FLUCSUS_SECRET_KEY="prod-secret-key"
export DATABASE_URL="sqlite:///prod.db"
```

### Configurações de Produção
```python
# Desabilitar debug
app.config['DEBUG'] = False

# Configurar database production
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

# Configurar logs
logging.basicConfig(level=logging.INFO)
```

## 🧪 Testes

### Scripts de Teste Disponíveis
- `test_pix_complete.py` - Testa sistema PIX completo
- `add_credits_manual.py` - Adiciona créditos manualmente
- `view_database.py` - Visualiza dados do banco

### Dados de Teste
```python
# Usuário de teste
username: "tidos"
password: "123456"
credits: 170.00

# PIX de teste
amounts: [10.00, 25.00, 50.00, 100.00]
```

## 🔧 Troubleshooting

### Problemas Comuns

#### Porta em Uso
```bash
# Encontrar processo na porta 5001
lsof -ti:5001

# Matar processo
kill -9 $(lsof -ti:5001)
```

#### Banco Corrompido
```bash
# Backup atual
cp instance/app.db instance/app_backup_$(date +%Y%m%d_%H%M%S).db

# Recriar tabelas
python3 -c "from __init__ import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

#### Sessões Perdidas
```python
# Verificar configuração de sessão
print(app.config['PERMANENT_SESSION_LIFETIME'])
print(app.config['SESSION_REFRESH_EACH_REQUEST'])
```

### Performance

#### Otimizações Implementadas
- Index em `reference_id` da tabela `credit_transaction`
- Sessões com renovação automática
- Queries otimizadas com limites
- Compressão de imagens (thumbnails)

#### Monitoramento
- Logs detalhados de tempo de resposta
- Contagem de CNH geradas por usuário
- Histórico de transações com paginação

## 📝 Próximas Melhorias

### Sugestões de Funcionalidades
1. **Dashboard Admin**: Interface web para administração
2. **Notificações**: Email/SMS para confirmação de pagamentos
3. **API Keys**: Sistema de chaves para integrações
4. **Backup Automático**: Agendamento de backups
5. **Métricas**: Dashboard com estatísticas de uso
6. **Múltiplos Gateways**: Suporte a outros meios de pagamento

### Refatorações Sugeridas
1. **Config Manager**: Centralizar configurações
2. **Exception Handler**: Tratamento global de erros
3. **Cache**: Redis para sessões e dados frequentes
4. **Queue System**: Celery para processamento assíncrono
5. **Tests**: Suite completa de testes automatizados 