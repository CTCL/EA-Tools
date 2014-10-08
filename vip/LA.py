from bs4 import BeautifulSoup
from requests import Session
import Levenshtein
import json


def getResponseSoup(payload, action, session):
    baseURL = 'http://web.go-vote-tn.tnsos.net/'
    response = session.post(baseURL + action, data=payload, verify=False)
    soup = BeautifulSoup(response.text)
    return soup


def getPollingPlace(soup):
    ppid = ''
    address = ''
    name = soup.find('th', {'id': 'pollingPlace'}).text.strip()
    for item in soup.find_all('td', {'headers': 'pollingPlace'}):
        if len(address) > 0:
            address += ' '
        address += item.text.strip()
    return ppid, name, address


def getValues(row):
    address = '{0} {1} {2} {3} {4}'
    address = address.format(row['vf_reg_cass_street_num'],
                             row['vf_reg_cass_pre_directional'],
                             row['vf_reg_cass_street_name'],
                             row['vf_reg_cass_street_suffix'],
                             row['vf_reg_cass_post_directional'])
    zipCode = '{:05d}'.format(int(row['vf_reg_cass_zip']))
    apt = row['vf_reg_cass_apt_num']
    city = row['vf_reg_cass_city']
    address = address.replace('     ', ' ').replace('    ', ' ')
    address = address.replace('   ', ' ').replace('  ', ' ')
    return address, zipCode, apt, city


def verifyCity(cities, city):
    maximum = 0
    city = str(city.upper())
    optionList = []
    for option in cities:
        text = str(option.strip().upper())
        score = Levenshtein.ratio(city, text)
        maximum = max(maximum, score)
        optionList.append((score, text))
    for option in optionList:
        if maximum == option[0]:
            return str(option[1])


def run(row):
    agent1 = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
    agent2 = '(KHTML, like Gecko) Chrome/37.0.2062.120 Safari/537.36'
    headers = {
        'Host': 'voterportal.sos.la.gov',
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Origin': 'https://voterportal.sos.la.gov',
        'X-Requested-With': 'XMLHttpRequest',
        'Content-Type': 'application/json; charset=UTF-8',
        'User-Agent': '{0} {1}'.format(agent1, agent2)
    }
    try:
        baseURL = 'https://voterportal.sos.la.gov'
        session = Session()
        session.get(baseURL)
        action = '/address.aspx'
        response = session.get(baseURL + action)
        soup = BeautifulSoup(response.text)
        address, zipCode, apt, city = getValues(row)
        action = '/default.aspx/GetCities'
        payload = {'zipCode': zipCode}
        response = session.post(baseURL + action, headers=headers,
                                data=json.dumps(payload))
        cities = []
        cityObject = json.loads(response.text)['d']
        for item in cityObject:
            cities.append(item['CityName'])
        city = verifyCity(cities, city)
        action = '/services/AddressLookup.ashx'
        session.get(baseURL + action, params={'zipCode': zipCode,
                                              'query': address})
        action = '/Default.aspx/VoterAddressSearch'
        payload = {'address': address, 'city': city, 'zipCode': zipCode}
        response = session.post(baseURL + action, headers=headers,
                                data=json.dumps(payload))
        headers['Cache-Control'] = 'max-age=0'
        voterID = json.loads(response.text)['d'][0]['VoterAddressId']
        payload = {
            'ctl00$cphBase$txtAddressZipCode': zipCode,
            'ctl00$cphBase$txtAddress1': address,
            'ctl00$cphBase$txtAddress2': apt,
            'ctl00$cphBase$cboCity': city
        }
        for item in soup.find_all('input', {'type': 'hidden'}):
            payload[item.get('name')] = item.get('value')
        payload['ctl00$cphBase$hdnAddressId'] = voterID
        action = '/address.aspx'
        response = session.post(baseURL + action, data=payload)
        with open('/home/michael/Desktop/output1.html', 'w') as outFile:
            outFile.write(response.text.replace(u'\xa9', ''))
        response = session.get(baseURL + '/home.aspx',
                               params={'galogin': 'address'})
        action = '/location/Pollplace.aspx'
        payload = {'l': 'pl'}
        response = session.get(baseURL + action, params=payload)
        soup = BeautifulSoup(response.text)
        return getPollingPlace(soup)
    except Exception as inst:
        print inst
        return '', '', ''
