import pytest

@pytest.fixture(autouse=True)
def _stub_input(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt="": "")
