from bs4 import BeautifulSoup
from requests import Session
import json


def getValues(row):
    fname = row['tsmart_first_name']
    lname = row['tsmart_last_name']
    dobStr = row['voterbase_dob']
    dob = '{0}/{1}/{2}'.format(dobStr[4:6], dobStr[6:8], dobStr[:4])
    return fname, lname, dob


def getOutputValues(soup):
    ppid = ''
    address = ''
    table = soup.find('table', {'id': 'tableResults'}).find_all('tr')
    row = table[2]
    values = row.find_all('td')[3].get_text().split('***')
    name = values[0].strip()
    for i in range(1, len(values)):
        if len(address) > 0:
            address += ' '
        address += values[i].strip()
    return ppid, name, address


def getHiddenValues(soup):
    form = soup.find('form', {'name': 'Form1'})
    fields = {}
    manualhide = form.find('div', {'class': 'displayNone printNone'})
    for item in manualhide.find_all('input'):
        value = item.get('value')
        if value is not None:
            fields[item.get('name')] = value
        else:
            fields[item.get('name')] = ''
    for item in form.find_all('input', {'type': 'hidden'}):
        fields[item.get('name')] = item.get('value')
    fields['__EVENTTARGET'] = ''
    fields['__EVENTARGUMENT'] = ''
    return fields


def query(fname, lname, dob, fields, formURL, session):
    baseName = 'ctl00$MainContent$'
    fields[baseName + 'txtNameFirst'] = fname
    fields[baseName + 'txtNameLast'] = lname
    fields[baseName + 'txtDob'] = dob
    fields[baseName + 'btnSearch'] = 'Submit'
    with open('/home/michael/Desktop/output.json', 'w') as outFile:
        outFile.write(json.dumps(fields, indent=4))
    response = session.post(formURL, data=fields)
    html = response.text
    return html.replace(u'\u2014', '-')  # .replace('<br />', '***')


def run(row):
    formURL = 'https://apps.sos.wv.gov/elections/voter/find-polling-place.aspx'
    try:
        session = Session()
        fname, lname, dob = getValues(row)
        response = session.get(formURL)
        soup = BeautifulSoup(response.text)
        hiddenFields = getHiddenValues(soup)
        html = query(fname, lname, dob, hiddenFields, formURL, session)
        with open('/home/michael/Desktop/output.html', 'w') as outFile:
            outFile.write(html)
        soup = BeautifulSoup(html)
        pollingInfo = getOutputValues(soup)
        return pollingInfo
    except Exception as inst:
        print type(inst)
        print inst
        return '', '', ''
