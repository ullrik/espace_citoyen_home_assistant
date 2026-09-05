"""Button platform for Espace Citoyen."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import EspaceCitoyenConfigEntry
from .coordinator import EspaceCitoyenCoordinator


async def async_setup_entry(
    hass,
    entry: EspaceCitoyenConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the manual refresh button."""
    async_add_entities(
        [EspaceCitoyenRefreshButton(entry.runtime_data.coordinator)]
    )


class EspaceCitoyenRefreshButton(
    CoordinatorEntity[EspaceCitoyenCoordinator],
    ButtonEntity,
):
    """Button that forces a new scrape."""

    _attr_has_entity_name = True
    _attr_name = "Planning espace citoyen Coueron - rafraichir reservations"
    _attr_icon = "mdi:refresh"

    def __init__(
        self,
        coordinator: EspaceCitoyenCoordinator,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.entry.entry_id}_refresh"

    @property
    def available(self) -> bool:
        """The refresh action remains available after a transient failure."""
        return True

    async def async_press(self) -> None:
        """Force a refresh."""
        await self.coordinator.async_request_refresh()
