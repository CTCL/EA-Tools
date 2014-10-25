from bs4 import BeautifulSoup
from requests import Session


def getValues(row):
    fname = row['tsmart_first_name']
    lname = row['tsmart_last_name']
    dobStr = row['voterbase_dob']
    dob = '{0}/{1}/{2}'.format(int(dobStr[4:6]), int(dobStr[6:8]),
                               int(dobStr[:4]))
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
        fields[item.get('name')] = item.get('value')
    for item in form.find_all('input', {'type': 'hidden'}):
        fields[item.get('name')] = item.get('value')
    fields['hiddenInputToUpdateATBuffer_CommonToolkitScripts'] = '1'
    fields['ctl00$pnlMenu_CollapsiblePanelExtender_ClientState'] = 'true'
    fields['ctl00$AccordionStateBoardMenu_AccordionExtender_ClientState'] = 0
    fields['ctl00$mtbSearch'] = ''
    return fields


def query(fname, lname, dob, fields, formURL, session):
    baseName = 'ctl00$MainContent$'
    fields[baseName + 'txtNameFirst'] = fname
    fields[baseName + 'txtNameLast'] = lname
    fields[baseName + 'txtDob'] = dob
    fields[baseName + 'btnSubmit'] = 'Submit'
    response = session.post(formURL, data=fields)
    html = response.text.replace('<br />', '***').replace(u'\u2014', '-')
    return html


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
