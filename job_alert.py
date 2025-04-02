import os
import json
import requests
from bs4 import BeautifulSoup
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Laad environment variables
load_dotenv()

class JobAlert:
    def __init__(self):
        self.seen_jobs = set()
        self.load_seen_jobs()
        
    def load_seen_jobs(self):
        try:
            with open('seen_jobs.json', 'r') as f:
                self.seen_jobs = set(json.load(f))
        except FileNotFoundError:
            self.seen_jobs = set()
            
    def save_seen_jobs(self):
        with open('seen_jobs.json', 'w') as f:
            json.dump(list(self.seen_jobs), f)
            
    def search_jobs(self):
        # Hier implementeren we de zoeklogica voor vacatures
        # Dit is een voorbeeld voor Indeed.nl
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        search_url = "https://www.indeed.nl/jobs?q=commercieel&l=nederland"
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        jobs = []
        for job in soup.find_all('div', class_='job_seen_beacon'):
            job_id = job.get('data-jk')
            if job_id and job_id not in self.seen_jobs:
                title = job.find('h2', class_='jobTitle').text.strip()
                company = job.find('span', class_='companyName').text.strip()
                location = job.find('div', class_='companyLocation').text.strip()
                
                jobs.append({
                    'id': job_id,
                    'title': title,
                    'company': company,
                    'location': location
                })
                self.seen_jobs.add(job_id)
        
        self.save_seen_jobs()
        return jobs
    
    def send_email(self, jobs):
        if not jobs:
            return
            
        sender_email = os.getenv('EMAIL_USER')
        receiver_email = os.getenv('EMAIL_RECEIVER')
        password = os.getenv('EMAIL_PASSWORD')
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = f'Nieuwe Vacatures Gevonden - {datetime.now().strftime("%d-%m-%Y")}'
        
        body = "De volgende nieuwe vacatures zijn gevonden:\n\n"
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
            print("E-mail succesvol verzonden!")
        except Exception as e:
            print(f"Fout bij het verzenden van de e-mail: {str(e)}")

def main():
    job_alert = JobAlert()
    
    def check_jobs():
        print(f"Controleren op nieuwe vacatures... {datetime.now()}")
        jobs = job_alert.search_jobs()
        if jobs:
            job_alert.send_email(jobs)
            print(f"{len(jobs)} nieuwe vacatures gevonden en verzonden.")
        else:
            print("Geen nieuwe vacatures gevonden.")
    
    # Controleer direct bij het starten
    check_jobs()
    
    # Plan dagelijkse controle om 9:00 uur
    schedule.every().day.at("09:00").do(check_jobs)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    main() 