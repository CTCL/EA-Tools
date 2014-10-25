from bs4 import BeautifulSoup
from requests import Session
import Levenshtein
import re
import json


def getValues(row):
    num = row['vf_reg_cass_street_num']
    predir = row['vf_reg_cass_pre_directional']
    name = row['vf_reg_cass_street_name']
    suffix = row['vf_reg_cass_street_suffix']
    postdir = row['vf_reg_cass_post_directional']
    city = row['vf_reg_cass_city']
    zipcode = row['vf_reg_cass_zip']
    county = row['vf_county_name']
    date = str(row['voterbase_dob'])
    lastName = row['tsmart_last_name']
    firstName = row['tsmart_first_name']
    dob = ''
    if len(date) == 8:
        dob = '{0}/{1}/{2}'.format(date[4:6], date[6:8], date[:4])
    return num, predir, name, suffix, postdir, city, zipcode, county, dob, firstName, lastName


def getHiddenValues(form):
    fields = {}
    for item in form.find_all('input', {'type': 'hidden'}):
        fields[item.get('name')] = item.get('value')
    return fields


def matchString(string, stringList):
    maximum = 0
    string = str(string.strip().upper())
    optionList = []
    for text in stringList:
        newstring = str(text[0].strip().upper())
        score = Levenshtein.ratio(string, newstring)
        maximum = max(maximum, score)
        optionList.append((score, text[1]))
    for option in optionList:
        if maximum == option[0]:
            return str(option[1])


def processBlanks(value, replacement):
    if value == '':
        value = replacement
    return value


def getBexar(num, predir, name, suffix, postdir, zipcode):
    session = Session()
    url = 'http://apps.bexar.org/ElectionSearch/ElectionSearch.aspx?psearchtab=1'
    response = session.get(url)
    soup = BeautifulSoup(response.text)
    form = soup.find('form', {'id': 'form1'})
    fields = getHiddenValues(form)
    addrStr = '{0} {1} {2} {3} {4}'.format(num, predir, name, suffix, postdir)
    addrStr = addrStr.strip().replace('   ', ' ').replace('  ', ' ')
    fields['tab2street'] = addrStr
    fields['tab2zipcode'] = zipcode
    fields['btnTab2'] = 'Search'
    response = session.post(url, data=fields)
    soup = BeautifulSoup(response.text)
    results = str(soup.find('div', {'id': 'DivResultFound'}).find('h3'))
    ppid = re.sub('^.* ([Pp][Rr][Ee][Cc][Ii][Nn][Cc][Tt] [0-9A-Za-z]*) .*$',
                  '\\1', results.replace('\n', ''))
    resultList = results.split('<br/>')
    name = resultList[3].strip()
    address = resultList[4].strip()
    return ppid, name, address


def getHarris(lastName, firstName, num, name):
    url = 'http://www.harrisvotes.org/VoterBallotSearch.aspx?L=E'
    session = Session()
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    form = soup.find('form')
    fields = getHiddenValues(form)
    baseName = 'ctl00$ContentPlaceHolder1$'
    fields[baseName + 'txtLastName'] = lastName
    fields[baseName + 'txtFirstName'] = firstName
    fields[baseName + 'txtHouseNo'] = num
    fields[baseName + 'txtStreet'] = name
    fields[baseName + 'btnSearchNA'] = 'Search'
    response = session.post(url, data=fields)
    soup = BeautifulSoup(response.text, 'lxml')
    baseName = 'ctl00_ContentPlaceHolder1_GridViewA_ctl02_GridViewLocations_'
    ppid = ''
    name = soup.find('span', {'id': baseName + 'ctl02_lblLocation'}).string
    name = name.strip()
    address = soup.find('span', {'id': baseName + 'ctl02_lblPollingAddress'}).string.split(',')[0]
    address = address.strip() + ' '
    address += soup.find('span',
                         {'id': baseName + 'ctl02_lblPollingCity'}).string
    address = address.strip() + ', TX'
    return ppid, name, address


def getDallas(firstName, lastName, dob):
    url = 'http://dallas-tx.mobile.clarityelections.com/mobile/seam/resource/rest/voter/find'
    payload = {
        'VOTER_ELIGIBILITY_LOOKUP_FIRST_NAME': firstName,
        'VOTER_ELIGIBILITY_LOOKUP_LAST_NAME': lastName,
        'VOTER_ELIGIBILITY_LOOKUP_BIRTH_DATE': dob
    }
    session = Session()
    response = session.get(url, params=payload)
    text = response.text.replace('\n', '')
    text = re.sub('^null\\((.*)\\)$', '\\1', text)
    data = json.loads(text)[0]
    precinctInfo = data['precinct']
    ppid = ''
    address = ''
    if 'name' in precinctInfo:
        ppid = precinctInfo['name']
    ppInfo = precinctInfo['defaultPollingPlace']
    name = ppInfo['name']
    addrDict = ppInfo['streetAddress']
    address = '{0} {1} {2} {3}, TX {4}'.format(addrDict['address1'],
                                               addrDict['address2'],
                                               addrDict['address3'],
                                               addrDict['city'],
                                               addrDict['zip'])
    return ppid, name, address


def run(row):
    num, predir, name, suffix, postdir, city, zipcode, county, dob, firstName, lastName = getValues(row)
    try:
        if county.upper() == 'BEXAR':
            pollingInfo = getBexar(num, predir, name, suffix, postdir, zipcode)
        elif county.upper() == 'HARRIS':
            pollingInfo = getHarris(lastName, firstName, num, name)
        elif county.upper() == 'DALLAS':
            pollingInfo = getDallas(firstName, lastName, dob)
        else:
            return '', '', ''
        return pollingInfo
    except Exception as inst:
        print type(inst)
        print inst
        return '', '', ''
