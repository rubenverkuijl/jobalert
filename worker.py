from app import app, db, JobAlert
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import time

load_dotenv()

def check_jobs():
    with app.app_context():
        # Haal alle actieve alerts op
        alerts = JobAlert.query.filter_by(is_active=True).all()
        
        for alert in alerts:
            # Controleer of het tijd is om te zoeken
            last_check = alert.last_check
            now = datetime.utcnow()
            
            if alert.frequency == 'daily' and (now - last_check).days < 1:
                continue
            elif alert.frequency == 'weekly' and (now - last_check).days < 7:
                continue
            elif alert.frequency == 'monthly' and (now - last_check).days < 30:
                continue
            
            # Zoek naar vacatures
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            location = alert.location if alert.location else 'nederland'
            search_url = f"https://www.indeed.nl/jobs?q={alert.search_query}&l={location}"
            
            try:
                response = requests.get(search_url, headers=headers)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                jobs = []
                for job in soup.find_all('div', class_='job_seen_beacon'):
                    title = job.find('h2', class_='jobTitle').text.strip()
                    company = job.find('span', class_='companyName').text.strip()
                    location = job.find('div', class_='companyLocation').text.strip()
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location
                    })
                
                if jobs:
                    send_job_alert(alert.user.email, alert.search_query, jobs)
                
                # Update last_check
                alert.last_check = now
                db.session.commit()
                
            except Exception as e:
                print(f"Fout bij het controleren van vacatures voor alert {alert.id}: {str(e)}")

def send_job_alert(user_email, search_query, jobs):
    sender_email = os.getenv('EMAIL_USER')
    password = os.getenv('EMAIL_PASSWORD')
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = user_email
    msg['Subject'] = f'Nieuwe Vacatures Gevonden voor "{search_query}"'
    
    body = f"Er zijn {len(jobs)} nieuwe vacatures gevonden voor uw zoekopdracht '{search_query}':\n\n"
    for job in jobs:
        body += f"Titel: {job['title']}\n"
        body += f"Bedrijf: {job['company']}\n"
        body += f"Locatie: {job['location']}\n"
        body += "-" * 50 + "\n"
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        server.send_message(msg)
        server.quit()
        print(f"E-mail succesvol verzonden naar {user_email}")
    except Exception as e:
        print(f"Fout bij het verzenden van de e-mail: {str(e)}")

if __name__ == '__main__':
    # Eerst een test mail versturen
    print("Test mail wordt verstuurd...")
    test_jobs = [{
        'title': 'Test Vacature',
        'company': 'Test Bedrijf',
        'location': 'Test Locatie'
    }]
    
    try:
        send_job_alert(os.getenv('EMAIL_USER'), 'TEST ALERT', test_jobs)
        print("Test mail is succesvol verstuurd!")
    except Exception as e:
        print(f"Fout bij versturen test mail: {str(e)}")
    
    print("\nStart normale job check proces...")
    while True:
        check_jobs()
        # Controleer elk uur
        time.sleep(3600)