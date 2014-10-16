from bs4 import BeautifulSoup
from requests import Session
import re


def getValues(row):
    fname = row['tsmart_first_name']
    lname = row['tsmart_last_name']
    zipCode = row['vf_reg_cass_zip']
    dobStr = row['voterbase_dob']
    dob = '{0}/{1}/{2}'.format(int(dobStr[4:6]), int(dobStr[6:8]),
                               int(dobStr[:4]))
    return fname, lname, zipCode, dob


def getOutputValues(soup):
    ppid = ''
    name = ''
    street1 = ''
    street2 = ''
    city = ''
    zipCode = ''
    IDBase = 'ctl00_ContentPlaceHolder1_registrationLookup_lblPollingPlace'
    name = soup.find('span', {'id': IDBase + 'Name'}).string
    street1tag = soup.find('span', {'id': IDBase + 'AddressLine1'})
    street2tag = soup.find('span', {'id': IDBase + 'AddressLine2'})
    citytag = soup.find('span', {'id': IDBase + 'AddressCity'})
    ziptag = soup.find('span', {'id': IDBase + 'AddressZipCode'})
    street1 = ''
    street2 = ''
    city = ''
    zipCode = ''
    if street1tag is not None:
        street1 = street1tag.string
    if street2tag is not None:
        street2 = street2tag.string
    if citytag is not None:
        city = citytag.string
    if ziptag is not None:
        zipCode = ziptag.string
    address = '{0} {1} {2}, IL {3}'.format(street1.strip(), street2.strip(),
                                           city.strip(), zipCode)
    return ppid, name, address


def getHiddenValues(soup):
    form = soup.find('form', {'name': 'aspnetForm'})
    fields = {}
    for item in form.find_all('input', {'type': 'hidden'}):
        fields[item.get('name')] = item.get('value')
    fields['hiddenInputToUpdateATBuffer_CommonToolkitScripts'] = '1'
    fields['ctl00$pnlMenu_CollapsiblePanelExtender_ClientState'] = 'true'
    fields['ctl00$AccordionStateBoardMenu_AccordionExtender_ClientState'] = 0
    fields['ctl00$mtbSearch'] = ''
    return fields


def query(session, fname, lname, zipCode, fields, dob, formURL):
    baseName = 'ctl00$ContentPlaceHolder1$registrationLookup$'
    fields[baseName + 'txtFirstName'] = fname
    fields[baseName + 'txtLastName'] = lname
    fields[baseName + 'txtZIPCode'] = zipCode
    fields[baseName + 'btnSubmit'] = 'Submit'
    response = session.post(formURL, data=fields)
    html = response.text.replace(u'\xa0', ' ').encode('utf-8')
    if re.search("We've found multiple voters with your name and ZIP code",
                 html):
        fields = getHiddenValues(BeautifulSoup(response.text))
        fields[baseName + 'txtBirthDate'] = dob
        fields[baseName + 'btnSubmit'] = 'Submit'
        response = session.post(formURL, data=fields)
        html = response.text
    return html


def run(row):
    formURL = 'http://www.elections.il.gov/votinginformation'
    formURL += '/registrationlookup.aspx'
    session = Session()
    while True:
        try:
            fname, lname, zipCode, dob = getValues(row)
            response = session.get(formURL)
            hiddenFields = getHiddenValues(BeautifulSoup(response.text))
            html = query(session, fname, lname, zipCode,
                         hiddenFields, dob, formURL)
            soup = BeautifulSoup(html)
            pollingInfo = getOutputValues(soup)
            return pollingInfo
        except Exception as inst:
            print type(inst)
            print inst
            return '', '', ''
