# Espace Citoyen — custom integration Home Assistant

Cette intégration reprend le scraping du script `espace_citoyen.py` et l'intègre
directement dans Home Assistant.

## Fonctionnement

- configuration par l'interface Home Assistant avec identifiant + mot de passe ;
- validation des identifiants à l'ajout ;
- récupération du planning de la semaine courante et de la semaine suivante ;
- actualisation automatique tous les jours à 06:00 (heure locale de Home Assistant) ;
- après un redémarrage postérieur à 06:00, une actualisation est faite si celle du jour manque ;
- actualisation manuelle par un bouton ;
- conservation en stockage interne Home Assistant de la dernière récupération réussie ;
- si une actualisation réseau échoue, le planning précédent n'est pas écrasé ;
- si l'authentification devient invalide, Home Assistant déclenche une réauthentification.

## Installation

Copier le dossier :

    custom_components/espace_citoyen

dans le dossier `/config/custom_components/` de Home Assistant.

La structure doit donc être :

    /config/custom_components/espace_citoyen/manifest.json
    /config/custom_components/espace_citoyen/__init__.py
    ...

Redémarrer Home Assistant, puis aller dans :

    Paramètres > Appareils et services > Ajouter une intégration

et rechercher :

    Espace Citoyen

## Entités

L'intégration crée notamment :

    sensor.planning_espace_citoyen_coueron
    button.planning_espace_citoyen_coueron_rafraichir_reservation

Les entity_id exacts peuvent varier si des entités portant ces noms existent déjà.
Utiliser les noms affichés dans Home Assistant pour confirmer.

L'état du sensor est la date/heure de la dernière récupération réussie.

Attributs principaux :

    planning
    last_update
    last_error

`planning` contient uniquement la semaine courante et la semaine suivante.

## Exemple Markdown Lovelace

    type: markdown
    content: >
      {% set planning = state_attr('sensor.espace_citoyen_planning', 'planning') or {} %}

      ## 📚 Planning Scolaire

      | Jour | 🌅 Matin | 🍽️ Midi | 🎨 Atelier | 🌙 Soir |
      |------|---------|---------|---------|---------|
      {% for date, info in planning.items() %}
        {% if info.isActif %}
          {% set r = info.reservations %}
      | {{ info.date }} |
      {{ '✅' if r.get('peri_mat') else '❌' }} |
      {{ '✅' if r.get('repas_midi') else '❌' }} |
      {{ '✅' if r.get('atelier_ville') else '❌' }} |
      {{ '✅' if r.get('peri_soir') else '❌' }} |
        {% endif %}
      {% endfor %}

Attention : dans le script d'origine le créneau du matin s'appelle `peri_mat`
(et non `peri_matin`). L'intégration conserve volontairement ce nom.

## URLs de réservation

La version 1.0.0 conserve les quatre URLs spécifiques présentes dans le script
d'origine ainsi que le mapping `idUnite -> créneau`.

Elles sont dans :

    custom_components/espace_citoyen/const.py

Si les identifiants d'inscription changent à la prochaine année scolaire, ces URLs
pourront devoir être mises à jour. Une évolution ultérieure pourra chercher à les
découvrir automatiquement depuis le compte.

## Débogage

Pour activer les logs détaillés :

    logger:
      default: info
      logs:
        custom_components.espace_citoyen: debug
