from bs4 import BeautifulSoup
from requests import Session
import Levenshtein
import re
import json
import time


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


def getEPaDC(num, predir, name, suffix, postdir, city, zipcode, url):
    city = city.upper()
    session = Session()
    url = 'http://{0}/mobile/seam/resource/rest/precinct/'.format(url)
    addrStr = '{0} {1} {2} {3} {4} {5} {6}'.format(num, predir, name, suffix,
                                                   postdir, city, zipcode)
    data = {
        'PRECINCT_FINDER_ADDRESS_NUMBER': num,
        'PRECINCT_FINDER_STREET_NAME': name,
        'PRECINCT_FINDER_APARTMENT_NUMBER': '',
        'PRECINCT_FINDER_CITY': city,
        'lang': 'en'
    }
    response = session.get(url + 'findstreet', params=data)
    addrData = json.loads(response.text)
    addresses = addrData['streets']
    addrList = []
    for item in addresses:
        addr = '{0} {1} {2} {3} {4} {5} {6}'.format(item['address'],
                                                    item['predir'],
                                                    item['street'],
                                                    item['type'],
                                                    item['postdir'],
                                                    item['city'],
                                                    item['zipcode'])
        addrList.append((addr, item['precinct']))
    precinct = matchString(addrStr, addrList)
    data = {
        'precinctId': precinct,
        'lang': 'en'
    }
    response = session.get(url + 'precinctdetail', params=data)
    precinctData = json.loads(response.text)
    ppid = ''
    if 'precinctName' in precinctData:
        ppid = precinctData['precinctName']
    ppInfo = precinctData['electionPrecincts'][0]['pollingPlace']
    name = ppInfo['name']
    addrDict = ppInfo['streetAddress']
    address = '{0} {1} {2}, TX {3}'.format(addrDict['address1'],
                                           addrDict['address2'],
                                           addrDict['city'],
                                           addrDict['zip'])
    return ppid, name, address


def getHidalgo(firstName, lastName, dob):
    url = 'http://apps.co.hidalgo.tx.us/VoterLookup/Lookup/Results'
    year = dob[6:]
    session = Session()
    data = {'LastName': lastName, 'FirstName': firstName, 'DOBYear': year}
    response = session.post(url, data=data)
    soup = BeautifulSoup(response.text)
    pageDict = {}
    for item in soup.find_all('div'):
        label = item.find('span', {'class': 'field-label'})
        value = item.find('span', {'class': 'field-value'})
        if label is not None and value is not None:
            for string in value.strings:
                pageDict[label.get_text().strip()] = string.strip()
                break
    ppid = ''
    name = ''
    address = ''
    if 'Precinct' in pageDict:
        ppid = pageDict['Precinct']
    if 'Location:' in pageDict:
        name = pageDict['Location:']
    if 'Address:' in pageDict:
        address = pageDict['Address:']
    if 'City:' in pageDict:
        address += ' ' + pageDict['City:']
    address += ' TX'
    return ppid, name, address


def getFBC(firstName, lastName, dob):
    listURL = 'http://www.fortbendcountytx.gov/index.aspx?page=1099'
    formURL = 'https://progprod.co.fort-bend.tx.us/Voter/default.aspx'
    session = Session()
    response = session.get(listURL)
    soup = BeautifulSoup(response.text)
    siteDict = {}
    tables = soup.find_all('table', {'id': re.compile('ctl00_listDataGrid_')})
    for table in tables:
        header = table.find('td', {'class': 'facility_header_cell'})
        values = header.string.split('|')
        name = values[0].strip()
        link = table.find('a', {'id': re.compile('googleMapHyperLink')})
        address = ' '.join(link.strings)
        location = {'name': name, 'address': address}
        for i in range(1, len(values)):
            siteDict[values[i].strip()] = location
    response = session.get(formURL, verify=False)
    formURL = response.url
    soup = BeautifulSoup(response.text)
    fields = getHiddenValues(soup.find('form'))
    fields['voterLname'] = lastName
    fields['voterFname'] = firstName
    fields['voterDOB'] = dob
    fields['sS'] = 'Start Search'
    fields['type'] = 'voterLname'
    fields['type1'] = 'voterCNumber'
    fields['voterDate'] = 'null'
    fields['voterCNumber'] = ''
    fields['formFirstName'] = ''
    fields['formLastName'] = ''
    response = session.post(formURL, data=fields, verify=False)
    soup = BeautifulSoup(response.text)
    ppid = soup.find('span', {'id': 'Precinct'}).string.strip()
    name = ''
    address = ''
    if ppid in siteDict:
        location = siteDict[ppid]
        name = location['name']
        address = location['address']
    return ppid, name, address


def getMontgomery(firstName, lastName, dob):
    ppid = ''
    name = ''
    address = ''
    session = Session()
    url = 'http://www.mctx.org/electioninfo/voterlookupresult.aspx?curLang=English'
    session.get(url)
    data = {
        'LNAME': lastName,
        'FNAME': firstName,
        'DOBM': dob[:2],
        'DOBD': dob[3:5],
        'DOBY': dob[6:],
        'SUBMIT1': 'Search'
    }
    response = session.post(url, data=data)
    soup = BeautifulSoup(response.text)
    table = soup.find('table', {'id': 'dgrElectionsNew'})
    link = table.find('a', {'href': re.compile('drvDirectionsNew')})
    name = table.find_all('tr')[1].find_all('td')[4].get_text()
    infoURL = link.get('href').replace('..', 'http://www.mctx.org')
    response = session.get(infoURL)
    soup = BeautifulSoup(response.text)
    location = soup.find('font', {'size': '4'})
    lList = []
    for line in location.strings:
        lList.append(line.strip())
    address = ''
    for i in range(1, len(lList) - 1):
        if len(address) > 0:
            address += ' '
        address += lList[i]
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
        elif county.upper() == 'EL PASO':
            url = 'www.epcountyvotes.com/ce'
            pollingInfo = getEPaDC(num, predir, name, suffix, postdir, city,
                                   zipcode, url)
        elif county.upper() == 'DENTON':
            url = 'www.votedenton.com/ce'
            pollingInfo = getEPaDC(num, predir, name, suffix, postdir, city,
                                   zipcode, url)
        elif county.upper() == 'HIDALGO':
            pollingInfo = getHidalgo(firstName, lastName, dob)
        elif county.upper() == 'FORT BEND':
            pollingInfo = getFBC(firstName, lastName, dob)
        elif county.upper() == 'MONTGOMERY':
            pollingInfo = getMontgomery(firstName, lastName, dob)
        elif county.upper() == 'JEFFERSON':
            url = 'jefferson-tx.mobile.clarityelections.com'
            pollingInfo = getEPaDC(num, predir, name, suffix, postdir, city,
                                   zipcode, url)
        else:
            return '', '', ''
        return pollingInfo
    except Exception as inst:
        print type(inst)
        print inst
        return '', '', ''
