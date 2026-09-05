"""Espace Citoyen integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_change

from .api import EspaceCitoyenApi
from .const import (
    CONF_PASSWORD,
    CONF_USERNAME,
    PLATFORMS,
    UPDATE_HOUR,
    UPDATE_MINUTE,
    UPDATE_SECOND,
)
from .coordinator import EspaceCitoyenCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass
class EspaceCitoyenRuntimeData:
    """Runtime objects for a config entry."""

    coordinator: EspaceCitoyenCoordinator


type EspaceCitoyenConfigEntry = ConfigEntry[EspaceCitoyenRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: EspaceCitoyenConfigEntry,
) -> bool:
    """Set up Espace Citoyen from a config entry."""
    api = EspaceCitoyenApi(
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = EspaceCitoyenCoordinator(hass, entry, api)

    # Restore the latest successful scrape before attempting the network.
    await coordinator.async_load_cache()

    # On first install, or if today's 06:00 refresh has not produced data yet,
    # try immediately. A failure does not erase a previously cached planning.
    if coordinator.should_refresh_on_start(UPDATE_HOUR):
        await coordinator.async_refresh()

    entry.runtime_data = EspaceCitoyenRuntimeData(coordinator=coordinator)

    async def _scheduled_refresh(now: datetime) -> None:
        """Refresh every day at 06:00 local Home Assistant time."""
        _LOGGER.debug("Actualisation planifiée Espace Citoyen")
        await coordinator.async_request_refresh()

    remove_listener = async_track_time_change(
        hass,
        _scheduled_refresh,
        hour=UPDATE_HOUR,
        minute=UPDATE_MINUTE,
        second=UPDATE_SECOND,
    )
    entry.async_on_unload(remove_listener)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: EspaceCitoyenConfigEntry,
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
