"""Regression tests for the set_preset_temp service disable flags."""

from datetime import timedelta

from homeassistant.components.climate import (
    DOMAIN as CLIMATE_DOMAIN,
)
from homeassistant.components.climate import (
    HVACMode,
)
from homeassistant.setup import async_setup_component

from custom_components.smart_thermostat.const import DOMAIN


async def _setup_thermostat(hass, name: str = "Preset Test Thermostat") -> str:
    """Set up a YAML thermostat with one preset temp and return its entity_id."""
    await async_setup_component(hass, "switch", {})
    await async_setup_component(hass, "sensor", {})
    await hass.async_block_till_done()

    hass.states.async_set("sensor.temperature", "19.0")
    hass.states.async_set("switch.heater", "off")

    config = {
        CLIMATE_DOMAIN: {
            "platform": DOMAIN,
            "name": name,
            "heater": "switch.heater",
            "target_sensor": "sensor.temperature",
            "target_temp": 20.0,
            "away_temp": 16.0,
            "keep_alive": timedelta(seconds=60),
        }
    }
    assert await async_setup_component(hass, CLIMATE_DOMAIN, config)
    await hass.async_block_till_done()

    entity_id = f"climate.{name.lower().replace(' ', '_')}"
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {"entity_id": entity_id, "hvac_mode": HVACMode.HEAT},
        blocking=True,
    )
    return entity_id


async def test_set_preset_temp_disable_false_keeps_temperature(hass):
    """`*_temp_disable: false` must not reset the preset temperature to min_temp."""
    entity_id = await _setup_thermostat(hass)

    await hass.services.async_call(
        DOMAIN,
        "set_preset_temp",
        {"entity_id": entity_id, "away_temp_disable": False},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.attributes["away_temp"] == 16.0


async def test_set_preset_temp_value_and_disable_false_together(hass):
    """Setting a temp while disable=false must keep the new temp, not min_temp."""
    entity_id = await _setup_thermostat(hass)

    await hass.services.async_call(
        DOMAIN,
        "set_preset_temp",
        {"entity_id": entity_id, "away_temp": 18.0, "away_temp_disable": False},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.attributes["away_temp"] == 18.0


async def test_set_preset_temp_disable_true_removes_preset(hass):
    """`*_temp_disable: true` must clear the preset temperature."""
    entity_id = await _setup_thermostat(hass)

    await hass.services.async_call(
        DOMAIN,
        "set_preset_temp",
        {"entity_id": entity_id, "away_temp_disable": True},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.attributes["away_temp"] is None
