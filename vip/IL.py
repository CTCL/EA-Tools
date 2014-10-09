from bs4 import BeautifulSoup
from requests import Session


def getValues(row):
    fname = row['tsmart_first_name']
    lname = row['tsmart_last_name']
    zipCode = row['vf_reg_cass_zip']
    return fname, lname, zipCode


def getOutputValues(soup):
    ppid = ''
    name = ''
    street1 = ''
    street2 = ''
    city = ''
    zipCode = ''
    IDBase = 'ctl00_ContentPlaceHolder1_registrationLookup_lblPollingPlace'
    name = soup.find('span', {'id': IDBase + 'Name'}).string
    street1 = soup.find('span', {'id': IDBase + 'AddressLine1'}).string
    street2Soup = soup.find('span', {'id': IDBase + 'AddressLine2'})
    if street2Soup is not None:
        street2 = street2Soup.text
    city = soup.find('span', {'id': IDBase + 'AddressCity'}).string
    zipCode = soup.find('span', {'id': IDBase + 'AddressZipCode'}).string
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


def query(session, fname, lname, zipCode, fields, formURL):
    baseName = 'ctl00$ContentPlaceHolder1$registrationLookup$'
    fields[baseName + 'txtFirstName'] = fname
    fields[baseName + 'txtLastName'] = lname
    fields[baseName + 'txtZIPCode'] = zipCode
    fields[baseName + 'btnSubmit'] = 'Submit'
    response = session.post(formURL, data=fields)
    html = response.text.replace(u'\xa0', ' ').encode('utf-8')
    return html


def run(row):
    formURL = 'http://www.elections.il.gov/votinginformation'
    formURL += '/registrationlookup.aspx'
    session = Session()
    while True:
        try:
            fname, lname, zipCode = getValues(row)
            response = session.get(formURL)
            hiddenFields = getHiddenValues(BeautifulSoup(response.text))
            html = query(session, fname, lname, zipCode, hiddenFields, formURL)
            soup = BeautifulSoup(html)
            pollingInfo = getOutputValues(soup)
            return pollingInfo
        except Exception as inst:
            print type(inst)
            print inst
            return '', '', ''
