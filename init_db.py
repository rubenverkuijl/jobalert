from app import app, db
import os

def init_database():
    with app.app_context():
        # Verwijder de oude database als deze bestaat
        db_path = 'instance/kayak_jobs.db'
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print("Oude database verwijderd")
            except Exception as e:
                print(f"Kon oude database niet verwijderen: {e}")
        
        # Maak de instance directory aan als deze niet bestaat
        os.makedirs('instance', exist_ok=True)
        
        # Maak de database opnieuw aan
        db.create_all()
        print("Database succesvol aangemaakt!")

if __name__ == "__main__":
    init_database() 