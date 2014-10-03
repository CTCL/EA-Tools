from gdata.spreadsheets.data import ListEntry
from apiclient import errors
from apiclient.discovery import build
from oauth2client.file import Storage
import gdata
import gdata.spreadsheets.client
import gdata.gauth
import time
import httplib2


def getService(service, version, creds):
    http = httplib2.Http()
    creds.authorize(http)
    return build(service, version, http=http)


def copySheet(name, originalKey, creds):
    service = getService('drive', 'v2', creds)
    newFile = {'title': name}
    try:
        return service.files().copy(fileId=originalKey,
                                    body=newFile).execute()
    except errors.HttpError, error:
        print 'An error occurred {0}'.format(error)
    return None


def getClient():
    client = gdata.spreadsheets.client.SpreadsheetsClient()
    credentials = Storage('.cred').get()
    scope = 'https://spreadsheets.google.com/feeds'
    clientid = credentials.client_id
    clientsecret = credentials.client_secret
    access = credentials.access_token
    refresh = credentials.refresh_token
    auth2token = gdata.gauth.OAuth2Token(client_id=clientid,
                                         client_secret=clientsecret,
                                         scope=scope,
                                         access_token=access,
                                         refresh_token=refresh,
                                         user_agent='sites-test/1.0')
    auth2token.authorize(client)
    return client


def convertRow(rowDict):
    #The api doesn't like capital letters or spaces.
    fixedRow = {'date': time.strftime("%m/%d/%Y")}
    for key in rowDict:
        fixedRow[key.lower().replace(' ', '')] = rowDict[key]
    return fixedRow


def writeRow(rowDict, client, sheetKey, sheetID='od6'):
    fixedRow = convertRow(rowDict)
    listEntry = ListEntry()
    listEntry.from_dict(fixedRow)
    client.add_list_entry(listEntry, sheetKey, sheetID)
