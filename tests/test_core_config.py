"""Unit tests for core configuration constants"""

from core import config


class TestConfigConstants:
    """Tests for configuration constants"""

    def test_technical_attrs_defined(self):
        """Test that TECHNICAL_ATTRS is properly defined"""
        assert hasattr(config, "TECHNICAL_ATTRS")
        assert isinstance(config.TECHNICAL_ATTRS, dict)
        assert len(config.TECHNICAL_ATTRS) > 0

        # Check some expected attributes
        assert "passing" in config.TECHNICAL_ATTRS
        assert "dribbling" in config.TECHNICAL_ATTRS
        assert "finishing" in config.TECHNICAL_ATTRS

    def test_mental_attrs_defined(self):
        """Test that MENTAL_ATTRS is properly defined"""
        assert hasattr(config, "MENTAL_ATTRS")
        assert isinstance(config.MENTAL_ATTRS, dict)
        assert len(config.MENTAL_ATTRS) > 0

        # Check some expected attributes
        assert "composure" in config.MENTAL_ATTRS
        assert "decisions" in config.MENTAL_ATTRS
        assert "determination" in config.MENTAL_ATTRS

    def test_physical_attrs_defined(self):
        """Test that PHYSICAL_ATTRS is properly defined"""
        assert hasattr(config, "PHYSICAL_ATTRS")
        assert isinstance(config.PHYSICAL_ATTRS, dict)
        assert len(config.PHYSICAL_ATTRS) > 0

        # Check some expected attributes
        assert "pace" in config.PHYSICAL_ATTRS
        assert "strength" in config.PHYSICAL_ATTRS
        assert "stamina" in config.PHYSICAL_ATTRS

    def test_gk_attrs_defined(self):
        """Test that GK_ATTRS is properly defined"""
        assert hasattr(config, "GK_ATTRS")
        assert isinstance(config.GK_ATTRS, dict)
        assert len(config.GK_ATTRS) > 0

        # Check some expected attributes
        assert "handling" in config.GK_ATTRS
        assert "reflexes" in config.GK_ATTRS
        assert "diving" in config.GK_ATTRS

    def test_score_ranges_defined(self):
        """Test that SCORE_RANGES is properly defined"""
        assert hasattr(config, "SCORE_RANGES")
        assert isinstance(config.SCORE_RANGES, dict)

        # Check required ranges
        assert "overall" in config.SCORE_RANGES
        assert "technical" in config.SCORE_RANGES
        assert "mental" in config.SCORE_RANGES
        assert "physical" in config.SCORE_RANGES
        assert "gk" in config.SCORE_RANGES
        assert "attribute" in config.SCORE_RANGES

        # Check ranges are tuples of (min, max)
        for key, value in config.SCORE_RANGES.items():
            assert isinstance(value, tuple)
            assert len(value) == 2
            assert value[0] < value[1]  # min < max

    def test_overall_score_weights_defined(self):
        """Test that OVERALL_SCORE_WEIGHTS is properly defined"""
        assert hasattr(config, "OVERALL_SCORE_WEIGHTS")
        assert isinstance(config.OVERALL_SCORE_WEIGHTS, dict)

        # Check required weights
        assert "technical" in config.OVERALL_SCORE_WEIGHTS
        assert "mental" in config.OVERALL_SCORE_WEIGHTS
        assert "physical" in config.OVERALL_SCORE_WEIGHTS
        assert "gk" in config.OVERALL_SCORE_WEIGHTS

        # Check weights are positive
        for weight in config.OVERALL_SCORE_WEIGHTS.values():
            assert isinstance(weight, (int, float))
            assert weight > 0

    def test_overall_score_divisor_defined(self):
        """Test that OVERALL_SCORE_DIVISOR is properly defined"""
        assert hasattr(config, "OVERALL_SCORE_DIVISOR")
        assert isinstance(config.OVERALL_SCORE_DIVISOR, (int, float))
        assert config.OVERALL_SCORE_DIVISOR > 0

    def test_position_distribution_defined(self):
        """Test that POSITION_DISTRIBUTION is properly defined"""
        assert hasattr(config, "POSITION_DISTRIBUTION")
        assert isinstance(config.POSITION_DISTRIBUTION, dict)

        # Check required keys
        assert "defender_ratio" in config.POSITION_DISTRIBUTION
        assert "midfielder_ratio" in config.POSITION_DISTRIBUTION
        assert "goalkeeper_count" in config.POSITION_DISTRIBUTION
        assert "substitute_gk_ratio" in config.POSITION_DISTRIBUTION

        # Check ratios are valid (0-1 for ratios, positive for count)
        assert 0 <= config.POSITION_DISTRIBUTION["defender_ratio"] <= 1
        assert 0 <= config.POSITION_DISTRIBUTION["midfielder_ratio"] <= 1
        assert config.POSITION_DISTRIBUTION["goalkeeper_count"] > 0
        assert 0 <= config.POSITION_DISTRIBUTION["substitute_gk_ratio"] <= 1

    def test_user_roles_defined(self):
        """Test that USER_ROLES is properly defined"""
        assert hasattr(config, "USER_ROLES")
        assert isinstance(config.USER_ROLES, dict)

        assert "VIEWER" in config.USER_ROLES
        assert "MANAGER" in config.USER_ROLES

    def test_valid_roles_defined(self):
        """Test that VALID_ROLES is properly defined"""
        assert hasattr(config, "VALID_ROLES")
        assert isinstance(config.VALID_ROLES, list)
        assert len(config.VALID_ROLES) > 0

        # Check that all valid roles are in USER_ROLES values
        for role in config.VALID_ROLES:
            assert role in config.USER_ROLES.values()

    def test_db_path_defined(self):
        """Test that DB_PATH is properly defined"""
        assert hasattr(config, "DB_PATH")
        assert isinstance(config.DB_PATH, str)
        assert len(config.DB_PATH) > 0

    def test_allocation_max_iterations_defined(self):
        """Test that ALLOCATION_MAX_ITERATIONS is properly defined"""
        assert hasattr(config, "ALLOCATION_MAX_ITERATIONS")
        assert isinstance(config.ALLOCATION_MAX_ITERATIONS, int)
        assert config.ALLOCATION_MAX_ITERATIONS > 0

    def test_scale_constants_defined(self):
        """Test that scale constants are properly defined"""
        assert hasattr(config, "ATTRIBUTE_TO_CATEGORY_SCALE")
        assert hasattr(config, "CATEGORY_TO_ATTRIBUTE_SCALE")

        assert isinstance(config.ATTRIBUTE_TO_CATEGORY_SCALE, (int, float))
        assert isinstance(config.CATEGORY_TO_ATTRIBUTE_SCALE, (int, float))
        assert config.ATTRIBUTE_TO_CATEGORY_SCALE > 0
        assert config.CATEGORY_TO_ATTRIBUTE_SCALE > 0
