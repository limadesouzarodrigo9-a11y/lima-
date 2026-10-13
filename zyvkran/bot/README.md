# 🤖 Bot Discord Profissional

Bot completo para Discord com sistemas de proteção, loja digital, tickets, pagamentos via Pix e muito mais.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Recursos](#-recursos)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração do Discord](#-configuração-do-discord)
- [Configuração do Bot](#-configuração-do-bot)
- [Como Usar](#-como-usar)
- [Comandos](#-comandos)
- [Deploy](#-deploy)
- [Estrutura do Projeto](#-estrutura-do-projeto)

## 🎯 Visão Geral

Este bot é uma solução completa para administradores de servidores Discord, oferecendo:

- ✅ Configuração automática de servidores
- 🛡️ Sistema de proteção em 3 níveis (Básico, Difícil, Impossível)
- 🛒 Loja digital com produtos e variantes
- 💰 Sistema de pagamentos via Pix
- 🎫 Sistema de tickets completo
- 🔐 Verificação de usuários
- 📝 Sistema de logs detalhados
- 🤖 Anti-Spam, Anti-Raid, Anti-Bot, Anti-Nuke
- 📊 Painel administrativo
- 💾 Banco de dados persistente

## 🚀 Recursos

### Sistema de Proteção
- **Modo Verde (Básico)**: Anti-spam básico, detecção de links, rate limit
- **Modo Laranja (Difícil)**: Anti-spam avançado, Anti-raid, filtro de palavras, moderação automática
- **Modo Vermelho (Impossível)**: Anti-bot, Anti-nuke, verification gate, proteção contra exclusões massivas

### Sistema de Loja
- Cadastro de produtos com variantes
- Controle de estoque
- Sistema de pedidos
- Pagamento via Pix
- Confirmação por administradores
- Canais privados de compra

### Sistema de Tickets
- Múltiplas categorias (Suporte, Compras, Denúncia, Ajuda, Pós-venda)
- Canais privados
- Transcript automático
- Gerenciamento completo

### Sistema Anti-Nuke
- Monitoramento de exclusão massiva de canais
- Monitoramento de criação massiva de canais
- Monitoramento de exclusão massiva de cargos
- Monitoramento de banimentos em massa
- Alertas e ações automáticas

## 📦 Pré-requisitos

- Python 3.11 ou superior
- Conta no Discord
- Servidor Discord com permissões de administrador

## 🔧 Instalação

### 1. Clone ou baixe o projeto

```bash
cd bot
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv
```

### 3. Ative o ambiente virtual

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instale as dependências

```bash
pip install -r requirements.txt
```

## 🎮 Configuração do Discord

### 1. Criar um Bot no Discord Developer Portal

1. Acesse [Discord Developer Portal](https://discord.com/developers/applications)
2. Clique em **"New Application"**
3. Dê um nome ao seu bot
4. Vá para a aba **"Bot"** no menu lateral
5. Clique em **"Add Bot"**
6. Copie o **TOKEN** do bot (você precisará dele depois)

### 2. Configurar Intents

Na aba **"Bot"**, habilite os seguintes **Privileged Gateway Intents**:

- ✅ **PRESENCE INTENT**
- ✅ **SERVER MEMBERS INTENT**
- ✅ **MESSAGE CONTENT INTENT**

**IMPORTANTE**: Sem esses intents, o bot não funcionará corretamente!

### 3. Configurar Permissões

Na aba **"OAuth2"** → **"URL Generator"**:

1. Marque os scopes:
   - ✅ `bot`
   - ✅ `applications.commands`

2. Marque as permissões do bot:
   - ✅ **Administrator** (para funcionamento completo)
   
   Ou selecione individualmente:
   - Manage Server
   - Manage Roles
   - Manage Channels
   - Kick Members
   - Ban Members
   - Manage Messages
   - Read Messages/View Channels
   - Send Messages
   - Embed Links
   - Attach Files
   - Read Message History
   - Mention Everyone
   - Use Slash Commands

3. Copie a URL gerada e cole no navegador para adicionar o bot ao seu servidor

### 4. Obter ID do Proprietário

1. No Discord, vá em **Configurações** → **Avançado**
2. Ative o **Modo Desenvolvedor**
3. Clique com o botão direito no seu nome
4. Selecione **"Copiar ID"**

## ⚙️ Configuração do Bot

### 1. Configurar Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas informações:

```env
DISCORD_TOKEN=seu_token_aqui
DATABASE_URL=sqlite+aiosqlite:///./bot.db
OWNER_ID=seu_id_aqui
```

**IMPORTANTE**: 
- Substitua `seu_token_aqui` pelo token do bot copiado do Discord Developer Portal
- Substitua `seu_id_aqui` pelo seu ID de usuário do Discord
- **NUNCA** compartilhe seu token com ninguém!

### 2. Configurar Banco de Dados

O bot usa **SQLite** por padrão, que é criado automaticamente na primeira execução.

Para usar **PostgreSQL** (recomendado para produção):

1. Instale o PostgreSQL
2. Crie um banco de dados
3. Atualize o `DATABASE_URL` no `.env`:

```env
DATABASE_URL=postgresql+asyncpg://usuario:senha@localhost:5432/nome_do_banco
```

4. Instale o driver PostgreSQL:

```bash
pip install asyncpg
```

## 🎯 Como Usar

### 1. Iniciar o Bot

```bash
python main.py
```

Você verá uma mensagem como:
```
INFO:bot:Logged in as NomeDoBot#1234 (ID: 123456789)
INFO:bot:------
INFO:bot:Synced 5 command(s)
```

### 2. Configurar o Servidor

1. No Discord, digite: `/despertar`
2. O bot enviará um painel com duas opções:

#### Opção A: 🚀 Iniciar (Configuração Manual)
- Clique em **"🚀 Iniciar"**
- Preencha o modal com o nome do servidor
- Selecione a moeda (BRL ou USD)
- Escolha o nível de proteção (Verde, Laranja ou Vermelho)

#### Opção B: ⚠️ Servidor Pré-Pronto (Configuração Automática)
- Clique em **"⚠️ Servidor Pré-Pronto"**
- Preencha sua chave Pix
- O bot criará automaticamente toda a estrutura do servidor

### 3. Usar o Painel Administrativo

Digite: `/painel`

O painel oferece acesso a:
- 🛡️ Proteção
- 🛒 Loja
- 🎫 Tickets
- 👥 Cargos
- 📋 Logs
- 🔐 Verificação
- 💾 Backup
- 📊 Estatísticas
- ⚙️ Configurações

## 📝 Comandos

### Comandos Principais

| Comando | Descrição | Permissão |
|---------|-----------|-----------|
| `/despertar` | Inicia a configuração do servidor | Proprietário |
| `/painel` | Abre o painel administrativo | Administrador |
| `/produto` | Gerencia produtos da loja | Administrador |
| `/ticket` | Configura o sistema de tickets | Administrador |

### Exemplos de Uso

#### Criar um Produto
```
/produto action:criar nome:"Produto X" preco:29.90 estoque:100
```

#### Listar Produtos
```
/produto action:listar
```

#### Configurar Tickets
```
/ticket
```

## 🌐 Deploy

### Opção 1: Executar Localmente

Mantenha o terminal aberto com o bot rodando:
```bash
python main.py
```

### Opção 2: Usar PM2 (Recomendado)

1. Instale o PM2:
```bash
npm install -g pm2
```

2. Crie um arquivo `ecosystem.config.js`:
```javascript
module.exports = {
  apps: [{
    name: "discord-bot",
    script: "main.py",
    interpreter: "python",
    interpreter_args: "-u",
    watch: false,
    max_memory_restart: "1G"
  }]
}
```

3. Inicie o bot:
```bash
pm2 start ecosystem.config.js
```

4. Configure para iniciar automaticamente:
```bash
pm2 startup
pm2 save
```

### Opção 3: Usar Docker

1. Crie um `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

2. Construa a imagem:
```bash
docker build -t discord-bot .
```

3. Execute o container:
```bash
docker run -d --name discord-bot --env-file .env discord-bot
```

### Opção 4: Usar Serviços Cloud

- **Heroku**: Deploy direto do GitHub
- **Railway**: Deploy automático
- **Render**: Deploy gratuito
- **VPS**: DigitalOcean, AWS, Google Cloud

## 📁 Estrutura do Projeto

```
bot/
├── main.py                 # Ponto de entrada do bot
├── config.py               # Configurações globais
├── .env                    # Variáveis de ambiente (não commitar!)
├── .env.example            # Template de variáveis
├── requirements.txt        # Dependências
│
├── cogs/                   # Módulos do bot
│   ├── despertar.py        # Comando /despertar
│   ├── setup.py            # Configuração do servidor
│   ├── protection.py       # Anti-Spam, Anti-Raid, Anti-Bot
│   ├── anti_nuke.py        # Proteção Anti-Nuke
│   ├── shop.py             # Sistema de loja
│   ├── tickets.py          # Sistema de tickets
│   ├── verification.py     # Verificação de usuários
│   ├── logs.py             # Sistema de logs
│   └── admin.py            # Painel administrativo
│
├── database/               # Camada de dados
│   ├── database.py         # Conexão e sessão
│   ├── models.py           # Modelos SQLAlchemy
│   └── repositories/       # Repositórios (CRUD)
│
├── views/                  # Componentes de UI
│   └── setup_views.py      # Views de configuração
│
├── utils/                  # Utilitários
│   └── embeds.py           # Factory de embeds
│
└── messages/               # Mensagens centralizadas
    └── messages.py         # Textos e embeds
```

## 🔒 Segurança

- ✅ Tokens armazenados em `.env` (nunca no código)
- ✅ Validação de permissões em todos os comandos
- ✅ Proteção contra spam e raid
- ✅ Sistema Anti-Nuke
- ✅ Logs de todas as ações administrativas
- ✅ Confirmação de pagamentos apenas por staff
- ✅ Canais privados para compras

## 🐛 Solução de Problemas

### Bot não responde
- Verifique se o token está correto no `.env`
- Verifique se os intents estão habilitados no Discord Developer Portal
- Verifique se o bot está online no servidor

### Comandos não aparecem
- Aguarde alguns minutos para a sincronização
- Verifique se o bot tem a permissão `Use Application Commands`

### Erro de permissões
- Verifique se o bot tem permissão de Administrador
- Verifique a hierarquia de cargos (bot deve estar acima dos cargos que gerencia)

### Banco de dados não cria
- Verifique se tem permissão de escrita no diretório
- Para PostgreSQL, verifique a string de conexão

## 📊 Tecnologias Utilizadas

- **Python 3.11+**
- **discord.py** - Biblioteca oficial do Discord
- **SQLAlchemy** - ORM para banco de dados
- **aiosqlite** - Driver SQLite assíncrono
- **python-dotenv** - Gerenciamento de variáveis de ambiente

## 🤝 Contribuindo

Este é um projeto open-source. Sinta-se livre para:
- Reportar bugs
- Sugerir melhorias
- Enviar pull requests

## 📄 Licença

Este projeto é gratuito para uso pessoal e comercial.

## 📞 Suporte

Para dúvidas e suporte:
- Abra uma issue no GitHub
- Entre em contato pelo Discord

## ⚠️ Avisos Importantes

1. **Nunca compartilhe seu token**
2. **Faça backup regular do banco de dados**
3. **Teste o bot em um servidor de teste antes de usar em produção**
4. **Respeite os Termos de Serviço do Discord**
5. **Mantenha o bot atualizado**

## 🎉 Agradecimentos

Obrigado por usar este bot! Esperamos que ele ajude a tornar seu servidor Discord mais seguro e organizado.

---

**Desenvolvido com ❤️ para a comunidade Discord**
