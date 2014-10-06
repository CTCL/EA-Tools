from oauth2client.client import OAuth2WebServerFlow
import os

api_id = os.getenv('GOOGLE_NATIVE_APP_CLIENT_ID')
api_secret = os.getenv('GOOGLE_NATIVE_APP_CLIENT_SECRET')
api_key = os.getenv('GOOGLE_PUBLIC_API_KEY')
vip_qa_data = os.getenv('VIPQADATA')
ev_qa_data = os.getenv('EVIPQADATA')
deccinputdir = os.getenv('DECCINPUT')
deccoutputdir = os.getenv('DECCOUTPUT')
HOST = os.getenv('PGHOST')
USER = os.getenv('PGUSER')
DB = os.getenv('PGDB')

CSRF_ENABLED = True
SECRET_KEY = os.getenv('SECRET_KEY')

states = {'AL': 'Alabama', 'AR': 'Arkansas', 'AZ': 'Arizona',
          'NH': 'New Hampshire',
          #'CA': 'California',
          #'GA': 'Georgia', 'ID': 'Idaho', 'IN': 'Indiana',
          #'LA': 'Louisiana', #'ME': 'Maine', 'MA': 'Massachusetts',
          #'SD': 'South Dakota', 'TN': 'Tennessee', #'TX': 'Texas'
          }

scope = '''https://spreadsheets.google.com/feeds
           https://www.googleapis.com/auth/drive'''
redirect = 'http://127.0.0.1:5000/auth_return'
flow = OAuth2WebServerFlow(client_id=api_id,
                           client_secret=api_secret,
                           scope=scope,
                           redirect_uri=redirect)

vipTemplateKey = '1qcqHBizQeFJwXsORMS_QS59gywuT9TRifwQe4BM_G3E'
evTemplateKey = '1_uEKMFrFxfu69Ws-2QbmUPm1kFNMY5txGJzG8bfzK4s'