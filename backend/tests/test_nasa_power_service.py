"""
Tests the NASA POWER response parsing logic against a realistic fake
payload shaped like NASA's documented JSON response. This verifies the
parsing/fallback-day-selection logic is correct even though we can't
reach power.larc.nasa.gov from this sandbox's restricted network — see
the honesty note in nasa_power_service.py.
"""

from unittest.mock import patch

import pytest

from app.services import nasa_power_service


def _fake_power_response(days: dict[str, float], fill_last_day=False):
    """Build a payload shaped like NASA POWER's real JSON response."""
    rainfall = dict(days)
    moisture = {d: 0.35 for d in days}
    temp = {d: 24.0 for d in days}
    if fill_last_day:
        last_day = sorted(days.keys())[-1]
        rainfall[last_day] = nasa_power_service.POWER_FILL_VALUE
        moisture[last_day] = nasa_power_service.POWER_FILL_VALUE
    return {
        "properties": {
            "parameter": {
                "PRECTOTCORR": rainfall,
                "GWETTOP": moisture,
                "T2M": temp,
            }
        }
    }


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_parses_latest_available_day():
    nasa_power_service._cache.clear()
    payload = _fake_power_response({"20240101": 12.5, "20240102": 40.2})
    with patch("app.services.nasa_power_service.requests.get", return_value=FakeResponse(payload)):
        result = nasa_power_service.fetch(10.0889, 77.0595)
    assert result.rainfall_mm_24h == 40.2
    assert result.soil_moisture_pct == 35.0
    assert result.temperature_c == 24.0
    assert result.source == "nasa_power"


def test_skips_fill_value_days():
    """NASA's -999 sentinel for the most recent (not-yet-processed) day
    should be skipped in favor of the latest real value."""
    nasa_power_service._cache.clear()
    payload = _fake_power_response({"20240101": 12.5, "20240102": 40.2}, fill_last_day=True)
    with patch("app.services.nasa_power_service.requests.get", return_value=FakeResponse(payload)):
        result = nasa_power_service.fetch(10.0889, 77.0595)
    assert result.rainfall_mm_24h == 12.5  # falls back to the earlier, valid day


def test_raises_when_no_usable_data():
    nasa_power_service._cache.clear()
    payload = _fake_power_response({"20240101": nasa_power_service.POWER_FILL_VALUE})
    with patch("app.services.nasa_power_service.requests.get", return_value=FakeResponse(payload)):
        with pytest.raises(ValueError):
            nasa_power_service.fetch(10.0889, 77.0595)


def test_caches_repeated_calls():
    """A second call for (nearly) the same point within the TTL should
    not hit the network again."""
    nasa_power_service._cache.clear()
    payload = _fake_power_response({"20240101": 5.0})
    with patch("app.services.nasa_power_service.requests.get", return_value=FakeResponse(payload)) as mock_get:
        nasa_power_service.fetch(10.09, 77.06)
        nasa_power_service.fetch(10.09, 77.06)
    assert mock_get.call_count == 1


def test_imd_service_falls_back_to_nasa_power():
    from app.services import imd_service

    nasa_power_service._cache.clear()
    payload = _fake_power_response({"20240101": 22.0})
    with patch("app.core.config.settings.USE_MOCK_IMD", False), patch(
        "app.services.nasa_power_service.requests.get", return_value=FakeResponse(payload)
    ):
        reading = imd_service.get_latest_rainfall(10.09, 77.06)
    assert reading.rainfall_mm_24h == 22.0
    assert reading.source == "nasa_power"


def test_imd_service_falls_back_to_mock_on_total_failure():
    from app.services import imd_service

    nasa_power_service._cache.clear()
    with patch("app.core.config.settings.USE_MOCK_IMD", False), patch(
        "app.services.nasa_power_service.requests.get", side_effect=ConnectionError("no network")
    ):
        reading = imd_service.get_latest_rainfall(10.09, 77.06)
    assert reading.source == "imd_mock"
    assert reading.rainfall_mm_24h >= 0


def test_satellite_service_shares_cache_with_imd_service():
    """Calling both services for the same point should only hit the
    network once, since they share nasa_power_service's cache."""
    from app.services import satellite_service

    nasa_power_service._cache.clear()
    payload = _fake_power_response({"20240101": 8.0})
    with patch("app.core.config.settings.USE_MOCK_IMD", False), patch(
        "app.services.nasa_power_service.requests.get", return_value=FakeResponse(payload)
    ) as mock_get:
        from app.services import imd_service

        imd_service.get_latest_rainfall(11.0, 76.5)
        satellite_service.get_latest_soil_moisture(11.0, 76.5)
    assert mock_get.call_count == 1
