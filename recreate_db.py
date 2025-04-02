from app import app, db
import os

def recreate_database():
    with app.app_context():
        # Verwijder de oude database als deze bestaat
        if os.path.exists('instance/kayak_jobs.db'):
            os.remove('instance/kayak_jobs.db')
        
        # Maak de database opnieuw aan
        db.create_all()
        print("Database succesvol opnieuw aangemaakt!")

if __name__ == "__main__":
    recreate_database() 