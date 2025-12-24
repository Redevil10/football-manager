"""Unit tests for scoring logic"""

from core.config import (
    SCORE_RANGES,
)
from logic.scoring import (
    adjust_attributes_by_category_score,
    adjust_category_attributes_by_single_attr,
    calculate_category_score,
    calculate_gk_score,
    calculate_mental_score,
    calculate_overall_score,
    calculate_physical_score,
    calculate_technical_score,
    set_gk_score,
    set_mental_score,
    set_overall_score,
    set_physical_score,
    set_technical_score,
)


class TestCalculateCategoryScore:
    """Tests for calculate_category_score function"""

    def test_empty_attributes(self):
        """Test with empty attributes returns 0"""
        assert calculate_category_score({}) == 0

    def test_single_attribute(self):
        """Test with single attribute"""
        assert calculate_category_score({"passing": 10}) == 10.0

    def test_multiple_attributes(self):
        """Test with multiple attributes calculates average"""
        attrs = {"passing": 10, "dribbling": 20, "finishing": 15}
        expected = (10 + 20 + 15) / 3
        assert calculate_category_score(attrs) == expected

    def test_all_same_values(self):
        """Test with all same values"""
        attrs = {"attr1": 15, "attr2": 15, "attr3": 15}
        assert calculate_category_score(attrs) == 15.0


class TestCalculateTechnicalScore:
    """Tests for calculate_technical_score function"""

    def test_minimum_score(self):
        """Test minimum technical score (all attributes = 1)"""
        player = {
            "technical_attrs": {
                "corners": 1,
                "crossing": 1,
                "dribbling": 1,
                "finishing": 1,
                "first_touch": 1,
            }
        }
        score = calculate_technical_score(player)
        # Average = 1, scaled = 1 * 5 = 5
        assert score == 5

    def test_maximum_score(self):
        """Test maximum technical score (all attributes = 20)"""
        player = {
            "technical_attrs": {
                "corners": 20,
                "crossing": 20,
                "dribbling": 20,
                "finishing": 20,
                "first_touch": 20,
            }
        }
        score = calculate_technical_score(player)
        # Average = 20, scaled = 20 * 5 = 100
        assert score == 100

    def test_mid_range_score(self):
        """Test mid-range technical score"""
        player = {
            "technical_attrs": {
                "corners": 10,
                "crossing": 10,
                "dribbling": 10,
            }
        }
        score = calculate_technical_score(player)
        # Average = 10, scaled = 10 * 5 = 50
        assert score == 50

    def test_empty_technical_attrs(self):
        """Test with empty technical attributes"""
        player = {"technical_attrs": {}}
        score = calculate_technical_score(player)
        assert score == 0


