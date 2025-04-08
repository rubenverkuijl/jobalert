import sys
import os

# Voeg het project directory toe aan het Python pad
path = '/home/rubenverkuijl/job_alert_2'
if path not in sys.path:
    sys.path.append(path)

# Stel de environment variabelen in
os.environ['FLASK_ENV'] = 'production'

# Importeer de Flask app
from app import app as application 