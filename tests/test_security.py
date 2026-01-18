"""Unit tests for security functions (CSRF and XSS protection)"""

from core.auth import (
    escape_js_string,
    generate_csrf_token,
    get_csrf_token,
    validate_csrf_token,
)


class TestGenerateCsrfToken:
    """Tests for generate_csrf_token function"""

    def test_generate_csrf_token_returns_string(self):
        """Test that generate_csrf_token returns a non-empty string"""
        sess = {}
        token = generate_csrf_token(sess)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_csrf_token_stores_in_session(self):
        """Test that generate_csrf_token stores token in session"""
        sess = {}
        token = generate_csrf_token(sess)
        assert "csrf_token" in sess
        assert sess["csrf_token"] == token

    def test_generate_csrf_token_unique_tokens(self):
        """Test that generate_csrf_token produces unique tokens"""
        sess1 = {}
        sess2 = {}
        token1 = generate_csrf_token(sess1)
        token2 = generate_csrf_token(sess2)
        assert token1 != token2

    def test_generate_csrf_token_overwrites_existing(self):
        """Test that generate_csrf_token overwrites existing token"""
        sess = {"csrf_token": "old_token"}
        token = generate_csrf_token(sess)
        assert sess["csrf_token"] == token
        assert token != "old_token"

    def test_generate_csrf_token_none_session(self):
        """Test that generate_csrf_token handles None session"""
        token = generate_csrf_token(None)
        assert token == ""

    def test_generate_csrf_token_sufficient_length(self):
        """Test that token has sufficient length for security"""
        sess = {}
        token = generate_csrf_token(sess)
        # token_urlsafe(32) produces ~43 characters
        assert len(token) >= 32


class TestGetCsrfToken:
    """Tests for get_csrf_token function"""

    def test_get_csrf_token_returns_existing(self):
        """Test that get_csrf_token returns existing token"""
        sess = {"csrf_token": "existing_token"}
        token = get_csrf_token(sess)
        assert token == "existing_token"

    def test_get_csrf_token_generates_if_missing(self):
        """Test that get_csrf_token generates token if missing"""
        sess = {}
        token = get_csrf_token(sess)
        assert len(token) > 0
        assert "csrf_token" in sess

    def test_get_csrf_token_none_session(self):
        """Test that get_csrf_token handles None session"""
        token = get_csrf_token(None)
        assert token == ""

    def test_get_csrf_token_consistent(self):
        """Test that get_csrf_token returns same token on repeated calls"""
        sess = {}
        token1 = get_csrf_token(sess)
        token2 = get_csrf_token(sess)
        assert token1 == token2


class TestValidateCsrfToken:
    """Tests for validate_csrf_token function"""

    def test_validate_csrf_token_valid(self):
        """Test that validate_csrf_token returns True for valid token"""
        sess = {}
        token = generate_csrf_token(sess)
        assert validate_csrf_token(sess, token) is True

    def test_validate_csrf_token_invalid(self):
        """Test that validate_csrf_token returns False for invalid token"""
        sess = {}
        generate_csrf_token(sess)
        assert validate_csrf_token(sess, "wrong_token") is False

    def test_validate_csrf_token_none_session(self):
        """Test that validate_csrf_token handles None session"""
        assert validate_csrf_token(None, "any_token") is False

    def test_validate_csrf_token_empty_token(self):
        """Test that validate_csrf_token rejects empty token"""
        sess = {}
        generate_csrf_token(sess)
        assert validate_csrf_token(sess, "") is False

    def test_validate_csrf_token_none_token(self):
        """Test that validate_csrf_token rejects None token"""
        sess = {}
        generate_csrf_token(sess)
        assert validate_csrf_token(sess, None) is False

    def test_validate_csrf_token_no_stored_token(self):
        """Test that validate_csrf_token returns False if no token stored"""
        sess = {}
        assert validate_csrf_token(sess, "any_token") is False

    def test_validate_csrf_token_timing_attack_resistant(self):
        """Test that validation uses constant-time comparison"""
        sess = {}
        token = generate_csrf_token(sess)
        # These should all take roughly the same time (constant-time comparison)
        # We can't easily test timing, but we verify the function works correctly
        assert validate_csrf_token(sess, token) is True
        assert validate_csrf_token(sess, "x" * len(token)) is False
        assert validate_csrf_token(sess, token[:-1]) is False