class TestCalculateOverallScore:
    """Tests for calculate_overall_score function"""

    def test_minimum_overall_score(self):
        """Test minimum overall score (all attributes = 1)"""
        player = {
            "technical_attrs": {"passing": 1, "dribbling": 1},
            "mental_attrs": {"composure": 1, "decisions": 1},
            "physical_attrs": {"pace": 1, "strength": 1},
            "gk_attrs": {"handling": 1, "reflexes": 1},
        }
        score = calculate_overall_score(player)
        # All category scores = 5
        # weighted_sum = 5*3 + 5*2 + 5*3 + 5*2 = 50
        # overall = 50 / 5 = 10
        assert score == 10

    def test_maximum_overall_score(self):
        """Test maximum overall score (all attributes = 20)"""
        player = {
            "technical_attrs": {"passing": 20, "dribbling": 20},
            "mental_attrs": {"composure": 20, "decisions": 20},
            "physical_attrs": {"pace": 20, "strength": 20},
            "gk_attrs": {"handling": 20, "reflexes": 20},
        }
        score = calculate_overall_score(player)
        # All category scores = 100
        # weighted_sum = 100*3 + 100*2 + 100*3 + 100*2 = 1000
        # overall = 1000 / 5 = 200
        assert score == 200

    def test_mid_range_overall_score(self):
        """Test mid-range overall score"""
        player = {
            "technical_attrs": {"passing": 10, "dribbling": 10},
            "mental_attrs": {"composure": 10, "decisions": 10},
            "physical_attrs": {"pace": 10, "strength": 10},
            "gk_attrs": {"handling": 10, "reflexes": 10},
        }
        score = calculate_overall_score(player)
        # All category scores = 50
        # weighted_sum = 50*3 + 50*2 + 50*3 + 50*2 = 500
        # overall = 500 / 5 = 100
        assert score == 100

    def test_weighted_calculation(self):
        """Test that weights are applied correctly"""
        player = {
            "technical_attrs": {"passing": 20},  # score = 100
            "mental_attrs": {"composure": 10},  # score = 50
            "physical_attrs": {"pace": 10},  # score = 50
            "gk_attrs": {"handling": 10},  # score = 50
        }
        score = calculate_overall_score(player)
        # weighted_sum = 100*3 + 50*2 + 50*3 + 50*2 = 650
        # overall = 650 / 5 = 130
        assert score == 130

    def test_score_clamping(self):
        """Test that scores are clamped to valid range"""
        # Create a player that would exceed max if not clamped
        player = {
            "technical_attrs": {"passing": 25, "dribbling": 25},  # Would be > 100
            "mental_attrs": {"composure": 25, "decisions": 25},
            "physical_attrs": {"pace": 25, "strength": 25},
            "gk_attrs": {"handling": 25, "reflexes": 25},
        }
        score = calculate_overall_score(player)
        # Should be clamped to max of 200
        assert score <= SCORE_RANGES["overall"][1]
        assert score >= SCORE_RANGES["overall"][0]


class TestSetCategoryScores:
    """Tests for set_*_score functions that redistribute attributes"""

    def test_set_technical_score_min(self):
        """Test setting minimum technical score"""
        result = set_technical_score(SCORE_RANGES["technical"][0])
        # All attributes should be set to minimum (1)
        assert all(v == SCORE_RANGES["attribute"][0] for v in result.values())
        assert len(result) > 0

    def test_set_technical_score_max(self):
        """Test setting maximum technical score"""
        result = set_technical_score(SCORE_RANGES["technical"][1])
        # All attributes should be set to maximum (20)
        assert all(v == SCORE_RANGES["attribute"][1] for v in result.values())
        assert len(result) > 0

    def test_set_technical_score_mid(self):
        """Test setting mid-range technical score"""
        score = 50
        result = set_technical_score(score)
        # avg_value = 50 / 5 = 10, so all attributes should be 10
        assert all(v == 10 for v in result.values())

    def test_set_mental_score(self):
        """Test setting mental score"""
        result = set_mental_score(75)
        # avg_value = 75 / 5 = 15, so all attributes should be 15
        assert all(v == 15 for v in result.values())

    def test_set_physical_score(self):
        """Test setting physical score"""
        result = set_physical_score(60)
        # avg_value = 60 / 5 = 12, so all attributes should be 12
        assert all(v == 12 for v in result.values())

    def test_set_gk_score(self):
        """Test setting goalkeeper score"""
        result = set_gk_score(80)
        # avg_value = 80 / 5 = 16, so all attributes should be 16
        assert all(v == 16 for v in result.values())

    def test_set_score_clamping(self):
        """Test that scores are clamped to valid ranges"""
        # Try to set score below minimum
        result = set_technical_score(0)
        assert all(v >= SCORE_RANGES["attribute"][0] for v in result.values())

        # Try to set score above maximum
        result = set_technical_score(200)
        assert all(v <= SCORE_RANGES["attribute"][1] for v in result.values())


