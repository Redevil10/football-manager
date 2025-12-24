"""Unit tests for authentication functions"""

from core.auth import hash_password, verify_password


class TestHashPassword:
    """Tests for hash_password function"""

    def test_hash_password_returns_tuple(self):
        """Test that hash_password returns a tuple of (hash, salt)"""
        password = "test_password"
        result = hash_password(password)
        assert isinstance(result, tuple)
        assert len(result) == 2
        hash_value, salt = result
        assert isinstance(hash_value, str)
        assert isinstance(salt, str)
        assert len(hash_value) > 0
        assert len(salt) > 0

    def test_hash_password_different_salts(self):
        """Test that same password produces different hashes with different salts"""
        password = "test_password"
        hash1, salt1 = hash_password(password)
        hash2, salt2 = hash_password(password)

        # Salts should be different
        assert salt1 != salt2
        # Hashes should be different (due to different salts)
        assert hash1 != hash2

    def test_hash_password_deterministic_with_salt(self):
        """Test that same password and salt produces same hash"""
        password = "test_password"
        # We can't directly control salt, but we can verify the hash algorithm works
        hash1, salt1 = hash_password(password)
        # Manually verify using the same salt
        import hashlib

        hash_obj = hashlib.sha256()
        hash_obj.update((password + salt1).encode("utf-8"))
        expected_hash = hash_obj.hexdigest()
        assert hash1 == expected_hash

    def test_hash_password_empty_string(self):
        """Test hashing empty password"""
        hash_value, salt = hash_password("")
        assert len(hash_value) > 0
        assert len(salt) > 0

    def test_hash_password_special_characters(self):
        """Test hashing password with special characters"""
        password = "p@ssw0rd!#$%"
        hash_value, salt = hash_password(password)
        assert len(hash_value) > 0
        assert len(salt) > 0


class TestVerifyPassword:
    """Tests for verify_password function"""

    def test_verify_password_correct(self):
        """Test verifying correct password"""
        password = "test_password"
        password_hash, salt = hash_password(password)
        assert verify_password(password, password_hash, salt) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password"""
        password = "test_password"
        wrong_password = "wrong_password"
        password_hash, salt = hash_password(password)
        assert verify_password(wrong_password, password_hash, salt) is False

    def test_verify_password_wrong_hash(self):
        """Test verifying with wrong hash"""
        password = "test_password"
        password_hash, salt = hash_password(password)
        wrong_hash = "wrong_hash_value"
        assert verify_password(password, wrong_hash, salt) is False

    def test_verify_password_wrong_salt(self):
        """Test verifying with wrong salt"""
        password = "test_password"
        password_hash, salt = hash_password(password)
        _, wrong_salt = hash_password("different_password")
        assert verify_password(password, password_hash, wrong_salt) is False

    def test_verify_password_empty_password(self):
        """Test verifying empty password"""
        password = ""
        password_hash, salt = hash_password(password)
        assert verify_password(password, password_hash, salt) is True
        assert verify_password("not_empty", password_hash, salt) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive"""
        password = "TestPassword"
        password_hash, salt = hash_password(password)
        assert verify_password("TestPassword", password_hash, salt) is True
        assert verify_password("testpassword", password_hash, salt) is False
        assert verify_password("TESTPASSWORD", password_hash, salt) is False

    def test_verify_password_unicode(self):
        """Test verifying password with unicode characters"""
        password = "pässwörd测试"
        password_hash, salt = hash_password(password)
        assert verify_password(password, password_hash, salt) is True
        assert verify_password("password", password_hash, salt) is False

    def test_verify_password_long_password(self):
        """Test verifying very long password"""
        password = "a" * 1000
        password_hash, salt = hash_password(password)
        assert verify_password(password, password_hash, salt) is True
        assert verify_password(password + "x", password_hash, salt) is False
