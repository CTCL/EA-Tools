from bs4 import BeautifulSoup
from requests import Session
import re


def getValues(row):
    fname = row['tsmart_first_name']
    lname = row['tsmart_last_name']
    date = row['voterbase_dob']
    dob = '{0}/{1}/{2}'.format(date[4:6], date[6:8], date[:4])
    return fname, lname, dob


def getOutputValues(soup):
    ppid = ''
    name = ''
    address = ''
    span = soup.find('span', {'id': 'ctl00_MainContent_lblVoteCenters'})
    if span is not None:
        span = str(span)
        locationList = re.sub('</?span.*?>', '', span).split('<br/>')
        locationList = locationList[0:len(locationList) - 1]
        for location in locationList:
            if len(name) > 0:
                name += ';'
            if len(address) > 0:
                address += ';'
            if len(ppid) > 0:
                ppid += ';'
            pollList = location.split(',')
            city = re.sub('\\(.*$', '', pollList[2]).strip()
            ppid += re.sub('\\((.*)\\)', '\\1', pollList[2]).strip()
            name += pollList[0].strip()
            address += '{0} {1}, SD'.format(pollList[1].strip(), city)
    else:
        name = soup.find('span', {'id': 'ctl00_MainContent_lblShowName'}).string
        address = soup.find('span', {'id': 'ctl00_MainContent_lblShowAddress'}).string
        ppid = soup.find('span', {'id': 'ctl00_MainContent_lblShowPrecinct'}).string
    return ppid, name, address


def getHiddenValues(soup):
    form = soup.find('form', {'id': 'aspnetForm'})
    fields = {}
    for item in form.find_all('input', {'type': 'hidden'}):
        fields[item.get('name')] = item.get('value')
    return fields


def query(session, fname, lname, dob, fields, formURL):
    baseName = 'ctl00$MainContent$'
    fields[baseName + 'txtFirstName'] = fname
    fields[baseName + 'txtLastName'] = lname
    fields[baseName + 'txtDOB'] = dob
    fields[baseName + 'btnSearch'] = 'Search'
    response = session.post(formURL, data=fields)
    html = response.text
    return html


def run(row):
    formURL = 'https://sos.sd.gov/Elections/VIPLogin.aspx'
    session = Session()
    while True:
        try:
            fname, lname, dob = getValues(row)
            response = session.get(formURL)
            soup = BeautifulSoup(response.text, 'lxml')
            hiddenFields = getHiddenValues(soup)
            html = query(session, fname, lname, dob,
                         hiddenFields, formURL).encode('windows-1252')
            soup = BeautifulSoup(html, 'lxml')
            pollingInfo = getOutputValues(soup)
            return pollingInfo
        except Exception as inst:
            print type(inst)
            print inst
            return '', '', ''
