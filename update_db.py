from app import app, db

def update_database():
    with app.app_context():
        # Voeg nieuwe kolommen toe
        db.engine.execute('ALTER TABLE user ADD COLUMN reset_token VARCHAR(100) UNIQUE')
        db.engine.execute('ALTER TABLE user ADD COLUMN reset_token_expiry DATETIME')
        print("Database succesvol bijgewerkt!")

if __name__ == "__main__":
    update_database() 