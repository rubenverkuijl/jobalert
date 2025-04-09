from app import app, db, User, JobAlert
from datetime import datetime, UTC
from werkzeug.security import generate_password_hash

def create_test_alert():
    with app.app_context():
        # Controleer of de test gebruiker bestaat
        test_user = User.query.filter_by(email='verkuijl@wearekayak.com').first()
        
        if not test_user:
            # Maak een test gebruiker aan
            test_user = User(
                email='verkuijl@wearekayak.com',
                password_hash=generate_password_hash('test123')  # Hash het wachtwoord
            )
            db.session.add(test_user)
            db.session.commit()
            print("Test gebruiker aangemaakt")
        
        # Controleer of de test alert bestaat
        test_alert = JobAlert.query.filter_by(
            user_id=test_user.id,
            search_query='Python'
        ).first()
        
        if not test_alert:
            # Maak een test alert aan
            test_alert = JobAlert(
                user_id=test_user.id,
                search_query='Python',
                location='Amsterdam',
                is_active=True,
                last_check=datetime.now(UTC),
                sent_job_ids='[]'
            )
            db.session.add(test_alert)
            db.session.commit()
            print("Test alert aangemaakt")
        else:
            print("Test alert bestaat al")

if __name__ == "__main__":
    create_test_alert() 