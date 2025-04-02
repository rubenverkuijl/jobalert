# Kayak Job Alerts Webapplicatie

Een moderne webapplicatie voor het beheren van persoonlijke job alerts voor het Kayak commercieel team.

## Functionaliteiten

- Persoonlijke accounts voor teamleden
- Aanmaken van meerdere job alerts per gebruiker
- Flexibele zoekcriteria (trefwoorden en locatie)
- Verschillende controlefrequenties (dagelijks, wekelijks, maandelijks)
- E-mailnotificaties voor nieuwe vacatures
- Modern en gebruiksvriendelijk dashboard

## Installatie

1. Installeer de benodigde packages:
```bash
pip install -r requirements.txt
```

2. Configureer het `.env` bestand:
```env
SECRET_KEY=uw_geheime_sleutel
EMAIL_USER=uw_email@gmail.com
EMAIL_PASSWORD=uw_app_specifieke_wachtwoord
```

> **Let op**: Voor Gmail moet u een app-specifiek wachtwoord genereren in uw Google Account instellingen.

## Gebruik

1. Start de webapplicatie:
```bash
python app.py
```

2. Start de achtergrondtaak voor het controleren van vacatures:
```bash
python worker.py
```

3. Open uw webbrowser en ga naar `http://localhost:5000`

## Ontwikkeling

De applicatie is gebouwd met:
- Flask voor de webapplicatie
- SQLAlchemy voor de database
- Flask-Login voor gebruikersauthenticatie
- Bootstrap 5 voor de frontend
- BeautifulSoup4 voor het scrapen van vacatures

## Structuur

- `app.py`: Hoofdapplicatie met routes en database modellen
- `worker.py`: Achtergrondtaak voor het controleren van vacatures
- `templates/`: HTML templates voor de gebruikersinterface
- `static/`: CSS, JavaScript en andere statische bestanden
- `kayak_jobs.db`: SQLite database met gebruikers en alerts

## Aanpassen van zoekcriteria

De zoekcriteria kunnen worden aangepast in het `search_jobs` method van de `worker.py` file. Momenteel zoekt het script naar vacatures op Indeed.nl. 