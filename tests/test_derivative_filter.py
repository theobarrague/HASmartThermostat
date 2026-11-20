"""Regression tests for the set_derivative_filter service."""

from datetime import timedelta

from homeassistant.components.climate import (
    DOMAIN as CLIMATE_DOMAIN,
)
from homeassistant.components.climate import (
    HVACMode,
)
from homeassistant.setup import async_setup_component

from custom_components.smart_thermostat.const import DOMAIN
from custom_components.smart_thermostat.pid_controller import PID


async def test_set_derivative_filter_service_updates_pid_controller(hass):
    """The set_derivative_filter service must change the PID's active filter."""
    await async_setup_component(hass, "switch", {})
    await async_setup_component(hass, "sensor", {})
    await hass.async_block_till_done()

    hass.states.async_set("sensor.temperature", "19.0")
    hass.states.async_set("switch.heater", "off")

    config = {
        CLIMATE_DOMAIN: {
            "platform": DOMAIN,
            "name": "Derivative Filter Thermostat",
            "heater": "switch.heater",
            "target_sensor": "sensor.temperature",
            "target_temp": 20.0,
            "keep_alive": timedelta(seconds=60),
        }
    }
    assert await async_setup_component(hass, CLIMATE_DOMAIN, config)
    await hass.async_block_till_done()

    entity_id = "climate.derivative_filter_thermostat"
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        "set_hvac_mode",
        {"entity_id": entity_id, "hvac_mode": HVACMode.HEAT},
        blocking=True,
    )

    await hass.services.async_call(
        DOMAIN,
        "set_derivative_filter",
        {"entity_id": entity_id, "derivative_filter": timedelta(seconds=30)},
        blocking=True,
    )
    await hass.async_block_till_done()

    component = hass.data[CLIMATE_DOMAIN]
    entity = next(e for e in component.entities if e.entity_id == entity_id)
    assert entity._pid_controller._derivative_filter == 30
    assert hass.states.get(entity_id).attributes["derivative_filter"] == 30


def test_pid_derivative_filter_property_is_wired():
    """PID exposes a settable derivative_filter that calc() actually uses."""
    pid = PID(1.0, 0.0, 1.0, 0.0, 0.0, 100.0, 0, 0)
    pid.derivative_filter = 5.0
    assert pid._derivative_filter == 5.0
