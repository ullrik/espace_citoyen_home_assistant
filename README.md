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
```
type: markdown
content: >
  {% set planning = state_attr('sensor.planning_espace_citoyen_coueron',
  'planning') or {} %}
  {% set ns = namespace(rows=[]) %}

  {# Semaine actuelle #}
  {% set today = now().date() %}
  {% set monday = today - timedelta(days=today.weekday()) %}
  {% set sunday = monday + timedelta(days=6) %}

  {% for date, info in planning.items() %}
    {% set d = strptime(date, '%Y%m%d').date() %}

    {% if monday <= d <= sunday %}
      {% set r = info.reservations or {} %}
      {% set weekday = d.weekday() %}

      {# Icône du jour #}
      {% if weekday >= 5 %}
        {% set icon = '💤' %}
      {% elif info.isFermeOuFerie %}
        {% set icon = '🔴' %}
      {% else %}
        {% set icon = '🏫' %}
      {% endif %}

      {# Icône verrouillage #}
      {% if info.isActif %}
        {% set lock = '🟢' %}
      {% else %}
        {% set lock = '🔒' %}
      {% endif %}

      {% set matin = '✅' if r.get('peri_mat', false) else '—' %}
      {% if r.get('repas_midi', false) %}
        {% set midi = '✅' %}
      {% elif r.get('peri_mercredi_midi', false) %}
        {% set midi = '➡️' %}
      {% else %}
        {% set midi = '—' %}
      {% endif %}
      {% if r.get('peri_mercredi_midi', false) %}
        {% set midi = midi ~ ' <small>12h30<small>' %}
      {% endif %}
      {% if r.get('peri_mercredi_midi', false) and r.get('alp_mercredi', false) %}
        {% set atelier = '⚠️' %}
      {% elif r.get('atelier_ville', false) or r.get('alp_mercredi', false) %}
        {% set atelier = '✅' %}
      {% else %}
        {% set atelier = '—' %}
      {% endif %}
      {% if r.get('alp_mercredi', false) %}
        {% set atelier = atelier ~ '<small>17h<small>' %}
      {% endif %}
      {% set soir = '✅' if r.get('peri_soir', false) else '—' %}

      {% set ligne = '| ' ~ icon ~ '&nbsp;&nbsp;' ~ info.date.split(' ')[0] ~ ' ' ~ info.date.split(' ')[1] ~ '&ensp;' ~ lock ~ ' | ' ~ matin ~ ' | ' ~ midi ~ ' | ' ~ atelier ~ ' | ' ~ soir ~ ' |' %}

      {% set ns.rows = ns.rows + [ligne] %}

    {% endif %}
  {% endfor %}


  ### Cette semaine — du {{ monday.strftime('%d/%m') }} au {{
  sunday.strftime('%d/%m/%Y') }}


  | Jour | 🌅 Matin | 🍽️ Midi | 🎨 Atelier | 🌙 Soir |

  |:---|:---:|:---:|:---:|:---:|

  {{ ns.rows | join('\n') }}


  **Légende :** 🏫 École &nbsp; 💤 Week-end &nbsp; 🔴 Fermé / vacances &nbsp; 🟢
  Modifiable &nbsp; 🔒 Verrouillé
card_mod:
  style:
    ha-markdown$: |
      table {
        width: 100%;
        table-layout: auto;
      }

      table th:first-child,
      table td:first-child {
        width: auto;
      }

      table th:not(:first-child),
      table td:not(:first-child) {
        width: 42px;
        min-width: 42px;
        max-width: 42px;
        padding-left: 4px;
        padding-right: 4px;
        text-align: center;
      }
```
Pour avoir la semaine suivante : 
changer cette ligne : 
```
  {% set monday = today - timedelta(days=today.weekday()) + timedelta(days=7) %}
```


## Débogage

Pour activer les logs détaillés :

    logger:
      default: info
      logs:
        custom_components.espace_citoyen: debug
