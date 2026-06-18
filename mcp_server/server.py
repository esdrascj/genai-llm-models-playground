import os

from dotenv import load_dotenv

load_dotenv()

SF_MCP_SERVER_URL = os.getenv(
    "SF_MCP_SERVER_URL",
    "https://api.salesforce.com/platform/mcp/v1/sandbox/platform/sobject-all",
)
SF_TOKEN_URL = os.getenv(
    "SF_TOKEN_URL",
    "https://resultadosdigitais--devhomolog.sandbox.my.salesforce.com/services/oauth2/token",
)
SF_CLIENT_ID = os.getenv("SF_CLIENT_ID", "")
SF_CLIENT_SECRET = os.getenv("SF_CLIENT_SECRET", "")
SF_GRANT_TYPE = os.getenv("SF_GRANT_TYPE", "")
