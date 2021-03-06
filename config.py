import os

#This import is needed for VIP
from oauth2client.client import OAuth2WebServerFlow

#These are generally useful
CSRF_ENABLED = True
SECRET_KEY = os.getenv('SECRET_KEY')

#These variables configure the DECC scripts
deccinputdir = os.getenv('DECCINPUT')
deccoutputdir = os.getenv('DECCOUTPUT')
HOST = os.getenv('PGHOST')
USER = os.getenv('PGUSER')
DB = os.getenv('PGDB')
PASSWORD = os.getenv('PGPASSWORD')

#These are all VIP Variables
api_id = os.getenv('GOOGLE_NATIVE_APP_CLIENT_ID')
api_secret = os.getenv('GOOGLE_NATIVE_APP_CLIENT_SECRET')
api_key = os.getenv('GOOGLE_PUBLIC_API_KEY')
geokey = os.getenv('GOOGLE_GEOCODE_API_KEY')
vip_qa_data = os.getenv('VIPQADATA')
ev_qa_data = os.getenv('EVIPQADATA')
states = {'AL': 'Alabama', 'AR': 'Arkansas', 'AZ': 'Arizona', 'ME': 'Maine',
          'NH': 'New Hampshire', 'TN': 'Tennessee', 'LA': 'Louisiana',
          'IL': 'Illinois', 'IN': 'Indiana', 'ID': 'Idaho', 'GA': 'Georgia',
          'MA': 'Massachusetts', 'SD': 'South Dakota', 'VT': 'Vermont',
          'FL': 'Florida', 'MS': 'Mississippi', 'KY': 'Kentucky',
          'TX': 'Texas', 'SC': 'South Carolina', 'WV': 'West Virginia',
          'NM': 'New Mexico'}
scope1 = 'https://spreadsheets.google.com/feeds'
scope2 = 'https://www.googleapis.com/auth/drive'
scope = '{0} {1}'.format(scope1, scope2)
redirect = os.getenv('AUTH_REDIRECT')
flow = OAuth2WebServerFlow(client_id=api_id,
                           client_secret=api_secret,
                           scope=scope,
                           redirect_uri=redirect)
vipTemplateKey = '1qcqHBizQeFJwXsORMS_QS59gywuT9TRifwQe4BM_G3E'
evTemplateKey = '1_uEKMFrFxfu69Ws-2QbmUPm1kFNMY5txGJzG8bfzK4s'
