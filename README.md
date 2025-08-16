# 🦆 DuckTickets - Event Ticketing Platform

Sistema completo de venda de ingressos para eventos, desenvolvido com **FastAPI** e preparado para **AWS**.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-orange.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)

## 🚀 Funcionalidades

### 🎫 **Core Features**
- **Gestão de Eventos**: CRUD completo com lotes de ingressos
- **Checkout Inteligente**: Seleção e compra com preços dinâmicos
- **Autenticação Dupla**: Login separado para usuários e administradores
- **Painel Admin**: Interface completa para gestão de eventos e vendas
- **Meus Ingressos**: Visualização de ingressos com QR codes

### 🎨 **Interface Moderna**
- **Design Responsivo**: Bootstrap 5 + CSS customizado
- **Carrossel de Eventos**: Destaque visual na homepage
- **Fonte Personalizada**: Logo com fonte Orbitron (estilo digital)
- **UX Otimizada**: Navegação intuitiva e animações suaves

### 🔧 **Tecnologia**
- **Backend**: Python 3.11 + FastAPI + SQLAlchemy
- **Frontend**: Jinja2 + Bootstrap + Font Awesome + Google Fonts
- **Banco**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Deploy**: AWS Elastic Beanstalk ready
- **Testes**: Pytest + Suite funcional completa

## 📋 Pré-requisitos

- **Python 3.11+**
- **Git**
- **SQLite** (incluído no Python)

## 🛠️ Instalação Local

### 1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/ducktickets.git
cd ducktickets
```

### 2. **Instale dependências**
```bash
pip install -r requirements.txt
```

### 3. **Configure variáveis de ambiente**
```bash
cp .env.example .env
# Arquivo .env já vem configurado para desenvolvimento local
```

### 4. **Configure banco de dados**
```bash
# Execute migrations
alembic upgrade head

# Popule dados de exemplo
python scripts/seed.py
```

### 5. **Execute localmente**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

🎉 **Acesse**: http://localhost:8000

## 🧪 Executar Testes

### **Suite Completa de Testes**
```bash
python run_all_tests.py
```

### **Apenas Testes Unitários**
```bash
pytest tests/ -v
```

### **Apenas Testes Funcionais**
```bash
python test_functional.py
```

## 🎯 Como Usar

### **👤 Usuário Final**
1. Acesse a homepage
2. Navegue pelos eventos no carrossel
3. Clique em "Comprar Ingressos"
4. Preencha dados e finalize pedido
5. Faça login para ver "Meus Ingressos"

### **🔧 Administrador**
1. Acesse `/admin-login`
2. Use: `admin@ducktickets.com`
3. Gerencie eventos e lotes no painel admin
4. Visualize estatísticas e pedidos

## 🏗️ Arquitetura

```
DuckTickets/
├── app/
│   ├── models/          # SQLAlchemy models
│   ├── routes/          # FastAPI routes
│   ├── schemas/         # Pydantic schemas
│   ├── services/        # Business logic
│   └── main.py          # FastAPI app
├── templates/           # Jinja2 templates
├── tests/              # Unit tests
├── alembic/            # Database migrations
└── scripts/            # Utility scripts
```

## 🚀 Deploy AWS

### **Elastic Beanstalk**
```bash
# Instalar EB CLI
pip install awsebcli

# Inicializar
eb init ducktickets --platform python-3.11

# Criar ambiente
eb create production

# Deploy
eb deploy
```

### **Variáveis de Ambiente (Produção)**
```bash
eb setenv \
  DATABASE_URL=postgresql://user:pass@host:5432/db \
  SECRET_KEY=your-secret-key \
  ENVIRONMENT=production \
  DEBUG=false
```

## 📊 Funcionalidades Técnicas

### **🔒 Segurança**
- Headers de segurança (CSP, HSTS, X-Frame-Options)
- Rate limiting (100 req/min por IP)
- Validação de entrada com Pydantic
- Secrets via variáveis de ambiente

### **📈 Observabilidade**
- Logs estruturados com structlog
- Métricas CloudWatch ready
- X-Ray tracing (produção)
- Health check endpoint (`/healthz`)

### **🧪 Qualidade**
- Cobertura de testes: Unit + Functional + Links
- Linting e formatação
- Type hints
- Documentação automática (`/docs`)

## 🎨 Screenshots

### Homepage com Carrossel
- Design moderno com gradientes
- Carrossel de eventos destacados
- Preços dinâmicos baseados nos lotes

### Painel Admin
- Interface completa de gestão
- CRUD de eventos e lotes
- Estatísticas em tempo real

### Checkout Flow
- Formulário intuitivo
- Seleção de quantidade
- Confirmação de pedido

## 🤝 Contribuição

1. **Fork** o projeto
2. **Crie** uma branch (`git checkout -b feature/nova-funcionalidade`)
3. **Commit** suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. **Push** para a branch (`git push origin feature/nova-funcionalidade`)
5. **Abra** um Pull Request

## 📝 Roadmap

- [ ] Integração Mercado Pago real
- [ ] Sistema de cupons avançado
- [ ] Relatórios de vendas
- [ ] Notificações por email (SES)
- [ ] App mobile (React Native)
- [ ] Multi-tenancy

## 🐛 Troubleshooting

### **Problemas Comuns**

**Erro de migração:**
```bash
alembic stamp head
alembic upgrade head
```

**Porta em uso:**
```bash
lsof -ti:8000 | xargs kill -9
```

**Dependências:**
```bash
pip install --upgrade -r requirements.txt
```

## 📄 Licença

MIT License - veja arquivo [LICENSE](LICENSE) para detalhes.

## 🏆 Créditos

Desenvolvido com ❤️ usando:
- [FastAPI](https://fastapi.tiangolo.com/) - Framework web moderno
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM Python
- [Bootstrap](https://getbootstrap.com/) - Framework CSS
- [Font Awesome](https://fontawesome.com/) - Ícones
- [Google Fonts](https://fonts.google.com/) - Tipografia

---

**🦆 DuckTickets** - *A melhor plataforma para seus eventos!*