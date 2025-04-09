import json
import os
import time
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, UTC
from dotenv import load_dotenv
from app import app, db, JobAlert

# Laad environment variabelen
load_dotenv()

# Configuratie voor mock data
USE_MOCK_DATA = True  # Zet dit op False om SerpApi te gebruiken
MOCK_DATA_FILE = 'mock_jobs.json'

def generate_job_id(job):
    """Genereer een unieke ID voor een vacature"""
    return f"{job.get('title', '')}_{job.get('company_name', '')}_{job.get('location', '')}"

def get_jobs_from_mock():
    """Haal vacatures op uit mock_jobs.json"""
    try:
        with open(MOCK_DATA_FILE, 'r', encoding='utf-8') as f:
            mock_data = json.load(f)
            print("Mock data succesvol geladen")
            return mock_data  # Direct de lijst met vacatures teruggeven
    except Exception as e:
        print(f"Fout bij het laden van mock data: {str(e)}")
        return []

def send_job_alert_email(user_email, search_query, location, jobs):
    try:
        # E-mail configuratie
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = os.getenv("EMAIL_USER")
        sender_password = os.getenv("EMAIL_PASSWORD")
        
        # E-mail bericht samenstellen
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = user_email
        msg['Subject'] = "Uw vacature leads van Kayak.jobs"
        
        # HTML inhoud voor de e-mail
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .job {{ margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #f9f9f9; }}
                .job-title {{ font-weight: bold; color: #2c3e50; font-size: 16px; margin-bottom: 5px; }}
                .job-company {{ color: #7f8c8d; margin-bottom: 5px; }}
                .job-location {{ color: #95a5a6; margin-bottom: 10px; }}
                .button {{ 
                    display: inline-block; 
                    padding: 8px 15px; 
                    background-color: #3498db; 
                    color: #ffffff !important; 
                    text-decoration: none !important; 
                    border-radius: 3px;
                    margin-top: 10px;
                }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
                .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Uw vacature leads van Kayak.jobs</h2>
                    <p>Er zijn {len(jobs)} nieuwe vacatures gevonden die voldoen aan uw zoekcriteria.</p>
                </div>
                <div class="jobs">
        """
        
        for job in jobs:
            # Haal de link uit de apply_options als die er is
            apply_link = None
            if 'apply_options' in job and len(job['apply_options']) > 0:
                apply_link = job['apply_options'][0].get('link', '')
            
            # Als er geen apply_link is, gebruik dan de job link
            final_link = apply_link or job.get('link', '')
            
            # Maak de link URL veilig voor HTML
            safe_link = final_link.replace('"', '&quot;')
            html_content += f"""
                    <div class="job">
                        <div class="job-title">{job.get('title', 'Geen titel')}</div>
                        <div class="job-company">{job.get('company_name', 'Onbekend bedrijf')}</div>
                        <div class="job-location">{job.get('location', 'Onbekende locatie')}</div>
                        <a href="{safe_link}" class="button">Bekijk vacature →</a>
                    </div>
            """
        
        html_content += """
                </div>
                <div class="footer">
                    <p>Met vriendelijke groeten,<br>team Kayak.jobs</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Voeg zowel HTML als plain text toe
        text_content = f"""
        Uw vacature leads van Kayak.jobs
        
        Er zijn {len(jobs)} nieuwe vacatures gevonden die voldoen aan uw zoekcriteria.
        
        """
        
        for job in jobs:
            text_content += f"""
        Titel: {job.get('title', 'Geen titel')}
        Bedrijf: {job.get('company_name', 'Onbekend bedrijf')}
        Locatie: {job.get('location', 'Onbekende locatie')}
        Link: {job.get('link', '')}
        
        """
        
        text_content += """
        Met vriendelijke groeten,
        team Kayak.jobs
        """
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        # E-mail versturen
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        print(f"E-mail succesvol verzonden naar {user_email}")
        
    except Exception as e:
        print(f"Fout bij het verzenden van de e-mail: {str(e)}")

def check_jobs():
    """Controleer alle actieve job alerts en stuur emails voor nieuwe vacatures"""
    print("Start normale job check...")
    
    with app.app_context():
        # Haal alle actieve alerts op
        active_alerts = JobAlert.query.filter_by(is_active=True).all()
        print(f"Aantal actieve alerts gevonden: {len(active_alerts)}")
        
        for alert in active_alerts:
            print(f"\nControleren alert: {alert.search_query} in {alert.location}")
            
            # Controleer of de alert recent is gecontroleerd
            if alert.last_check:
                # Converteer last_check naar UTC als het naive is
                if alert.last_check.tzinfo is None:
                    last_check_utc = alert.last_check.replace(tzinfo=UTC)
                else:
                    last_check_utc = alert.last_check
                
                if (datetime.now(UTC) - last_check_utc) < timedelta(hours=24):
                    print("Alert is te recent gecontroleerd, overslaan...")
                    continue
                
            try:
                if USE_MOCK_DATA:
                    print("Gebruik mock data in plaats van SerpApi")
                    all_jobs = get_jobs_from_mock()
                else:
                    # SerpApi parameters
                    location = alert.location if alert.location else "Netherlands"
                    params = {
                        "engine": "google_jobs",
                        "q": f"{alert.search_query}",
                        "location": location,
                        "hl": "nl",
                        "gl": "nl",
                        "api_key": os.getenv("SERPAPI_KEY"),
                        "num": "25",
                        "lrad": "50",  # Zoekradius in kilometers
                        "chips": "date_posted:today"  # Alleen vacatures van vandaag
                    }
                    
                    print(f"Zoeken naar: {params['q']} in {params['location']}")
                    print(f"API Key aanwezig: {'Ja' if os.getenv('SERPAPI_KEY') else 'Nee'}")
                    
                    # Verzamel resultaten van meerdere pagina's
                    all_jobs = []
                    next_page_token = None
                    max_pages = 3  # Maximum aantal pagina's om te controleren
                    max_jobs = 25  # Maximum aantal resultaten
                    
                    for page in range(max_pages):
                        if next_page_token:
                            params["next_page_token"] = next_page_token
                        
                        print(f"Versturen request naar SerpApi...")
                        response = requests.get("https://serpapi.com/search", params=params)
                        print(f"Response status code: {response.status_code}")
                        
                        if response.status_code != 200:
                            print(f"Error response: {response.text}")
                            break
                            
                        response.raise_for_status()
                        data = response.json()
                        
                        # Debug informatie
                        print(f"Response keys: {list(data.keys())}")
                        
                        if "jobs_results" in data:
                            jobs = data["jobs_results"]
                            print(f"Gevonden {len(jobs)} vacatures op pagina {page + 1}")
                            all_jobs.extend(jobs)
                            
                            # Controleer of we genoeg resultaten hebben
                            if len(all_jobs) >= max_jobs:
                                all_jobs = all_jobs[:max_jobs]
                                break
                            
                            # Controleer of er een volgende pagina is
                            next_page_token = data.get("serpapi_pagination", {}).get("next_page_token")
                            if not next_page_token:
                                print("Geen volgende pagina beschikbaar")
                                break
                                
                            # Wacht even tussen requests
                            time.sleep(2)
                        else:
                            print("Geen vacatures gevonden in response")
                            print(f"Beschikbare data: {data}")
                            break
                
                print(f"Totaal aantal gevonden vacatures: {len(all_jobs)}")
                
                if all_jobs:
                    # Haal de verzonden job IDs op
                    sent_job_ids = json.loads(alert.sent_job_ids)
                    
                    # Filter nieuwe vacatures
                    new_jobs = []
                    for job in all_jobs:
                        job_id = generate_job_id(job)
                        if job_id not in sent_job_ids:
                            new_jobs.append(job)
                    
                    print(f"Aantal nieuwe vacatures: {len(new_jobs)}")
                    
                    if new_jobs:
                        # Haal de gebruiker op via de relatie
                        user = alert.user
                        if user and user.email:
                            # Stuur email met de nieuwe vacatures
                            send_job_alert_email(user.email, alert.search_query, alert.location, new_jobs)
                            print(f"Email verzonden naar {user.email}")
                            
                            # Update sent_job_ids
                            new_job_ids = [generate_job_id(job) for job in new_jobs]
                            sent_job_ids.extend(new_job_ids)
                            
                            # Beperk de lijst tot 10.000 tekens
                            if len(json.dumps(sent_job_ids)) > 10000:
                                sent_job_ids = sent_job_ids[-100:]  # Houd de laatste 100 IDs
                            
                            alert.sent_job_ids = json.dumps(sent_job_ids)
                            db.session.commit()
                        else:
                            print(f"Geen geldig email adres gevonden voor alert {alert.id}")
                
                # Update last_check tijd
                alert.last_check = datetime.now(UTC)
                db.session.commit()
                
            except Exception as e:
                print(f"Fout bij het controleren van alert {alert.id}: {str(e)}")
                if hasattr(e, 'response'):
                    print(f"Response body: {e.response.text}")
                continue

if __name__ == "__main__":
    while True:
        check_jobs()
        print("\nWachten op volgende check...")
        time.sleep(300)  # Wacht 5 minuten