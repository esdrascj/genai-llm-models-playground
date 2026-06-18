import logging
import os

import httpx
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

from agent.deps import AgentDeps
from agent.tools import add_emoji_reaction
from mcp_server.server import SF_CLIENT_ID, SF_CLIENT_SECRET, SF_MCP_SERVER_URL, SF_TOKEN_URL


SYSTEM_PROMPT = """\
You are a friendly Slack assistant. You help people by answering questions, \
having conversations, and being generally useful in Slack.

## PERSONALITY
- Friendly, helpful, and approachable
- Lightly witty — a touch of humor when appropriate, but never forced
- Concise and clear — respect people's time
- Confident but honest when you don't know something

## RESPONSE GUIDELINES
- Keep responses to 3 sentences max — be punchy, scannable, and actionable
- End with a clear next step on its own line so it's easy to spot
- Use a bullet list only for multi-step instructions
- Use casual, conversational language
- Use emoji sparingly — at most one per message, and only to set tone

## FORMATTING RULES
- Use standard Markdown syntax: **bold**, _italic_, `code`, ```code blocks```, > blockquotes
- Use bullet points for multi-step instructions

## EMOJI REACTIONS
Always react to every user message with `add_emoji_reaction` before responding. \
Pick any Slack emoji that reflects the *topic* or *tone* of the message — be creative and specific \
(e.g. `dog` for dog topics, `books` for learning, `wave` for greetings). \
Vary your picks across a thread; don't repeat the same emoji.

## SLACK MCP SERVER
You may have access to the Slack MCP Server, which gives you powerful Slack tools \
beyond your built-in tools. Use them whenever they would help the user.

## SALESFORCE MCP SERVER
If you have access to the Salesforce MCP Server, you can use it to access Salesforce data and \
perform Salesforce actions. Use it whenever it would help the user.
Always use it for Salesforce-related questions and tasks.

Available capabilities:
- **Search**: Search messages and files across public channels, search for channels by name
- **Read**: Read channel message history, read thread replies, read canvas documents
- **Write**: Send messages, create draft messages, schedule messages for later
- **Canvases**: Create, read, and update Slack canvas documents

Use these tools when they can help answer a question or complete a task — for example, \
searching for relevant messages, checking a channel for context, or creating a canvas. \
Also use them when the user explicitly asks you to perform a Slack action.
"""

logger = logging.getLogger(__name__)

_cached_model: str | None = None


def get_model():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY não configurada no .env")
    return "google-gla:gemini-2.5-flash"


SLACK_MCP_URL = "https://mcp.slack.com/mcp"

agent = Agent(
    get_model(),
    deps_type=AgentDeps,
   system_prompt=SYSTEM_PROMPT,
    tools=[add_emoji_reaction],
)


def run_agent(text, deps, message_history=None):
    """Run the agent, optionally connecting to the Slack and Salesforce MCP servers."""
    toolsets = []

    if deps.user_token:
        logger.info("Slack MCP Server enabled (user_token present)")
        toolsets.append(
            MCPServerStreamableHTTP(
                SLACK_MCP_URL,
                headers={"Authorization": f"Bearer {deps.user_token}"},
            )
        )
    else:
        logger.info("Slack MCP Server disabled (no user_token)")

    if SF_CLIENT_ID and SF_CLIENT_SECRET:
        try:
            resp = httpx.post(
                SF_TOKEN_URL,
                data={
                    "grant_type": "client_credentials",
                    "client_id": SF_CLIENT_ID,
                    "client_secret": SF_CLIENT_SECRET,
                },
            )
            resp.raise_for_status()
            sf_token = resp.json()["access_token"]
            logger.info("Salesforce MCP Server enabled")
            toolsets.append(
                MCPServerStreamableHTTP(
                    SF_MCP_SERVER_URL,
                    headers={
                        "Authorization": f"Bearer {sf_token}",
                        "Content-Type": "application/json",
                    },
                )
            )
        except Exception:
            logger.warning("Salesforce MCP Server disabled (auth failed)", exc_info=True)
    else:
        logger.info("Salesforce MCP Server disabled (credentials not configured)")

    return agent.run_sync(
        text,
        model=get_model(),
        deps=deps,
        message_history=message_history,
        toolsets=toolsets,
    )
