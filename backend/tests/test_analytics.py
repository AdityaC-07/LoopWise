import datetime
import pytest
from app.seeds.demo_analytics import generate_demo_rollups


def test_demo_rollups_generation():
    rollups = generate_demo_rollups()
    assert len(rollups) == 90  # 30 days * 3 wards
    ward_b = [r for r in rollups if r["ward_id"] == "WD-DEMO-B"]
    assert len(ward_b) == 30


def test_ward_b_contamination_spike_narrative():
    rollups = generate_demo_rollups()
    ward_b = [r for r in rollups if r["ward_id"] == "WD-DEMO-B"]
    ward_b.sort(key=lambda x: x["date"])
    
    # Check days 14-18 have contamination rate spike (0.48)
    spike_days = ward_b[13:18]  # 0-indexed days 13 to 17 (days 14 to 18)
    for day in spike_days:
        assert day["contamination_rate"] >= 0.40


def test_ward_a_improving_trend_narrative():
    rollups = generate_demo_rollups()
    ward_a = [r for r in rollups if r["ward_id"] == "WD-DEMO-A"]
    ward_a.sort(key=lambda x: x["date"])
    
    first_day = ward_a[0]
    last_day = ward_a[-1]
    assert first_day["contamination_rate"] > last_day["contamination_rate"]


def test_ward_c_consistent_recycling_narrative():
    rollups = generate_demo_rollups()
    ward_c = [r for r in rollups if r["ward_id"] == "WD-DEMO-C"]
    for day in ward_c:
        assert day["recovery_potential_avg"] >= 0.80


def test_demo_rollups_contain_material_breakdown():
    rollups = generate_demo_rollups()
    for r in rollups:
        assert "plastic" in r["material_breakdown"]
        assert "paper" in r["material_breakdown"]
