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
        name = county.text.upper().replace('_', ' ')
        code = county.get('value')
        countyDict[name] = code
    return countyDict


def generatePayload(county, houseNum, preDir, street, suffix,
                    postDir, zipCode, hiddenFields, counties):
    payload = {
        'selectSearchCriteria': '2',
        'action': 'Search',
        'search': 'Search',
        'county': counties[county.upper()],
        'houseNumber': houseNum,
        'streetDirection': preDir,
        'streetName': street,
        'streetType': suffix,
        'streetSuffix': postDir,
        'zipcode': zipCode
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
                                            ).replace('   ', ' '
                                                      ).replace('  ', ' ')
    return ppid, name, address


def getValues(row):
    county = row['vf_county_name']
    houseNum = row['vf_reg_cass_street_num']
    preDir = row['vf_reg_cass_pre_directional']
    street = row['vf_reg_cass_street_name']
    suffix = row['vf_reg_cass_street_suffix']
    postDir = row['vf_reg_cass_post_directional']
    zipCode = row['vf_reg_cass_zip']
    return county, houseNum, preDir, street, suffix, postDir, zipCode


def run(row):
    county, houseNum, preDir, street, suffix, postDir, zipCode = getValues(row)
    baseURL = 'https://voter.azsos.gov'
    form = getFormSoup(baseURL + '/VoterView/PollingPlaceSearch.do')
    hiddenFields, action = getHiddenFields(form)
    counties = getCounties(form)
    payload = generatePayload(county, houseNum, preDir, street, suffix,
                              postDir, zipCode, hiddenFields, counties)
    response = getResponseSoup(payload, baseURL + action)
    pollingInfo = getPollingPlace(response)
    return pollingInfo
