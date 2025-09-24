Project
=======

Deze map is bedoeld als overzichtelijke plek waar het volledige werkende project in staat.
Het bevat een 'working_copy' die je kunt vullen met de huidige projectbestanden via het bootstrap-script.

Structuur (in `project/working_copy`):

- `app/`      : Flask-app code (kopie van `app/`)
- `config/`   : Configuratiebestanden (kopie van `config/`)
- `static/`   : CSS/JS/afbeeldingen
- `templates/`: Jinja2 templates
- `scripts/`  : helper scripts
- `archive/`  : gearchiveerde tests en artifacts
- root files  : `run.py`, `requirements.txt`, `Dockerfile`, `README.md`, `VERSION`, etc.

Waarom dit zo:

- Houdt de hoofdmap schoon en gericht op repo-beheer (`.git`, CI, docs).
- Maakt het eenvoudig om een volledige, verplaatsbare projectmap te hebben (bijv. voor deployment of zip).

Hoe vullen:

1. Open PowerShell in de repository root.

2. Draai het bootstrap-script:

```powershell
.
\scripts\bootstrap_project.ps1
```

Het script maakt `project/working_copy/` en kopieert de relevante mappen en belangrijke root-bestanden.
Als `working_copy` al bestaat wordt het hernoemd naar een timestamped backup voordat er gekopieerd wordt.

Herstellen / rollback

- De originele bestanden blijven ongewijzigd in de repo. Gebruik de backup als je wilt terugdraaien.
