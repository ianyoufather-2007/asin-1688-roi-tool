import math

import pytest

from asin_1688_roi.roi_config import RoiAssumptions, load_roi_assumptions


def test_default_assumptions_preserve_current_calculation_profile():
    assumptions, source = load_roi_assumptions(None)

    assert assumptions == RoiAssumptions(
        commission_rate=0.15,
        storage_usd=0.10,
        conversion_rate=0.10,
        ad_traffic_share=0.20,
        weight_low_cny_per_kg=8.50,
        weight_high_cny_per_kg=10.60,
        volume_low_cny_per_cbm=1360.0,
        volume_high_cny_per_cbm=1900.0,
    )
    assert source == "内置默认参数"


def test_assumptions_file_can_override_a_subset(tmp_path):
    config = tmp_path / "roi.json"
    config.write_text(
        '{"commission_rate": 0.12, "storage_usd": 0.25}',
        encoding="utf-8",
    )

    assumptions, source = load_roi_assumptions(config)

    assert assumptions.commission_rate == 0.12
    assert assumptions.storage_usd == 0.25
    assert assumptions.conversion_rate == 0.10
    assert source == str(config.resolve())


def test_assumptions_file_rejects_unknown_fields(tmp_path):
    config = tmp_path / "roi.json"
    config.write_text('{"made_up_fee": 0.20}', encoding="utf-8")

    with pytest.raises(ValueError, match="未知参数"):
        load_roi_assumptions(config)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("commission_rate", True),
        ("commission_rate", math.inf),
        ("commission_rate", 1.0),
        ("storage_usd", -0.01),
        ("conversion_rate", 0),
        ("conversion_rate", 1.01),
        ("ad_traffic_share", -0.01),
        ("ad_traffic_share", 1.01),
        ("weight_low_cny_per_kg", -1),
    ],
)
def test_assumptions_reject_invalid_business_values(field, value):
    values = RoiAssumptions().to_dict()
    values[field] = value

    with pytest.raises(ValueError, match=field):
        RoiAssumptions.from_mapping(values)
