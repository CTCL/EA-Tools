from bs4 import BeautifulSoup
import urllib2
import re
import requests


def getFormSoup(url):
    response = urllib2.urlopen(url)
    soup = BeautifulSoup(response.read())
    return soup


def getCounties(soup):
    countyDict = {}
    countySelector = soup.find('select', {'name': 'county'})
    countyOptions = countySelector.find_all('option')
    for county in countyOptions:
        name = county.text
        code = county.get('value')
        countyDict[name] = code
    return countyDict


def generatePayload(county, addrStr, zipcode, counties):
    payload = {
        'action': 'Search',
        'countyRequired': 'true',
        'selectSearchCriteria': '2',
        'county': counties[county.upper()],
        'electionCombo': '20726_200000',
        'nameLast': '',
        'dobMonth': '0',
        'dobDay': '0',
        'dobYear': '0',
        'voterId': '',
        'DLN': '',
        'address': addrStr,
        'zipcode': zipcode,
        'search': 'Search'
    }
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
        if 'Ballot Style' in pollingDict:
            ppid = pollingDict['Ballot Style']
        if 'Address' in pollingDict:
            street = pollingDict['Address']
        if 'City' in pollingDict:
            city = pollingDict['City']
        address = '{0} {1}, {2} {3}'.format(street, city, 'NM', zip
                                            ).replace('   ', ' '
                                                      ).replace('  ', ' ')
    return ppid, name, address


def getValues(row):
    county = row['vf_county_name']
    num = row['vf_reg_cass_street_num']
    predir = row['vf_reg_cass_pre_directional']
    name = row['vf_reg_cass_street_name']
    suffix = row['vf_reg_cass_street_suffix']
    postdir = row['vf_reg_cass_post_directional']
    zipcode = row['vf_reg_cass_zip']
    addrStr = '{0} {1} {2} {3} {4}'.format(num, predir, name, suffix, postdir)
    addrStr.strip().replace('   ', ' ').replace('  ', ' ')
    return county, addrStr, zipcode


def run(row):
    county, addrStr, zipcode = getValues(row)
    baseURL = 'https://voterview.state.nm.us/VoterView/PollingPlaceSearch.do'
    form = getFormSoup(baseURL)
    counties = getCounties(form)
    payload = generatePayload(county, addrStr, zipcode, counties)
    response = getResponseSoup(payload, baseURL)
    pollingInfo = getPollingPlace(response)
    return pollingInfo
