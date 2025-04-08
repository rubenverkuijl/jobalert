from app import app, db, JobAlert
from datetime import datetime, timedelta

def reset_alerts():
    with app.app_context():
        # Haal alle alerts op
        alerts = JobAlert.query.all()
        
        # Zet de last_check tijd 2 dagen terug
        two_days_ago = datetime.utcnow() - timedelta(days=2)
        
        for alert in alerts:
            alert.last_check = two_days_ago
            print(f"Reset alert: {alert.search_query}")
        
        # Sla de wijzigingen op
        db.session.commit()
        print("Alle alerts zijn gereset!")

if __name__ == '__main__':
    reset_alerts() 