"""Sensor platform for Espace Citoyen."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EspaceCitoyenConfigEntry
from .const import ATTR_LAST_ERROR, ATTR_LAST_UPDATE, ATTR_PLANNING, DOMAIN
from .coordinator import EspaceCitoyenCoordinator


async def async_setup_entry(
    hass,
    entry: EspaceCitoyenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the planning sensor."""
    async_add_entities(
        [EspaceCitoyenPlanningSensor(entry.runtime_data.coordinator)]
    )


class EspaceCitoyenPlanningSensor(
    CoordinatorEntity[EspaceCitoyenCoordinator],
    SensorEntity,
):
    """Planning sensor exposing the two-week planning as an attribute."""

    _attr_has_entity_name = True
    _attr_name = "Planning espace citoyen Coueron"
    _attr_icon = "mdi:calendar-school"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(
        self,
        coordinator: EspaceCitoyenCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_planning"

    @property
    def available(self) -> bool:
        """Keep cached data visible when a refresh fails."""
        return bool(self.coordinator.data)

    @property
    def native_value(self) -> datetime | None:
        """Use the last successful refresh as sensor state."""
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get("last_update")
        if not isinstance(value, str):
            return None

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return planning and refresh metadata."""
        if not self.coordinator.data:
            return {
                ATTR_PLANNING: {},
                ATTR_LAST_UPDATE: None,
                ATTR_LAST_ERROR: self.coordinator.last_error,
            }

        return {
            ATTR_PLANNING: self.coordinator.data.get("planning", {}),
            ATTR_LAST_UPDATE: self.coordinator.data.get("last_update"),
            ATTR_LAST_ERROR: self.coordinator.last_error,
        }
