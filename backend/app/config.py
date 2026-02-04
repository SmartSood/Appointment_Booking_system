from pydantic_settings import BaseSettings


def _async_db_url(url: str) -> str:
    """Use asyncpg driver for PostgreSQL (required by SQLAlchemy async)."""
    if url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/dobble"

    @property
    def async_database_url(self) -> str:
        return _async_db_url(self.database_url)  # use postgresql+asyncpg for async
    openai_api_key: str = ""
    # Gemini via Vertex AI (GCP)
    vertexai_project: str = ""
    vertexai_location: str = "us-central1"
    # Google Calendar: use (A) service account JSON or (B) OAuth 2.0 (no key file; use when org blocks service account keys)
    google_credentials_file: str = ""  # (A) Path to service account JSON
    google_calendar_id: str = "primary"  # "primary" or a calendar ID
    # (B) OAuth 2.0 – create "OAuth 2.0 Client ID" (Desktop or Web) in GCP Console, then run script to get refresh token
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""
    google_oauth_refresh_token: str = ""
    # Email: SendGrid (primary) or Gmail
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@example.com"  # Must be verified in SendGrid
    gmail_oauth_credentials: str = ""
    # Slack for doctor notifications
    slack_bot_token: str = ""
    slack_channel_id: str = ""
    # CORS
    frontend_origin: str = "http://localhost:3000"
    # MCP server (FastMCP)
    # FastMCP SSE endpoint (mounted at /mcp, SSE lives at /mcp/sse)
    mcp_server_url: str = "http://localhost:8000/mcp/sse"
    # JWT (auth)
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 days

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
