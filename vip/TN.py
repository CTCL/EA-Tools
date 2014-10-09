from bs4 import BeautifulSoup
from requests import Session
import Levenshtein


def getPollingPlace(soup):
    ppid = ''
    address = ''
    name = ''
    pollingInfo = soup.find('div', {'class': 'locationInfo'})
    if pollingInfo.find('h3') is not None:
        name = pollingInfo.find('h3').text.strip()
    for paragraph in pollingInfo.find_all('p'):
        if paragraph.find('label').text == 'Address:':
            for span in paragraph.find_all('span'):
                if len(address) != 0:
                    address += ' '
                address += str(span.text)
    return ppid, name, address


def getValues(row):
    address = '{0} {1} {2} {3} {4}'
    address = address.format(row['vf_reg_cass_street_num'],
                             row['vf_reg_cass_pre_directional'],
                             row['vf_reg_cass_street_name'],
                             row['vf_reg_cass_street_suffix'],
                             row['vf_reg_cass_post_directional'])
    zipCode = '{:05d}'.format(int(row['vf_reg_cass_zip']))
    address = address.replace('     ', ' ').replace('    ', ' ')
    address = address.replace('   ', ' ').replace('  ', ' ')
    return address, zipCode


def verifyAddress(soup, address):
    maximum = 0
    options = soup.find_all('option')
    address = str(address.upper())
    optionList = []
    for option in options:
        text = str(option.text.strip().upper())
        score = Levenshtein.ratio(address, text)
        maximum = max(maximum, score)
        optionList.append((score, option.get('value')))
    for option in optionList:
        if maximum == option[0]:
            return {'selected_voter': str(option[1])}


def run(row):
    try:
        baseURL = 'http://web.go-vote-tn.tnsos.net'
        session = Session()
        address, zipCode = getValues(row)
        action = '/search/address'
        payload = {'address': address, 'zip': zipCode}
        response = session.post(baseURL + action, data=payload)
        soup = BeautifulSoup(response.text)
        action = '/search/select-voter'
        payload = verifyAddress(soup, address)
        session.post(baseURL + action, data=payload)
        session.get(baseURL + '/locations')
        payload = {'type': 'election-day'}
        action = '/locations/list'
        response = session.get(baseURL + action, params=payload)
        soup = BeautifulSoup(response.text, 'lxml')
        return getPollingPlace(soup)
    except Exception as inst:
        print inst
        return '', '', ''
