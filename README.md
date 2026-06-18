# Amora Slack Agent

Agente de IA integrado ao Slack, construído com **Bolt for Python** e **Pydantic AI**, utilizando o modelo **Google Gemini 2.5 Flash** como provider de linguagem.

O agente responde mensagens diretas, menções em canais, e aparece no painel de assistente nativo do Slack. Cada conversa mantém contexto dentro da thread. Quando disponível, conecta ao **Slack MCP Server** para executar ações no Slack (buscar mensagens, ler canais, criar canvases).

---

## Stack

| Componente | Tecnologia |
|---|---|
| Framework Slack | [Bolt for Python](https://docs.slack.dev/tools/bolt-python/) |
| Framework de agente | [Pydantic AI](https://ai.pydantic.dev/) |
| Modelo de linguagem | Google Gemini 2.5 Flash |
| Modo de conexão | Socket Mode (WebSocket — sem porta HTTP exposta) |
| Linguagem | Python 3.12 |

---

## Pré-requisitos

- Python 3.12+
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (para rodar via container)
- Conta no [Google AI Studio](https://aistudio.google.com/) para gerar a `GEMINI_API_KEY`
- Acesso ao workspace Slack com permissão para instalar apps

---

## 1. Configurar o Slack App

### 1.1 Criar o app

1. Acesse [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From a manifest**
2. Escolha o workspace de destino
3. Cole o conteúdo do arquivo [`manifest.json`](./manifest.json) na aba JSON e clique em **Next**
4. Revise a configuração e clique em **Create**
5. Clique em **Install to Workspace** → **Allow**

### 1.2 Coletar os tokens

**Bot Token (`SLACK_BOT_TOKEN`)**
- Menu lateral → **OAuth & Permissions**
- Copie o **Bot User OAuth Token** (`xoxb-...`)

**App Token (`SLACK_APP_TOKEN`)**
- Menu lateral → **Basic Information** → seção **App-Level Tokens**
- Clique em **Generate Token and Scopes**
- Adicione o scope `connections:write`
- Copie o token gerado (`xapp-...`)

### 1.3 Configurar variáveis de ambiente

Copie o arquivo de exemplo e preencha com seus tokens:

```bash
cp .env.sample .env
```

Conteúdo do `.env`:

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
GEMINI_API_KEY=AIza...
```

> Os valores **nunca devem ter aspas** (`"` ou `'`) em torno deles no arquivo `.env`.
> Exemplo correto: `SLACK_BOT_TOKEN=xoxb-abc123`
> Exemplo errado: `SLACK_BOT_TOKEN="xoxb-abc123"`

---

## 2. Rodar localmente (sem Docker)

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar (Windows)
.venv\Scripts\activate

# Ativar (macOS/Linux)
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Iniciar o agente
python app.py
```

O agente conecta ao Slack via WebSocket (Socket Mode). Quando o terminal mostrar `⚡️ Bolt app is running!`, o bot está ativo.

---

## 3. Rodar via Docker (recomendado para testes e produção)

Docker é a abordagem padrão para garantir que o ambiente seja idêntico entre desenvolvimento, testes e produção. O projeto já inclui `Dockerfile` e `.dockerignore` configurados.

### 3.1 Build da imagem

```bash
docker build -t amora-slack-agent .
```

Este comando lê o `Dockerfile`, instala as dependências e empacota o código em uma imagem. Na primeira execução demora alguns minutos; nas seguintes é muito mais rápido devido ao cache.

### 3.2 Rodar o container

```bash
docker run --env-file .env amora-slack-agent
```

O `--env-file .env` injeta os tokens no container em tempo de execução — eles nunca são gravados dentro da imagem.

Para rodar em segundo plano (sem bloquear o terminal):

```bash
docker run -d --env-file .env --name slack-agent amora-slack-agent
```

### 3.3 Comandos úteis

```bash
# Ver containers ativos
docker ps

# Acompanhar logs em tempo real
docker logs -f slack-agent

# Parar o container
docker stop slack-agent

# Remover o container (necessário antes de subir um novo com o mesmo nome)
docker rm slack-agent
```

### 3.4 Atualizar após modificar o código

Toda mudança no código exige rebuild da imagem. O fluxo é:

```bash
docker stop slack-agent
docker rm slack-agent
docker build -t amora-slack-agent .
docker run -d --env-file .env --name slack-agent amora-slack-agent
```

---

## 4. Estrutura do projeto

```
amora-slack-agent/
│
├── app.py                        # Entry point principal — Socket Mode
├── app_oauth.py                  # Entry point alternativo — HTTP Mode (OAuth)
├── manifest.json                 # Configuração do Slack App
├── requirements.txt              # Dependências Python
├── Dockerfile                    # Receita para gerar a imagem Docker
├── .dockerignore                 # Arquivos excluídos do build Docker
├── .env                          # Variáveis de ambiente (não commitar)
├── .env.sample                   # Template das variáveis de ambiente
│
├── agent/
│   ├── agent.py                  # Definição do agente Pydantic AI + Gemini
│   ├── deps.py                   # AgentDeps: contexto injetado em cada chamada
│   └── tools/
│       ├── __init__.py
│       └── emoji_reaction.py     # Ferramenta: adiciona reação emoji às mensagens
│
├── listeners/
│   ├── events/
│   │   ├── app_home_opened.py    # Evento: usuário abre a aba Home do bot
│   │   ├── app_mentioned.py      # Evento: bot é mencionado em um canal
│   │   ├── assistant_thread_started.py  # Evento: thread no painel de assistente
│   │   └── message.py            # Evento: mensagem direta ao bot
│   ├── actions/
│   │   └── feedback_buttons.py   # Ação: clique nos botões de feedback (👍/👎)
│   └── views/
│       ├── app_home_builder.py   # Constrói a view da aba Home (Block Kit)
│       └── feedback_builder.py   # Constrói os botões de feedback nas respostas
│
└── thread_context/
    └── store.py                  # Histórico de conversa em memória por thread
```

### Como os componentes se relacionam

```
Slack (usuário envia mensagem)
        ↓  WebSocket (Socket Mode)
    app.py
        ↓  register_listeners()
    listeners/events/message.py   (ou app_mentioned.py)
        ↓
    thread_context/store.py       → recupera histórico da thread
        ↓
    agent/agent.py                → chama Gemini via Pydantic AI
        ↓  tools disponíveis
    agent/tools/emoji_reaction.py → reage à mensagem no Slack
    Slack MCP Server (opcional)   → busca/escreve no Slack
        ↓
    resposta enviada de volta ao Slack via WebClient
        ↓
    thread_context/store.py       → salva histórico atualizado
```

**`agent/agent.py`** — Define o agente Pydantic AI com o model Gemini, o system prompt e as ferramentas disponíveis. A função `run_agent()` é chamada por cada listener de mensagem.

**`agent/deps.py`** — O dataclass `AgentDeps` carrega o contexto de cada requisição: cliente Slack, ID do usuário, canal, timestamps da thread, e o user token (quando disponível para o MCP Server).

**`thread_context/store.py`** — Store em memória com TTL de 24 horas e limite de 1000 conversas simultâneas. Permite que o agente se lembre do que foi dito anteriormente dentro de uma thread.

**`listeners/`** — Cada arquivo registra um handler para um evento específico do Slack. O Bolt framework roteia os eventos recebidos para o handler correto.

---

## 5. Deploy em produção (GCP ou AWS)

O `Dockerfile` presente neste projeto é a unidade de deploy. O processo em ambas as plataformas segue o mesmo padrão:

```
Código no GitHub → CI/CD faz o build da imagem → imagem enviada ao registry → serviço atualizado
```

### AWS — ECS com Fargate

1. Publicar a imagem no **ECR** (Elastic Container Registry)
2. Criar um serviço no **ECS Fargate** apontando para a imagem
3. Configurar as variáveis de ambiente no painel de **Task Definition** (não no código)
4. O Fargate gerencia escalabilidade e disponibilidade

```bash
# Exemplo de push para ECR
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
docker build -t amora-slack-agent .
docker tag amora-slack-agent:latest <account>.dkr.ecr.<region>.amazonaws.com/amora-slack-agent:latest
docker push <account>.dkr.ecr.<region>.amazonaws.com/amora-slack-agent:latest
```

### GCP — Cloud Run

1. Publicar a imagem no **Artifact Registry**
2. Criar um serviço no **Cloud Run** com `--min-instances=1` (necessário para manter a conexão WebSocket ativa)
3. Configurar as variáveis de ambiente como **Secrets** no Secret Manager

```bash
# Exemplo de push para Artifact Registry
gcloud auth configure-docker <region>-docker.pkg.dev
docker build -t amora-slack-agent .
docker tag amora-slack-agent:latest <region>-docker.pkg.dev/<project>/amora/amora-slack-agent:latest
docker push <region>-docker.pkg.dev/<project>/amora/amora-slack-agent:latest
```

> **Importante:** Em produção, as variáveis de ambiente (`SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, `GEMINI_API_KEY`) devem ser configuradas pelo painel do serviço (ECS Task Definition ou Cloud Run Secrets), nunca embutidas na imagem Docker ou no código.

---

## Interagindo com o bot no Slack

Após o agente estar rodando:

| Forma de interação | Como usar |
|---|---|
| **Mensagem direta** | Abra um DM com o bot e envie qualquer mensagem |
| **Menção em canal** | `/invite @nome-do-bot` no canal, depois `@nome-do-bot sua pergunta` |
| **App Home** | Clique no bot na barra lateral → aba **Home** |
| **Painel de assistente** | Clique em **Add Agent** no Slack, selecione o bot |

O bot responde sempre dentro de uma thread, mantendo o contexto da conversa durante 24 horas.

---

## Referências

- [Bolt for Python — Socket Mode](https://tools.slack.dev/bolt-python/concepts/socket-mode/)
- [Pydantic AI — Google Gemini](https://ai.pydantic.dev/models/google/)
- [Slack AI Agent Quickstart](https://docs.slack.dev/ai/agent-quickstart)
- [bolt-python-starter-agent](https://github.com/slack-samples/bolt-python-starter-agent/tree/main/pydantic-ai)
