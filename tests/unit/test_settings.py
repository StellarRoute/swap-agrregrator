# Smoke test proving Settings loads with sane defaults without requiring a real .env file.
from config.settings import Settings


def test_settings_load_with_defaults():
    settings = Settings(_env_file=None)
    assert settings.environment == "development"
    assert settings.use_mock_drips_client is True
    assert settings.use_mock_signal_provider is True
    assert 0.0 <= settings.risk_score_threshold <= 1.0
