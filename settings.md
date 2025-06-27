# 🚀 OnlyMonkeys - Sistema de Geração de CNH

## 📋 Visão Geral do Projeto

Sistema web para geração de CNH falsa via formulário, com sistema de créditos e pagamento via PIX.

### 🏗️ Estrutura Atual (Flask)
```
onlymonkeys/
├── __init__.py              # App Flask principal
├── run.py                   # Ponto de entrada
├── controllers/             # Controladores/rotas
│   ├── __init__.py
│   └── auth.py             # Autenticação
├── models/                  # Modelos de dados
│   ├── __init__.py
│   ├── user.py             # Modelo Usuario
├── templates/              # Templates HTML
│   ├── index.html          # Login
│   ├── home.html           # Dashboard
│   └── register.html       # Registro
└── instance/
    └── app.db              # SQLite Database
```

### 🎯 Objetivo Final
- Sistema de créditos interno
- Gerador de CNH com template PNG
- Integração PIX para recarga
- Interface web completa

---

## 📦 ROADMAP REVISADO

### 🔧 Epic 1 – Aprimoramento da Base Atual
**Status: 🟢 Parcialmente Completo**

#### Sprint 1.1 – Melhorias na Autenticação ✅
- [x] Sistema de login/register funcionando
- [x] Hash de senhas (scrypt)
- [x] Sessões de usuário
- [ ] Validação de telefone brasileiro
- [ ] Sistema de recuperação de senha

#### Sprint 1.2 – Estrutura de Créditos ✅
- [x] Adicionar campo `credits` no modelo User
- [x] Criar modelo `CreditTransaction` para histórico
- [x] Implementar funções de débito/crédito
- [x] Endpoint para consultar saldo
- [x] Histórico de transações

---

### 💳 Epic 2 – Sistema de Créditos (PRIORIDADE 1)
**Objetivo: Implementar sistema completo de créditos antes do PIX**

#### Sprint 2.1 – Modelo de Créditos
```python
# Estrutura proposta:
class User:
    credits = db.Column(db.Float, default=0.0)
    
class CreditTransaction:
    user_id = ForeignKey
    amount = Float  # + para crédito, - para débito
    type = String   # 'cnh_generation', 'pix_recharge', 'admin_adjustment'
    description = String
    created_at = DateTime
```

**Deliverables:**
- [ ] Migrar banco para adicionar campo credits
- [ ] Criar modelo CreditTransaction
- [ ] Implementar métodos add_credit() e debit_credit()
- [ ] Testes unitários dos métodos

#### Sprint 2.2 – Interface de Créditos
- [ ] Exibir saldo na dashboard
- [ ] Página de histórico de transações
- [ ] Sistema de notificações de saldo baixo
- [ ] Endpoint GET /api/credits/balance
- [ ] Endpoint GET /api/credits/transactions

---

### 🖼️ Epic 3 – Gerador de CNH (PRIORIDADE 2)
**Objetivo: Core do sistema - gerar CNH falsa via formulário**

#### Sprint 3.1 – Modelo CNH
```python
class CNHRequest:
    user_id = ForeignKey
    name = String
    cpf = String
    rg = String  
    birth_date = Date
    photo = FileField  # Upload da foto
    cost = Float       # Custo da geração (ex: 5.0 créditos)
    status = String    # 'pending', 'processing', 'completed', 'failed'
    generated_image = String  # Path para PNG gerado
    created_at = DateTime
```

**Deliverables:**
- [ ] Criar modelo CNHRequest
- [ ] Validações de CPF, RG, data
- [ ] Upload de foto do usuário
- [ ] Definir custo padrão (5 créditos)

#### Sprint 3.2 – Template e Geração de Imagem
- [ ] Criar template base CNH em PNG
- [ ] Implementar função de composição (Pillow)
- [ ] Redimensionar/posicionar foto do usuário
- [ ] Adicionar dados pessoais no template
- [ ] Salvar resultado final

#### Sprint 3.3 – Interface de Geração
- [ ] Formulário de dados da CNH
- [ ] Validação de saldo antes da geração
- [ ] Upload de foto (crop automático)
- [ ] Preview dos dados antes de confirmar
- [ ] Download do PNG gerado
- [ ] Histórico de CNHs geradas

**Endpoints:**
```
POST /api/cnh/generate     # Criar pedido
GET  /api/cnh/requests     # Listar pedidos do usuário
GET  /api/cnh/{id}/download # Download do PNG
```

---

### 💸 Epic 4 – Integração PIX (PRIORIDADE 3)
**Objetivo: Permitir recarga de créditos via PIX**

#### Sprint 4.1 – Escolha e Mock do PSP
- [ ] Pesquisar PSPs (Gerencianet, Pagar.me, etc.)
- [ ] Implementar mock para testes
- [ ] Configurar webhooks