class TestEscapeJsString:
    """Tests for escape_js_string function"""

    def test_escape_js_string_empty(self):
        """Test that escape_js_string handles empty string"""
        assert escape_js_string("") == ""

    def test_escape_js_string_none(self):
        """Test that escape_js_string handles None"""
        assert escape_js_string(None) == ""

    def test_escape_js_string_simple(self):
        """Test that escape_js_string passes through simple strings"""
        result = escape_js_string("hello")
        assert "hello" in result

    def test_escape_js_string_single_quote(self):
        """Test that escape_js_string escapes single quotes"""
        result = escape_js_string("it's")
        # html.escape converts ' to &#x27; which is safe in JS
        assert "'" not in result

    def test_escape_js_string_double_quote(self):
        """Test that escape_js_string escapes double quotes"""
        result = escape_js_string('say "hello"')
        # html.escape converts " to &quot; which is safe in JS
        assert '"' not in result

    def test_escape_js_string_backslash(self):
        """Test that escape_js_string escapes backslashes"""
        result = escape_js_string("path\\to\\file")
        assert "\\\\" in result

    def test_escape_js_string_newline(self):
        """Test that escape_js_string escapes newlines"""
        result = escape_js_string("line1\nline2")
        assert "\\n" in result

    def test_escape_js_string_carriage_return(self):
        """Test that escape_js_string escapes carriage returns"""
        result = escape_js_string("line1\rline2")
        assert "\\r" in result

    def test_escape_js_string_html_tags(self):
        """Test that escape_js_string escapes HTML tags"""
        result = escape_js_string("<script>alert('xss')</script>")
        assert "<script>" not in result
        # html.escape converts < to &lt; and > to &gt; which is safe
        assert "<" not in result
        assert ">" not in result

    def test_escape_js_string_html_entities(self):
        """Test that escape_js_string escapes HTML entities"""
        result = escape_js_string("a & b")
        assert "&amp;" in result

    def test_escape_js_string_xss_attack_vector(self):
        """Test that escape_js_string prevents XSS attack vectors"""
        # Test common XSS payloads
        payloads = [
            "');alert('xss');//",
            '";alert("xss");//',
            "</script><script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
        ]
        for payload in payloads:
            result = escape_js_string(payload)
            # Verify the result doesn't contain unescaped dangerous characters
            assert "'" not in result or "\\'" in result
            assert '"' not in result or '\\"' in result
            assert "<" not in result

    def test_escape_js_string_unicode(self):
        """Test that escape_js_string handles unicode characters"""
        result = escape_js_string("用户名")
        # Unicode should be preserved (HTML escape handles it)
        assert len(result) > 0

    def test_escape_js_string_in_js_context(self):
        """Test that escaped string is safe for JavaScript string context"""
        username = "O'Brien</script><script>alert('xss')"
        escaped = escape_js_string(username)
        # The escaped string should be safe to use in:
        # confirm('Delete user {escaped}?')
        # It should not break out of the string or inject scripts
        assert "'" not in escaped or "\\'" in escaped
        assert "<" not in escaped


class TestCsrfWorkflow:
    """Integration tests for CSRF protection workflow"""

    def test_full_csrf_workflow(self):
        """Test complete CSRF token generation and validation workflow"""
        # Simulate login - generate token
        sess = {}
        token = generate_csrf_token(sess)

        # Simulate form submission - validate token
        assert validate_csrf_token(sess, token) is True

        # Token should still be valid for subsequent requests
        assert validate_csrf_token(sess, token) is True

    def test_csrf_token_after_session_clear(self):
        """Test that CSRF validation fails after session is cleared"""
        sess = {}
        token = generate_csrf_token(sess)

        # Simulate logout - clear session
        sess.clear()

        # Token should no longer be valid
        assert validate_csrf_token(sess, token) is False

    def test_csrf_token_regeneration(self):
        """Test that new token invalidates old token"""
        sess = {}
        old_token = generate_csrf_token(sess)

        # Generate new token (e.g., after login)
        new_token = generate_csrf_token(sess)

        # Old token should no longer be valid
        assert validate_csrf_token(sess, old_token) is False
        # New token should be valid
        assert validate_csrf_token(sess, new_token) is True
