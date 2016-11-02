from bs4 import BeautifulSoup
from requests import Session
import Levenshtein
import json


def getValues(row):
    num = row['vf_reg_cass_street_num']
    predir = row['vf_reg_cass_pre_directional']
    name = row['vf_reg_cass_street_name']
    suffix = row['vf_reg_cass_street_suffix']
    postdir = row['vf_reg_cass_post_directional']
    county = row['vf_county_name']
    return num, predir, name, suffix, postdir, county


def getHiddenValues(form):
    fields = {}
    for item in form.find_all('input', {'type': 'hidden'}):
        fields[item.get('name')] = item.get('value')
    return fields


def getCounties(soup):
    counties = {}
    selectName = 'ctl00$ContentPlaceHolder1$usrCounty$cboCounty'
    select = soup.find('select', {'name': selectName})
    for item in select.find_all('option'):
        counties[item.text.strip().upper()] = item.get('value')
    return counties


def matchString(string, stringList):
    maximum = 0
    string = str(string.strip().upper())
    optionList = []
    for text in stringList:
        newstring = str(text.strip().upper())
        score = Levenshtein.ratio(string, newstring)
        maximum = max(maximum, score)
        optionList.append((score, text))
    for option in optionList:
        if maximum == option[0]:
            return str(option[1])


def processBlanks(value, replacement):
    if value == '':
        value = replacement
    return value


def getJefferson(num, predir, name, suffix, postdir):
    url = 'http://www.jeffersoncountyclerk.org/WhereDoIVote/Default.aspx'
    addrStr = '{0} {1} {2} {3} {4}'.format(num, predir, name, suffix, postdir)
    addrStr = addrStr.strip().replace('   ', ' ').replace('  ', ' ')
    session = Session()
    data = {'count': 20, 'prefixText': addrStr}
    header = {'Content-Type': 'application/json; charset=UTF-8'}
    response = session.post(url + '/GetAddress', data=json.dumps(data),
                            headers=header)
    data = json.loads(response.text)
    addresses = data['d']
    address = matchString(addrStr, addresses)
    html = session.get(url).text
    fields = getHiddenValues(BeautifulSoup(html).find('form'))
    fields['txtStreet'] = address
    fields['cmdDisplay'] = 'Search'
    response = session.post(url, data=fields)
    soup = BeautifulSoup(response.text)
    name = ''
    address = ''
    ppid = ''
    nameLabel = soup.find('span', {'id': 'lblLocation'})
    addressLabel = soup.find('span', {'id': 'lblAddress'})
    if nameLabel is not None:
        name = nameLabel.string.strip()
    if addressLabel is not None:
        address = addressLabel.string.strip()
        address += ' LOUISVILLE, KY'
    return ppid, name, address


def getFayette(num, predir, name, suffix):
    url = 'https://www.fayettecountyclerk.com/web/elections/votingLocationsResults.htm'
    session = Session()
    fields = {'streetInNumber': num, 'streetInDir': predir,
              'streetInName': name, 'streetInType': suffix}
    response = session.post(url, data=fields)
    soup = BeautifulSoup(response.text)
    table = soup.find('table', {'cellpadding': '2'}).find_all('tr')
    precinctDict = {}
    for row in table:
        cells = row.find_all('td')
        label = cells[0].get_text().strip()
        value = cells[1].get_text().strip()
        precinctDict[label] = value
    ppid = ''
    name = ''
    address = ''
    if 'Precinct Code:' in precinctDict:
        ppid = precinctDict['Precinct Code:'].strip()
    if 'Voting Location:' in precinctDict:
        name = precinctDict['Voting Location:']
        name = name.replace('- View on Map', '').strip()
    if 'Precinct Address:' in precinctDict:
        address = precinctDict['Precinct Address:'].strip()
    if 'Precinct Zip Code:' in precinctDict:
        address += ' LEXINGTON, KY '
        address += precinctDict['Precinct Zip Code:'].strip()
    return ppid, name, address


def run(row):
    num, predir, name, suffix, postdir, county = getValues(row)
    try:
        if county.upper() == 'JEFFERSON':
            pollingInfo = getJefferson(num, predir, name, suffix, postdir)
        elif county.upper() == 'FAYETTE':
            pollingInfo = getFayette(num, predir, name, suffix)
        else:
            return '', '', ''
        return pollingInfo
    except Exception as inst:
        print type(inst)
        print inst
        return '', '', ''
