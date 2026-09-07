"""Synchronous web client for Espace Citoyen.

The web site is scraped with requests/BeautifulSoup. All methods in this
module are synchronous and must therefore be executed in Home Assistant's
executor.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .const import (
    BASE_URL,
    CITY_PATH,
    CRENEAUX,
    LOGIN_PAGE_URL,
    LOGIN_URL,
    RESERVATION_TYPES,
)


class EspaceCitoyenError(Exception):
    """Base exception for the Espace Citoyen client."""


class AuthenticationError(EspaceCitoyenError):
    """Raised when authentication fails."""


class EspaceCitoyenConnectionError(EspaceCitoyenError):
    """Raised when the web site cannot be reached or parsed."""


class EspaceCitoyenApi:
    """Client used by the Home Assistant integration."""

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self._password = password
        self._reservation_urls: list[str] = []

    @staticmethod
    def _convertir_date_fr(number: int | str) -> str:
        parsed = datetime.strptime(str(number), "%Y%m%d")
        jours = [
            "lundi",
            "mardi",
            "mercredi",
            "jeudi",
            "vendredi",
            "samedi",
            "dimanche",
        ]
        mois = [
            "janvier",
            "février",
            "mars",
            "avril",
            "mai",
            "juin",
            "juillet",
            "août",
            "septembre",
            "octobre",
            "novembre",
            "décembre",
        ]
        return (
            f"{jours[parsed.weekday()]} {parsed.day:02d} "
            f"{mois[parsed.month - 1]}"
        )

    @staticmethod
    def _new_session() -> requests.Session:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/151.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "fr-FR,fr;q=0.9",
            }
        )
        return session

    @staticmethod
    def _get_verification_token(session: requests.Session) -> str:
        response = session.get(LOGIN_PAGE_URL, timeout=(10, 30))
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        token_input = soup.select_one(
            '#idFormConnexion input[name="__RequestVerificationToken"]'
        )

        if token_input is None:
            raise AuthenticationError(
                "Le champ __RequestVerificationToken est introuvable."
            )

        token = token_input.get("value")
        if not token:
            raise AuthenticationError(
                "Le token anti-CSRF est présent mais vide."
            )

        return str(token)

    @staticmethod
    def _get_reservation_urls(html: str) -> dict[str, str]:
        """Extract reservation URLs from the citizen account page."""
        matches = re.findall(
            r'href="([^"]*NouvelleDemandeReservation/\d+/\d+/\d+/\d+)"',
            html,
        )

        # Supprime les éventuels doublons tout en conservant l'ordre.
        matches = list(dict.fromkeys(matches))

        if len(matches) != len(RESERVATION_TYPES):
            raise EspaceCitoyenConnectionError(
                f"Nombre inattendu de calendriers trouvés : "
                f"{len(matches)} au lieu de {len(RESERVATION_TYPES)}."
            )

        #return {
        #    name: urljoin(BASE_URL, match)
        #    for name, match in zip(RESERVATION_TYPES, matches)
        #}
        return [
            urljoin(BASE_URL, match)
            for match in matches
        ]

    def _login(self) -> requests.Session:
        session = self._new_session()
        token = self._get_verification_token(session)

        response = session.post(
            LOGIN_URL,
            data={
                "__RequestVerificationToken": token,
                "username": self._username,
                "password": self._password,
            },
            headers={
                "Referer": LOGIN_PAGE_URL,
                "Origin": BASE_URL,
            },
            timeout=(10, 30),
            allow_redirects=False,
        )

        if response.status_code not in {200, 302, 303}:
            raise EspaceCitoyenConnectionError(
                f"Réponse inattendue du serveur : HTTP {response.status_code}"
            )

        if response.status_code in {302, 303}:
            redirect_location = response.headers.get("Location")
            if not redirect_location:
                raise EspaceCitoyenConnectionError(
                    "Le serveur renvoie une redirection sans destination."
                )

            redirect_url = urljoin(LOGIN_URL, redirect_location)
            if urlparse(redirect_url).netloc != urlparse(BASE_URL).netloc:
                raise EspaceCitoyenConnectionError(
                    "Redirection vers un domaine inattendu."
                )

            response = session.get(
                redirect_url,
                headers={"Referer": LOGIN_URL},
                timeout=(10, 30),
            )
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        if soup.select_one("#idFormConnexion") is not None:
            raise AuthenticationError(
                "Identifiant ou mot de passe incorrect."
            )

        return session

    def authenticate(self) -> None:
        """Validate credentials without fetching all calendars."""
        session = None
        try:
            session = self._login()
            account_url = f"{BASE_URL}{CITY_PATH}/CompteCitoyen"

            response = session.get(account_url, timeout=(10, 30))
            response.raise_for_status()

            self._reservation_urls = self._get_reservation_urls(response.text)
        except AuthenticationError:
            raise
        except requests.RequestException as err:
            raise EspaceCitoyenConnectionError(str(err)) from err
        finally:
            if session is not None:
                session.close()

    @staticmethod
    def _extract_int(pattern: str, html: str, name: str) -> str:
        match = re.search(pattern, html)
        if match is None:
            raise EspaceCitoyenConnectionError(
                f"Impossible de trouver le paramètre {name}."
            )
        return match.group(1)

    def _get_calendrier_reservation(
        self,
        session: requests.Session,
        reservation_url: str,
    ) -> dict:
        response = session.get(reservation_url, timeout=(10, 30))
        response.raise_for_status()
        html = response.text

        id_per = self._extract_int(r"var idPer = (\d+)", html, "idPer")
        id_ins = self._extract_int(r"var idIns = (\d+)", html, "idIns")
        id_lie = self._extract_int(r"var idLie = (\d+)", html, "idLie")
        id_clg = self._extract_int(r"var idClg = (\d+)", html, "idClg")

        calendrier_url = (
            f"{BASE_URL}{CITY_PATH}/DemandeEnfance/"
            "NouvelleDemandeReservationGetCalendrier"
        )

        response_calendrier = session.get(
            calendrier_url,
            params={
                "idPer": id_per,
                "idIns": id_ins,
                "idLie": id_lie,
                "idClg": id_clg,
            },
            headers={
                "x-requested-with": "XMLHttpRequest",
                "Referer": reservation_url,
            },
            timeout=(10, 30),
        )
        response_calendrier.raise_for_status()

        try:
            return response_calendrier.json()
        except requests.exceptions.JSONDecodeError as err:
            raise EspaceCitoyenConnectionError(
                "Le calendrier n'a pas renvoyé un JSON valide."
            ) from err

    @staticmethod
    def _date_window(today: date) -> tuple[date, date]:
        """Return Monday current week -> Sunday next week."""
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=13)
        return start, end

    def get_planning(self, today: date) -> dict[str, dict]:
        """Fetch and aggregate current week + next week planning."""
        start_date, end_date = self._date_window(today)
        jours_data: dict[str, dict] = {}
        session = None

        try:
            session = self._login()

            if not self._reservation_urls:
                self.authenticate()
                #raise EspaceCitoyenConnectionError(
                #    "Les URLs de réservation ne sont pas disponibles. "
                #    "Appelez authenticate() avant get_planning()."
                #)
            
            #for reservation_url in reservation_urls.values():
            for reservation_url in self._reservation_urls:
                data = self._get_calendrier_reservation(
                    session,
                    reservation_url,
                )

                semaines = data.get("listeSemainesAffichees")
                if not isinstance(semaines, list):
                    raise EspaceCitoyenConnectionError(
                        "Format du calendrier inattendu : "
                        "listeSemainesAffichees absente."
                    )

                for semaine in semaines:
                    for jour_data in semaine.get("listeJoursAffiches", []):
                        id_jour = jour_data.get("idJour")
                        if not id_jour:
                            continue

                        try:
                            parsed_date = datetime.strptime(
                                str(id_jour),
                                "%Y%m%d",
                            ).date()
                        except (TypeError, ValueError):
                            continue

                        if not start_date <= parsed_date <= end_date:
                            continue

                        key = str(id_jour)
                        if key not in jours_data:
                            jours_data[key] = {
                                "date": self._convertir_date_fr(id_jour),
                                "isActif": bool(
                                    jour_data.get("isActif", False)
                                ),
                                "isFermeOuFerie": bool(
                                    jour_data.get("isFermeOuFerie", False)
                                ),
                                "reservations": {},
                            }

                        for unite in jour_data.get("listeUnitesJour", []):
                            if unite.get("nbConsoBase") != 1:
                                continue

                            creneau = CRENEAUX.get(unite.get("idUnite"))
                            if creneau:
                                jours_data[key]["reservations"][creneau] = True

            return dict(sorted(jours_data.items()))

        except AuthenticationError:
            raise
        except requests.Timeout as err:
            raise EspaceCitoyenConnectionError(
                "Le serveur n'a pas répondu dans le délai prévu."
            ) from err
        except requests.RequestException as err:
            raise EspaceCitoyenConnectionError(
                f"Erreur HTTP : {err}"
            ) from err
        finally:
            if session is not None:
                session.close()