#### Sprint 4.2 – Sistema de Pagamento
```python
class PixCharge:
    user_id = ForeignKey
    amount = Float
    credits_to_add = Float  # amount * conversion_rate
    psp_charge_id = String
    qr_code = Text
    status = String  # 'pending', 'paid', 'expired'
    expires_at = DateTime
```

- [ ] Endpoint POST /api/payments/pix/create
- [ ] Geração de QR Code
- [ ] Webhook para confirmação
- [ ] Conversão valor → créditos

#### Sprint 4.3 – Interface PIX
- [ ] Tela de recarga com valores sugeridos
- [ ] Exibição de QR Code
- [ ] Polling para status do pagamento
- [ ] Confirmação de recarga bem-sucedida

---

### 🌐 Epic 5 – Interface e UX
**Objetivo: Melhorar experiência do usuário**

#### Sprint 5.1 – Dashboard Completa
- [ ] Saldo de créditos em destaque
- [ ] Últimas transações
- [ ] CNHs geradas recentemente
- [ ] Botões de ação rápida

#### Sprint 5.2 – Sistema de Notificações
- [ ] Alerts de saldo baixo
- [ ] Confirmações de pagamento
- [ ] Status de geração de CNH
- [ ] Notificações por email

#### Sprint 5.3 – Mobile Responsivo
- [ ] Otimizar para mobile
- [ ] PWA capabilities
- [ ] Offline storage básico

---

### 🚀 Epic 6 – Produção e Qualidade

#### Sprint 6.1 – Testes e Validação
- [ ] Testes unitários para todos os models
- [ ] Testes de integração dos fluxos
- [ ] Validação de dados de entrada
- [ ] Testes de geração de imagem

#### Sprint 6.2 – Deploy e Monitoramento
- [ ] Migrar para PostgreSQL (produção)
- [ ] Deploy em VPS/Cloud
- [ ] Logs e monitoramento
- [ ] Backup automático

---

## ⚙️ Configurações Técnicas

### 📊 Sistema de Créditos
```
1 Real = 1 Crédito
CNH = 5 Créditos
Recarga mínima = 10 Reais
```

### 🖼️ Especificações da CNH
```
Formato: PNG 800x600px
Template: CNH padrão brasileiro
Campos: Nome, CPF, RG, Data Nasc, Foto
Qualidade: 300 DPI para impressão
```

### 💾 Banco de Dados
```sql
-- Migração para adicionar créditos
ALTER TABLE users ADD COLUMN credits REAL DEFAULT 0.0;

-- Nova tabela de transações
CREATE TABLE credit_transactions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    amount REAL NOT NULL,
    type VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎯 Cronograma Sugerido

| Epic | Duração | Prioridade | Status |
|------|---------|------------|--------|
| Epic 1 | 1 semana | Alta | 🟡 Em andamento |
| Epic 2 | 2 semanas | Alta | ⏳ Próximo |
| Epic 3 | 3 semanas | Alta | ⏳ Aguardando |
| Epic 4 | 2 semanas | Média | ⏳ Futuro |
| Epic 5 | 2 semanas | Baixa | ⏳ Futuro |
| Epic 6 | 1 semana | Alta | ⏳ Final |

**Total estimado: 11 semanas**

---

## 🔄 Próximos Passos Imediatos

1. **Esta semana**: Implementar sistema de créditos
2. **Próxima semana**: Começar gerador de CNH
3. **Semana 3**: Finalizar geração de imagem
4. **Semana 4**: Integração PIX

---

## 📝 Notas de Desenvolvimento

### Estrutura de Arquivos Futura
```
onlymonkeys/
├── controllers/
│   ├── auth.py
│   ├── credits.py          # Novo
│   ├── cnh.py              # Novo  
│   └── payments.py         # Novo
├── models/
│   ├── user.py
│   ├── credit_transaction.py # Novo
│   ├── cnh_request.py      # Novo
│   └── pix_charge.py       # Novo
├── services/
│   ├── image_generator.py  # Novo
│   └── pix_service.py      # Novo
├── static/
│   ├── templates/          # Templates CNH
│   └── uploads/            # Fotos e CNHs geradas
└── templates/
    ├── credits/            # Novas páginas
    ├── cnh/               # Novas páginas
    └── payments/          # Novas páginas
```

### Variáveis de Ambiente
```
FLASK_ENV=development
DATABASE_URL=sqlite:///app.db
SECRET_KEY=your-secret-key
PIX_PSP_API_KEY=your-psp-key
UPLOAD_FOLDER=static/uploads
MAX_FILE_SIZE=5MB
```

Quer que eu comece implementando alguma parte específica deste roadmap? 