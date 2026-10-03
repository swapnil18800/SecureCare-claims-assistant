from securecare.formatting import format_inr
from securecare.security import looks_like_api_key, redact_secrets


def test_key_shape_check():
    assert looks_like_api_key("sk-" + "a" * 30)
    assert not looks_like_api_key("hello") and not looks_like_api_key("")


def test_redaction():
    assert redact_secrets("bad key sk-proj-abcdef123456789 used") == "bad key sk-*** used"


def test_inr_format():
    assert format_inr(127500) == "₹1,27,500"
    assert format_inr(999) == "₹999"
    assert format_inr(10000000) == "₹1,00,00,000"
