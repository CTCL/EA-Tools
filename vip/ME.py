from bs4 import BeautifulSoup
import requests
import Levenshtein
import re


def getPollingPlace(soup):
    ppid = ''
    address = ''
    name = ''
    mapURL = soup.find('a', {'href': re.compile('gmaps')}).get('href')
    args = mapURL.split('?')[1].split('&')
    for item in args:
        kwargs = item.split('=')
        if kwargs[0] == 'address':
            address = kwargs[1]
        if kwargs[0] == 'name':
            name = kwargs[1]
    return ppid, name, address


def getValues(row):
    address = '{0} {1} {2} {3}'
    street = address.format(row['vf_reg_cass_pre_directional'],
                            row['vf_reg_cass_street_name'],
                            row['vf_reg_cass_street_suffix'],
                            row['vf_reg_cass_post_directional'])
    num = row['vf_reg_cass_street_num']
    city = row['vf_reg_cass_city']
    address = address.replace('     ', ' ').replace('    ', ' ')
    address = address.replace('   ', ' ').replace('  ', ' ')
    return street, num, city


def getCities(soup):
    cities = {}
    select = soup.find('select', {'name': 'voter_lookup_town'})
    for item in select.find_all('option'):
        cities[item.text.strip().upper()] = item.get('value')
    return cities


def verifyCity(cities, city):
    maximum = 0
    city = str(city.upper())
    optionList = []
    for option in cities:
        text = str(option.strip().upper())
        value = cities[option]
        score = Levenshtein.ratio(city, text)
        maximum = max(maximum, score)
        optionList.append((score, value))
    for option in optionList:
        if maximum == option[0]:
            return str(option[1])


def run(row):
    url = 'http://www.maine.gov/portal/government/edemocracy/lookup_voter_info'
    street, num, city = getValues(row)
    try:
        form = BeautifulSoup(requests.get(url).text)
        cities = getCities(form)
        cityValue = verifyCity(cities, city)
        url += '_results'
        payload = {'number': num, 'street': street, 'town': cityValue}
        response = requests.get(url, params=payload)
        return getPollingPlace(BeautifulSoup(response.text))
    except Exception as inst:
        print inst
        return '', '', ''
