"""Data coordinator for Espace Citoyen."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.util import dt as dt_util

from .api import (
    AuthenticationError,
    EspaceCitoyenApi,
    EspaceCitoyenError,
)
from .const import STORAGE_KEY_PREFIX, STORAGE_VERSION

_LOGGER = logging.getLogger(__name__)


class EspaceCitoyenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate planning refreshes and persist last good data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: EspaceCitoyenApi,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="Espace Citoyen",
            config_entry=entry,
            update_interval=None,
            always_update=True,
        )
        self.api = api
        self.entry = entry
        self.last_error: str | None = None
        self._store = Store[dict[str, Any]](
            hass,
            STORAGE_VERSION,
            f"{STORAGE_KEY_PREFIX}.{entry.entry_id}",
            serialize_in_event_loop=False,
        )

    async def async_load_cache(self) -> None:
        """Load the last successful result from HA storage."""
        cached = await self._store.async_load()
        if not cached:
            return

        planning = cached.get("planning")
        last_update = cached.get("last_update")
        if isinstance(planning, dict) and isinstance(last_update, str):
            self.async_set_updated_data(
                {
                    "planning": planning,
                    "last_update": last_update,
                }
            )

    def cache_is_from_today(self) -> bool:
        """Return True if stored data was refreshed today."""
        if not self.data:
            return False

        value = self.data.get("last_update")
        if not isinstance(value, str):
            return False

        try:
            last_update = datetime.fromisoformat(value)
        except ValueError:
            return False

        if last_update.tzinfo is None:
            last_update = last_update.replace(tzinfo=dt_util.DEFAULT_TIME_ZONE)

        return dt_util.as_local(last_update).date() == dt_util.now().date()

    def should_refresh_on_start(self, update_hour: int) -> bool:
        """Decide whether startup should trigger an immediate web request.

        - No cached data: refresh immediately so a newly configured integration
          gets useful data straight away.
        - Cache already refreshed today: do nothing.
        - Old cache before 06:00: keep it and wait for the scheduled refresh.
        - Old cache from 06:00 onward: refresh immediately, because HA may have
          been stopped at the normal refresh time.
        """
        if not self.data:
            return True

        if self.cache_is_from_today():
            return False

        return dt_util.now().hour >= update_hour

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch fresh data, retaining the previous data on error."""
        today = dt_util.now().date()

        try:
            planning = await self.hass.async_add_executor_job(
                self.api.get_planning,
                today,
            )
        except AuthenticationError as err:
            self.last_error = str(err)
            raise ConfigEntryAuthFailed(str(err)) from err
        except EspaceCitoyenError as err:
            self.last_error = str(err)
            raise UpdateFailed(str(err)) from err
        except Exception as err:
            self.last_error = str(err)
            _LOGGER.exception("Erreur inattendue pendant l'actualisation")
            raise UpdateFailed(str(err)) from err

        now_iso = dt_util.now().isoformat()
        result = {
            "planning": planning,
            "last_update": now_iso,
        }

        self.last_error = None
        await self._store.async_save(result)
        return result
