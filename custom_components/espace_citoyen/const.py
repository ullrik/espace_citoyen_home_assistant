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

# URLs reprises du script d'origine.
RESERVATION_URLS: dict[str, str] = {
    "Periscolaire": (
        f"{BASE_URL}{CITY_PATH}/DemandeEnfance/"
        "NouvelleDemandeReservation/3/292685/15/965"
    ),
    "ALP_Mercredi": (
        f"{BASE_URL}{CITY_PATH}/DemandeEnfance/"
        "NouvelleDemandeReservation/3/292983/15/268"
    ),
    "Ateliers": (
        f"{BASE_URL}{CITY_PATH}/DemandeEnfance/"
        "NouvelleDemandeReservation/3/292833/15/967"
    ),
    "Restauration_Scolaire": (
        f"{BASE_URL}{CITY_PATH}/DemandeEnfance/"
        "NouvelleDemandeReservation/3/292535/15/2070"
    ),
}

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
