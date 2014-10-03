from bs4 import BeautifulSoup
import urllib2
import re
import requests


def getFormSoup(url):
    response = urllib2.urlopen(url)
    soup = BeautifulSoup(response.read())
    return soup


def getHiddenFields(soup):
    form = soup.find('form', {'name': 'pollingPlaceSearchForm'})
    action = form.get('action')
    hiddenFields = form.find_all('input',
                                 {re.compile('[Tt][Ty][Pp][Ee]'):
                                  re.compile('[Hh][Ii][Dd][Dd][Ee][Nn]')})
    fieldDict = {}
    for field in hiddenFields:
        fieldDict[field.get('name')] = field.get('value')
    return fieldDict, action


def getCounties(soup):
    countyDict = {}
    countySelector = soup.find('select', {'name': 'county'})
    countyOptions = countySelector.find_all('option')
    for county in countyOptions:
        name = county.text
        code = county.get('value')
        countyDict[name] = code
    return countyDict


def generatePayload(county, lastName, dob, hiddenFields, counties):
    day = '{:02d}'.format(int(re.sub('^.*/(.*)/.*$', '\\1', dob)))
    month = '{:02d}'.format(int(re.sub('^(.*)/.*/.*', '\\1', dob)))
    year = re.sub('.*/.*/(.*)', '\\1', dob)
    cname = county.upper().replace('DE KALB', 'DEKALB')
    cname = cname.replace('SAINT ', 'ST_').replace(' ', '_')
    payload = {
        'nameLast': lastName,
        'county': counties[county.upper().replace('DE KALB', 'DEKALB').replace(
            'SAINT ', 'ST_').replace(' ', '_')],
        'dobMonth': month,
        'dobDay': day,
        'dobYear': year,
        'selectSearchCriteria': '1'
    }
    payload = dict(payload.items() + hiddenFields.items())
    payload['action'] = 'Search'
    return payload


def getResponseSoup(payload, url):
    response = requests.post(url, data=payload, verify=False)
    soup = BeautifulSoup(response.text)
    return soup


def getPollingPlace(soup):
    pollingPlaces = soup.find_all('div', {'id': 'polling-place'}, 'lxml')
    ppid = ''
    address = ''
    name = ''
    if len(pollingPlaces) > 0:
        defaultPP = pollingPlaces[len(pollingPlaces) - 1]
        labels = defaultPP.find_all('span', {'class': 'label'})
        data = defaultPP.find_all('span', {'class': 'data'})
        pollingDict = {}
        zip = ''
        street = ''
        city = ''
        for i in range(0, len(labels)):
            if re.search('Zip', labels[i].text):
                zip = data[i].text
            else:
                pollingDict[labels[i].text] = data[i].text
        name = pollingDict['Name']
        if 'Address' in pollingDict:
            street = pollingDict['Address']
        if 'City' in pollingDict:
            city = pollingDict['City']
        address = '{0} {1}, {2} {3}'.format(street, city, 'AL', zip
                                            ).replace('     ', ' '
                                                      ).replace('    ', ' ')
    return ppid, name, address


def getValues(row):
    county = row['COUNTYNAME']
    lastName = row['LASTNAME']
    dob = row['BIRTHDATE']
    return county, lastName, dob


def run(row):
    county, lastName, dob = getValues(row)
    baseURL = 'https://myinfo.alabamavotes.gov'
    form = getFormSoup(baseURL + '/VoterView/PollingPlaceSearch.do')
    hiddenFields, action = getHiddenFields(form)
    counties = getCounties(form)
    payload = generatePayload(county, lastName, dob, hiddenFields, counties)
    response = getResponseSoup(payload, baseURL + action)
    pollingInfo = getPollingPlace(response)
    return pollingInfo
