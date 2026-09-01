"""
Tests for the Smart Recommendation Engine.
Run: pytest tests/test_recommendations.py -v
"""
import pytest
import math

from app.services.recommendation_engine import (
    predict_wait_time,
    compute_congestion_score,
    compute_slot_score,
    congestion_label,
)


class TestWaitTimePrediction:
    def test_basic_calculation(self):
        """WaitTime = (queue × avg_mins × complexity) / counters"""
        result = predict_wait_time(10, 20.0, 1.0, 2)
        assert result == pytest.approx(100.0)

    def test_zero_queue_gives_zero_wait(self):
        assert predict_wait_time(0, 20.0, 1.0, 4) == 0.0

    def test_minimum_one_counter(self):
        """Active counters 0 should be treated as 1 to avoid division by zero."""
        result = predict_wait_time(5, 10.0, 1.0, 0)
        assert result > 0

    def test_higher_complexity_increases_wait(self):
        low = predict_wait_time(5, 20.0, 1.0, 2)
        high = predict_wait_time(5, 20.0, 1.5, 2)
        assert high > low

    def test_more_counters_reduces_wait(self):
        few = predict_wait_time(10, 20.0, 1.0, 2)
        many = predict_wait_time(10, 20.0, 1.0, 8)
        assert many < few


class TestCongestionScore:
    def test_score_in_range(self):
        score = compute_congestion_score(50, 100, 10, 100, 20.0)
        assert 0 <= score <= 100

    def test_full_capacity_high_score(self):
        score = compute_congestion_score(100, 100, 100, 100, 30.0)
        assert score >= 70

    def test_empty_centre_low_score(self):
        score = compute_congestion_score(0, 100, 0, 100, 20.0)
        assert score <= 20

    def test_score_never_exceeds_100(self):
        score = compute_congestion_score(10000, 100, 10000, 100, 120.0)
        assert score == 100.0


class TestCongestionLabel:
    def test_labels(self):
        assert congestion_label(10) == "Low"
        assert congestion_label(35) == "Moderate"
        assert congestion_label(60) == "High"
        assert congestion_label(80) == "Very High"


class TestSlotScore:
    def test_lower_is_better(self):
        good = compute_slot_score(0.2, 5.0, 15.0)
        bad = compute_slot_score(0.9, 60.0, 85.0)
        assert good < bad

    def test_perfect_slot_near_zero(self):
        score = compute_slot_score(0.0, 0.0, 0.0)
        assert score == pytest.approx(0.0)

    def test_score_bounded(self):
        score = compute_slot_score(1.0, 120.0, 100.0)
        assert 0 <= score <= 1.0
