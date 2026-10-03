from app.core.config import Settings


def test_settings_defaults(monkeypatch):
    # Clear environment variables to test defaults
    monkeypatch.delenv("APP_NAME", raising=False)
    monkeypatch.delenv("API_PORT", raising=False)
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    
    settings = Settings()
    assert settings.APP_NAME == "RAGX API"
    assert settings.POSTGRES_DB == "ragx"

def test_settings_override(monkeypatch):
    monkeypatch.setenv("APP_NAME", "RAGX_TEST")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    
    settings = Settings()
    assert settings.APP_NAME == "RAGX_TEST"
    assert settings.POSTGRES_USER == "test_user"
