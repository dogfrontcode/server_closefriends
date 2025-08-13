# 🚗 OnlyMonkeys - Sistema de Geração de CNH

Sistema completo para geração de CNH (Carteira Nacional de Habilitação) digital com sistema de créditos e pagamentos PIX integrados.

## 📋 Índice
- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Como Rodar](#como-rodar)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Sistema de Créditos](#sistema-de-créditos)
- [Sistema PIX](#sistema-pix)
- [API Endpoints](#api-endpoints)
- [Administração](#administração)
- [Contribuindo](#contribuindo)

## 🎯 Sobre o Projeto

O **OnlyMonkeys** é um sistema web desenvolvido em Flask que permite a geração de CNH digitais personalizadas. O sistema inclui:

- **Sistema de usuários** com autenticação e sessões persistentes
- **Sistema de créditos** para controle de uso
- **Pagamentos PIX** integrados com gateway Flucsus
- **Geração de CNH** com dados personalizados
- **Interface moderna** e responsiva
- **Sistema de administração** via linha de comando

## ✨ Funcionalidades

### 🔐 Autenticação e Usuários
- Registro e login de usuários
- Sessões persistentes (2 horas)
- Controle de acesso por sessão

### 💳 Sistema de Créditos
- Saldo de créditos por usuário
- Histórico completo de transações
- Adição manual de créditos via admin
- Tipos de transação: PIX, manual, consumo

### 💰 Pagamentos PIX
- Integração com gateway **Flucsus**
- Valores fixos: R$ 10, R$ 25, R$ 50, R$ 100
- QR Code e código PIX para pagamento
- Confirmação automática via webhook
- Monitoramento de status em tempo real

### 🚗 Geração de CNH
- Interface para dados personalizados
- Geração de imagem da CNH
- Thumbnail automático
- Histórico de CNH geradas
- Consumo de créditos por geração

### 📊 Dashboard
- Estatísticas do usuário
- Histórico de transações
- Gerenciamento de CNH
- Interface moderna e responsiva

## 🛠️ Tecnologias

### Backend
- **Python 3.8+**
- **Flask** - Framework web
- **SQLAlchemy** - ORM para banco de dados
- **SQLite** - Banco de dados
- **Requests** - Integração com APIs externas

### Frontend
- **HTML5/CSS3**
- **JavaScript** (Vanilla)
- **Tailwind CSS** - Framework CSS
- **Responsive Design**

### Integrações
- **Flucsus** - Gateway de pagamentos PIX
- **PIL (Pillow)** - Manipulação de imagens

## 🚀 Como Rodar

### Pré-requisitos
```bash
# Python 3.8 ou superior
python3 --version

# Pip (gerenciador de pacotes)
pip3 --version
```

### Instalação
```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/onlymonkeys.git
cd onlymonkeys

# 2. Instale as dependências
pip3 install -r requirements.txt

# 3. Execute o servidor
python3 run.py
```

### Configuração PIX (Opcional)
Se quiser usar PIX real, configure as credenciais da Flucsus em `controllers/pix_payment.py`:
```python
FLUCSUS_PUBLIC_KEY = "sua_chave_publica"
FLUCSUS_SECRET_KEY = "sua_chave_secreta"
```

## 📁 Estrutura do Projeto

```
onlymonkeys/
├── __init__.py                 # Configuração principal do Flask
├── run.py                     # Servidor de desenvolvimento
├── requirements.txt           # Dependências Python
├── 
├── controllers/               # Controladores da aplicação
│   ├── auth.py               # Autenticação e usuários
│   ├── cnh.py                # Geração de CNH
│   ├── credits.py            # Sistema de créditos
│   └── pix_payment.py        # Pagamentos PIX
├── 
├── models/                    # Modelos do banco de dados
│   ├── user.py               # Modelo de usuário
│   ├── cnh_request.py        # Modelo de CNH
│   └── credit_transaction.py # Modelo de transações
├── 
├── services/                  # Serviços auxiliares
│   ├── cnh_generator.py      # Geração de imagens CNH
│   └── pix_recharge_service.py # Serviço PIX
├── 
├── templates/                 # Templates HTML
│   ├── home.html             # Página principal
│   ├── index.html            # Login
│   └── register.html         # Registro
├── 
├── static/                    # Arquivos estáticos
│   ├── fonts/                # Fontes
│   ├── uploads/              # CNHs organizadas por usuário/CPF
│   └── cnh_matriz/           # Templates da CNH
├── 
├── instance/                  # Banco de dados
│   └── app.db                # SQLite database
└── 
└── add_credits_manual.py      # Script para adicionar créditos
```

## 💳 Sistema de Créditos

### Como Funciona
1. Usuários começam com **0 créditos**
2. Cada **CNH gerada** consome **1 crédito**
3. Créditos podem ser adicionados via:
   - **PIX** (valores fixos)
   - **Administração manual**

### Tipos de Transação
- `pix_pending` - PIX criado, aguardando pagamento
- `pix_confirmed` - PIX confirmado, créditos adicionados
- `pix_failed` - PIX falhou ou expirou
- `manual_credit` - Créditos adicionados manualmente
- `cnh_generation` - Créditos consumidos na geração

### Adicionar Créditos Manualmente
```bash
# Ver usuários disponíveis
python3 add_credits_manual.py --list-users

# Adicionar créditos
python3 add_credits_manual.py usuario 50.00 "Crédito promocional"

# Ver ajuda completa
python3 add_credits_manual.py --help
```

## 💰 Sistema PIX

### Integração Flucsus
- **Gateway**: Flucsus (https://flucsus.com.br)
- **Valores fixos**: R$ 10, R$ 25, R$ 50, R$ 100
- **Produto**: "RECARGA"

### Fluxo de Pagamento
1. **Usuário** clica em valor PIX
2. **Sistema** cria transação na Flucsus
3. **Modal** exibe QR Code e código PIX
4. **Usuário** paga via app bancário
5. **Webhook** confirma pagamento
6. **Créditos** são adicionados automaticamente

### Monitoramento
- Status em tempo real (polling a cada 3s)
- Timeout de 15 minutos
- Logs detalhados de todas as operações

## 🔌 API Endpoints

### Autenticação
```
POST /login              # Login do usuário
POST /register           # Registro de usuário
POST /logout             # Logout
GET  /api/session/check  # Verificar sessão
```

### Créditos
```
GET  /api/credits/balance      # Saldo atual
GET  /api/credits/transactions # Histórico de transações
```

### PIX
```
POST /api/pix/create-payment   # Criar pagamento PIX
GET  /api/pix/check-payment/:id # Verificar status
POST /api/pix/webhook          # Webhook da Flucsus
```

### CNH
```
POST /api/cnh/generate    # Gerar nova CNH
GET  /api/cnh/my-cnhs     # Listar CNH do usuário
GET  /api/cnh/stats       # Estatísticas do usuário
```

## ⚙️ Administração

### Scripts Disponíveis
```bash
# Adicionar créditos manualmente
python3 add_credits_manual.py usuario 50.00 "Descrição"

# Visualizar banco de dados
python3 view_database.py

# Executar servidor
python3 run.py
```

### Logs
- Todos os logs são salvos no console
- Incluem: operações PIX, transações, geração de CNH
- Nível de log configurável

### Backups
- Backups automáticos do banco em `instance/`
- Nomenclatura: `app_backup_[feature]_[timestamp].db`

## 🔧 Configurações Importantes

### Sessões
```python
# __init__.py
PERMANENT_SESSION_LIFETIME = timedelta(hours=2)  # 2 horas
SESSION_REFRESH_EACH_REQUEST = True              # Renovar automaticamente
```

### PIX (Flucsus)
```python
# controllers/pix_payment.py
FLUCSUS_PUBLIC_KEY = "sua_chave_publica"
FLUCSUS_SECRET_KEY = "sua_chave_secreta"
FLUCSUS_API_URL = "https://app.flucsus.com.br/api/v1"
```

### Banco de Dados
```python
# __init__.py
SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
```

## 🤝 Contribuindo

### Para Adicionar Novas Funcionalidades

1. **Modelos**: Adicione em `models/`
2. **Controladores**: Crie em `controllers/`
3. **Templates**: Adicione em `templates/`
4. **Migrations**: Execute scripts de migração
5. **Testes**: Crie scripts de teste

### Padrões do Código
- **Logs**: Use logging para todas as operações importantes
- **Validação**: Sempre valide dados de entrada
- **Transações**: Use transações do SQLAlchemy para operações críticas
- **Comentários**: Documente funções complexas

### Estrutura de Commits
```
feat: adiciona nova funcionalidade
fix: corrige bug
docs: atualiza documentação
style: ajustes de estilo
refactor: refatoração de código
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique os **logs** no console
2. Consulte a **documentação** dos endpoints
3. Teste com **scripts auxiliares**
4. Verifique o **banco de dados** com `view_database.py`

## 📝 Licença

Este projeto é privado e não possui licença pública.

---

**Desenvolvido com ❤️ para geração de CNH digital**
