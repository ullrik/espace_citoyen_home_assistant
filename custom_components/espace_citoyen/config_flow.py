"""Config flow for Espace Citoyen."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.helpers import selector

from .api import (
    AuthenticationError,
    EspaceCitoyenApi,
    EspaceCitoyenError,
)
from .const import CONF_PASSWORD, CONF_USERNAME, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def _validate_credentials(
    hass: HomeAssistant,
    username: str,
    password: str,
) -> None:
    api = EspaceCitoyenApi(username, password)
    await hass.async_add_executor_job(api.authenticate)


class EspaceCitoyenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Espace Citoyen config flow."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Handle initial setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]

            try:
                await _validate_credentials(
                    self.hass,
                    username,
                    password,
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except EspaceCitoyenError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception(
                    "Erreur inattendue pendant la validation"
                )
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(username.lower())
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="Espace Citoyen",
                    data={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.TEXT,
                    )
                ),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=selector.TextSelectorType.PASSWORD,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> ConfigFlowResult:
        """Start reauthentication."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Confirm new credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            username = user_input[CONF_USERNAME].strip()
            password = user_input[CONF_PASSWORD]

            try:
                await _validate_credentials(
                    self.hass,
                    username,
                    password,
                )
            except AuthenticationError:
                errors["base"] = "invalid_auth"
            except EspaceCitoyenError:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception(
                    "Erreur inattendue pendant la réauthentification"
                )
                errors["base"] = "unknown"
            else:
                return self.async_update_reload_and_abort(
                    self._reauth_entry,
                    data_updates={
                        CONF_USERNAME: username,
                        CONF_PASSWORD: password,
                    },
                )

        current_username = (
            self._reauth_entry.data[CONF_USERNAME]
            if self._reauth_entry
            else ""
        )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=current_username,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        )
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        )
                    ),
                }
            ),
            errors=errors,
        )
