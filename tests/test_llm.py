from securecare.agents.llm import build_llm

FAKE_KEY = "sk-test-" + "A1b2C3d4" * 4


def test_openrouter_is_the_default_provider():
    assert build_llm(FAKE_KEY).openai_api_base == "https://openrouter.ai/api/v1"


def test_deepseek_direct_uses_deepseek_base_url():
    llm = build_llm(FAKE_KEY, "deepseek-chat", provider="deepseek")
    assert llm.openai_api_base == "https://api.deepseek.com"


def test_openai_uses_the_default_base_url():
    assert build_llm(FAKE_KEY, "gpt-4o-mini", provider="openai").openai_api_base is None
