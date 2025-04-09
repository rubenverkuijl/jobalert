from app import app, db, User, JobAlert

def cleanup_alerts():
    with app.app_context():
        # Zoek de test gebruiker
        test_user = User.query.filter_by(email='test@example.com').first()
        
        if test_user:
            # Verwijder alle alerts van deze gebruiker
            JobAlert.query.filter_by(user_id=test_user.id).delete()
            
            # Verwijder de gebruiker
            db.session.delete(test_user)
            
            db.session.commit()
            print("Test gebruiker en bijbehorende alerts zijn verwijderd")
        else:
            print("Test gebruiker niet gevonden")

if __name__ == "__main__":
    cleanup_alerts() 