class TestSetOverallScore:
    """Tests for set_overall_score function"""

    def test_set_overall_score_min(self):
        """Test setting minimum overall score"""
        result = set_overall_score(SCORE_RANGES["overall"][0])
        # Should return all category attributes
        assert "technical" in result
        assert "mental" in result
        assert "physical" in result
        assert "gk" in result

    def test_set_overall_score_max(self):
        """Test setting maximum overall score"""
        result = set_overall_score(SCORE_RANGES["overall"][1])
        # Should return all category attributes
        assert "technical" in result
        assert "mental" in result
        assert "physical" in result
        assert "gk" in result

    def test_set_overall_score_mid(self):
        """Test setting mid-range overall score"""
        result = set_overall_score(100)
        # Verify structure
        assert "technical" in result
        assert "mental" in result
        assert "physical" in result
        assert "gk" in result

        # Verify that attributes are within valid range
        for category, attrs in result.items():
            for attr_value in attrs.values():
                assert (
                    SCORE_RANGES["attribute"][0]
                    <= attr_value
                    <= SCORE_RANGES["attribute"][1]
                )

    def test_set_overall_score_roundtrip(self):
        """Test that setting overall score and recalculating gives similar result"""
        target_score = 150
        result = set_overall_score(target_score)

        # Reconstruct player dict
        player = {
            "technical_attrs": result["technical"],
            "mental_attrs": result["mental"],
            "physical_attrs": result["physical"],
            "gk_attrs": result["gk"],
        }

        # Calculate overall score from the attributes
        calculated_score = calculate_overall_score(player)

        # Should be close to target (within reasonable rounding error)
        assert abs(calculated_score - target_score) <= 2


class TestAdjustAttributes:
    """Tests for attribute adjustment functions"""

    def test_adjust_attributes_by_category_score(self):
        """Test adjusting attributes to match target score"""
        category_attrs = {"passing": 10, "dribbling": 10, "finishing": 10}
        target_score = 75  # Should result in avg attribute of 15

        result = adjust_attributes_by_category_score(
            category_attrs, target_score, "technical"
        )

        # All attributes should be adjusted proportionally
        assert len(result) == len(category_attrs)
        # Average should be close to 15 (75 / 5)
        avg = sum(result.values()) / len(result)
        assert abs(avg - 15) < 1

    def test_adjust_attributes_empty(self):
        """Test adjusting empty attributes"""
        result = adjust_attributes_by_category_score({}, 50, "technical")
        assert result == {}

    def test_adjust_category_attributes_by_single_attr(self):
        """Test adjusting other attributes when one changes"""
        category_attrs = {"passing": 10, "dribbling": 10, "finishing": 10}
        changed_key = "passing"
        new_value = 15

        result = adjust_category_attributes_by_single_attr(
            category_attrs, changed_key, new_value
        )

        # Changed attribute should be new value
        assert result[changed_key] == new_value
        # Other attributes should be adjusted proportionally
        assert "dribbling" in result
        assert "finishing" in result

    def test_adjust_category_attributes_invalid_key(self):
        """Test adjusting with invalid key returns original"""
        category_attrs = {"passing": 10, "dribbling": 10}
        result = adjust_category_attributes_by_single_attr(
            category_attrs, "invalid_key", 15
        )
        assert result == category_attrs

    def test_adjust_category_attributes_zero_division(self):
        """Test adjusting when old value is zero"""
        category_attrs = {"passing": 0, "dribbling": 10}
        result = adjust_category_attributes_by_single_attr(category_attrs, "passing", 5)
        # Should handle zero division gracefully
        assert result["passing"] == 5
        assert "dribbling" in result


class TestCalculateMentalScore:
    """Tests for calculate_mental_score function"""

    def test_mental_score_calculation(self):
        """Test mental score calculation"""
        player = {
            "mental_attrs": {
                "composure": 15,
                "decisions": 15,
                "determination": 15,
            }
        }
        score = calculate_mental_score(player)
        # Average = 15, scaled = 15 * 5 = 75
        assert score == 75


class TestCalculatePhysicalScore:
    """Tests for calculate_physical_score function"""

    def test_physical_score_calculation(self):
        """Test physical score calculation"""
        player = {
            "physical_attrs": {
                "pace": 12,
                "strength": 12,
                "stamina": 12,
            }
        }
        score = calculate_physical_score(player)
        # Average = 12, scaled = 12 * 5 = 60
        assert score == 60


class TestCalculateGkScore:
    """Tests for calculate_gk_score function"""

    def test_gk_score_calculation(self):
        """Test goalkeeper score calculation"""
        player = {
            "gk_attrs": {
                "handling": 18,
                "reflexes": 18,
                "diving": 18,
            }
        }
        score = calculate_gk_score(player)
        # Average = 18, scaled = 18 * 5 = 90
        assert score == 90
