# Slack Agent — Bolt Python + Pydantic AI + Gemini

## Visão Geral

Agente de IA no Slack usando:
- **Bolt for Python** — framework oficial da Slack para integração
- **Pydantic AI** — framework de agente com suporte nativo a Gemini
- **Google Gemini** (`gemini-2.0-flash`) — modelo via `GOOGLE_API_KEY`

Referência base: [bolt-python-starter-agent/pydantic-ai](https://github.com/slack-samples/bolt-python-starter-agent/tree/main/pydantic-ai)

---

## Passo 1: Clonar o repositório base

```bash
git clone https://github.com/slack-samples/bolt-python-starter-agent
cd bolt-python-starter-agent/pydantic-ai
```

---

## Passo 2: Adaptar para Gemini

### 2.1 Atualizar `requirements.txt`

Substituir o provider de AI:

```diff
- pydantic-ai[openai,anthropic]
+ pydantic-ai[google]
  slack-bolt>=1.28.0
  slack-sdk==3.41.0
  slack-cli-hooks<1.0.0
  python-dotenv==1.2.2
```

### 2.2 Editar `agent/agent.py`

Substituir a função `get_model()` para usar Gemini:

```python
import os
from pydantic_ai import Agent
from agent.deps import AgentDeps

def get_model():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY não configurada no .env")
    return "google-gla:gemini-2.0-flash"

agent = Agent(
    get_model(),
    deps_type=AgentDeps,
    system_prompt=(
        "Você é um assistente amigável no Slack. "
        "Responda de forma concisa (máx. 3 frases). "
        "Use Markdown e emojis estrategicamente."
    ),
)
```

### 2.3 Atualizar `.env`

Copiar o sample e preencher:

```bash
cp .env.sample .env
```

Conteúdo do `.env`:

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
GOOGLE_API_KEY=AIza...
```

---

## Passo 3: Criar o Slack App

1. Acesse [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From manifest**
2. Cole o conteúdo do arquivo `manifest.json` do repositório
3. Instale o app no workspace: **OAuth & Permissions** → **Usar os dois botões para instalar no workspace**
4. Copie o `Bot User OAuth Token` (xoxb-...) → `.env` como `SLACK_BOT_TOKEN`
5. Em **Basic Information** → **App-Level Tokens** → gere um token com scope `connections:write` → `.env` como `SLACK_APP_TOKEN`

**Scopes necessários (já no manifest.json):**

| Tipo | Scopes |
|---|---|
| Bot | `assistant:write`, `channels:history`, `groups:history`, `im:history`, `chat:write`, `reactions:write`, `users:read`, `app_mentions:read` |
| User | `search:read`, `channels:read`, `groups:read`, `im:read`, `users:read` |

**Eventos a subscrever:**
- `app_home_opened`, `app_mentioned`, `assistant_thread_started`
- `message.channels`, `message.groups`, `message.im`

---

## Passo 4: Executar Localmente

```bash
# Criar e ativar ambiente virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Rodar em Socket Mode (não precisa de URL pública)
python app.py
```

**Testar:**
- Abra um DM com o bot no Slack e envie uma mensagem
- Mencione `@NomeDoBot` em um canal
- Acesse a aba App Home do bot

---

## Passo 5: Deploy em Produção

### Opção A: Socket Mode (apps internas — mais simples)

Funciona em qualquer servidor sem expor porta pública. O bot conecta ao Slack via WebSocket.

**Dockerfile:**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

**Serviços recomendados:**

| Serviço | Plano gratuito | Observação |
|---|---|---|
| [Railway](https://railway.app) | Sim (limitado) | Deploy simples via GitHub |
| [Render](https://render.com) | Sim (com sleep) | Adicionar health check para evitar sleep |
| [Fly.io](https://fly.io) | Sim | Boa opção para containers |
| GCP Cloud Run | Sim (free tier) | Configurar min-instances=1 para evitar cold start |
| AWS ECS / EC2 | Pago | Mais controle, mais complexo |

**Deploy no Railway (exemplo):**

```bash
# Fazer push para GitHub
git init && git add . && git commit -m "initial"
git push origin main

# No Railway: New Project → Deploy from GitHub
# Adicionar variáveis de ambiente no painel do Railway:
# SLACK_BOT_TOKEN, SLACK_APP_TOKEN, GOOGLE_API_KEY
```

### Opção B: HTTP Mode (apps distribuídas / Marketplace)

- Requer URL pública HTTPS
- Use `app_oauth.py` como entry point em vez de `app.py`
- Configure a **Request URL** no painel do Slack App
- Para dev local use `ngrok`: `ngrok http 3000`
- **Necessário** para publicar no Slack Marketplace

---

## Estrutura Final do Projeto

```
slack-agent/
├── app.py                    # Entry point (Socket Mode - dev/produção interna)
├── app_oauth.py              # Entry point (HTTP Mode - produção distribuída)
├── manifest.json             # Config do Slack App
├── requirements.txt          # Dependências (pydantic-ai[google])
├── .env                      # Tokens (não commitar!)
├── .env.sample               # Template de variáveis
├── agent/
│   ├── agent.py              # Agent pydantic-ai configurado com Gemini
│   ├── deps.py               # AgentDeps (client, user_id, channel_id, thread_ts)
│   └── tools/                # Ferramentas customizadas do agente
├── listeners/
│   ├── events/
│   │   ├── app_home_opened.py
│   │   ├── app_mentioned.py
│   │   └── message.py
│   ├── actions/
│   │   └── feedback_buttons.py
│   └── views/
│       ├── app_home_builder.py
│       └── feedback_builder.py
└── thread_context/
    └── store.py              # Histórico de conversa por thread (em memória)
```

---

## Resumo das Mudanças vs. Repositório Original

| Arquivo | O que muda |
|---|---|
| `requirements.txt` | `pydantic-ai[google]` no lugar de `[openai,anthropic]` |
| `agent/agent.py` | `get_model()` retorna `"google-gla:gemini-2.0-flash"` usando `GOOGLE_API_KEY` |
| `.env` | Adicionar `GOOGLE_API_KEY=AIza...` |

Todos os outros arquivos (`app.py`, `listeners/`, `thread_context/`, `deps.py`, `manifest.json`) são aproveitados **sem alteração**.

---

## Referências

- [Slack AI Agent Quickstart](https://docs.slack.dev/ai/agent-quickstart)
- [bolt-python-starter-agent (pydantic-ai)](https://github.com/slack-samples/bolt-python-starter-agent/tree/main/pydantic-ai)
- [Pydantic AI — Google Gemini provider](https://ai.pydantic.dev/models/google/)
- [Bolt for Python — Socket Mode](https://tools.slack.dev/bolt-python/concepts/socket-mode/)
- [Comparação HTTP vs Socket Mode](https://docs.slack.dev/apis/events-api/comparing-http-socket-mode/)
