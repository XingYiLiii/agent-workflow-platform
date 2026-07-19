from app.core.config import get_settings


def test_default_settings() -> None:
    settings = get_settings()

    assert settings.app_name == "Agent Workflow Platform"
    assert settings.environment == "development"
