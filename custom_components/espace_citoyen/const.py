"""Constants for the Espace Citoyen integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "espace_citoyen"

CONF_USERNAME = "username"
CONF_PASSWORD = "password"

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BUTTON]

BASE_URL = "https://www.espace-citoyens.net"
CITY_PATH = "/ville-coueron/espace-citoyens"

LOGIN_PAGE_URL = f"{BASE_URL}{CITY_PATH}/"
LOGIN_URL = f"{BASE_URL}{CITY_PATH}/Home/Logon"

REGEX_RESERVATION: r'href="([^"]*NouvelleDemandeReservation/\d+/\d+/\d+/\d+)"'

RESERVATION_TYPES: tuple[str, ...] = (
    "Periscolaire",
    "ALP_Mercredi",
    "Ateliers",
    "Restauration_Scolaire",
)

CRENEAUX: dict[int, str] = {
    1: "repas_midi",
    3: "peri_mat",
    4: "peri_soir",
    43: "alp_mercredi",
    48: "peri_mercredi_midi",
    56: "atelier_ville",
}

UPDATE_HOUR = 6
UPDATE_MINUTE = 0
UPDATE_SECOND = 0

STORAGE_VERSION = 1
STORAGE_KEY_PREFIX = "espace_citoyen"

ATTR_PLANNING = "planning"
ATTR_LAST_UPDATE = "last_update"
ATTR_LAST_ERROR = "last_error"
