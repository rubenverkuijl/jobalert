from app import app, db, User
from werkzeug.security import generate_password_hash

def reset_password(email, new_password):
    with app.app_context():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            print(f"Wachtwoord succesvol gereset voor {email}")
        else:
            print(f"Geen gebruiker gevonden met e-mail {email}")

if __name__ == "__main__":
    email = input("Voer uw e-mailadres in: ")
    new_password = input("Voer een nieuw wachtwoord in: ")
    reset_password(email, new_password) 