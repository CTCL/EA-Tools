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
    return num, predir, name, suffix, postdir, city, zipcode, county


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


def precinctFinder(url, num, predir, name, suffix, postdir, city, zipcode, eid):
    session = Session()
    action = 'precinctfinder.aspx'
    fixedpredir = processBlanks(predir, '--')
    fixedsuffix = processBlanks(suffix, '--')
    fixedpostdir = processBlanks(postdir, '--')
    response = session.get(url + action)
    soup = BeautifulSoup(response.text)
    form = soup.find('form', {'name': 'Form1'})
    fields = getHiddenValues(form)
    fields['txtAddressNumber'] = num
    fields['ddPreDirection'] = fixedpredir
    fields['txtStreetName'] = name
    fields['ddStreetType'] = fixedsuffix
    fields['ddPostDirection'] = fixedpostdir
    fields['btnLocatePrecinct'] = 'Locate Precinct'
    response = session.post(url + action, data=fields)
    html = response.text.encode('Windows-1252')
    soup = BeautifulSoup(html, 'lxml')
    addrStr = '{0} {1} {2} {3} {4} {5} {6}'
    addrStr = addrStr.format(num, predir, name, suffix, postdir, city, zipcode)
    addrStr = addrStr.replace('   ', ' ').replace('  ', ' ')
    values = []
    for item in soup.find_all('label'):
        field = item.find('input')
        if field is not None:
            value = field.get('value')
            address = item.get_text().replace('\n', ' ').replace('\t', ' ')
            address = address.replace('     ', ' ').replace('     ', ' ')
            address = address.replace('    ', ' ').replace('  ', ' ')
            address = re.sub('[Pp]recinct.*$', '', address).replace('  ', ' ')
            print address
            values.append((address, value))
    finalStr = matchString(addrStr, values)
    precinct = re.sub('^.*PrecinctID=(.*)$', '\\1', finalStr)
    data = {'PrecinctID': precinct, 'eid': eid}
    action = 'PollingPlace.aspx'
    response = session.get(url + action, params=data)
    soup = BeautifulSoup(response.text.replace('<br />', ' '))
    name = soup.find('span', {'id': 'ppControl_lblName'}).string
    address = soup.find('span', {'id': 'ppControl_lblAddress1'}).string
    ppid = ''
    return ppid, name, address


def voterFocus(num, predir, name, suffix, postdir, city, zipcode, fullcounty):
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    url = 'http://www.voterfocus.com/findmyprecinct/asmx/service2.asmx/'
    action = 'GetAddress2'
    session = Session()
    data = {'CurCounty': fullcounty, 'CurStreetText': name,
            'CurStreetNumber': num}
    response = session.post(url + action, headers=headers,
                            data=json.dumps(data))
    dictList = json.loads(json.loads(response.text)['d'])
    fields = {}
    for item in dictList:
        sdir = item['Street_Dir'].upper().strip()
        stype = item['Street_Type'].upper().strip()
        dsuffix = item['Street_Dir_Suffix'].upper().strip()
        szip = item['Street_ZipCode'].strip()
        if sdir == predir and stype == suffix and dsuffix == postdir and szip == zipcode:
            fields = item
            break
    fields['CurCounty'] = fullcounty
    fields['Street_Number'] = num
    action = 'GetPrecincts'
    response = session.post(url + action, headers=headers,
                            data=json.dumps(fields))
    ppInfo = json.loads(json.loads(response.text)['d'])[0]
    name = ppInfo['place_name'].strip()
    address = '{0} {1} {2} {3} {4} {5} {6}, FL {7}'
    address = address.format(ppInfo['street_number'],
                             ppInfo['street_number_suffix'],
                             ppInfo['street_dir'], ppInfo['street_name'],
                             ppInfo['street_type'],
                             ppInfo['street_dir_suffix'],
                             ppInfo['city_name'], ppInfo['PN_Zip_Code'])
    address = address.strip().replace('     ', ' ').replace('    ', ' ')
    address = address.replace('   ', ' ').replace('  ', ' ')
    ppid = ''
    return ppid, name, address


def getLee(num, predir, name, suffix, postdir, zipcode):
    url = 'http://www.precinctfind.com/pl_fl_lee.php'
    session = Session()
    payload = {'number': num, 'direction': predir, 'name': name,
               'type': suffix, 'post_dir': postdir, 'zip': zipcode, 'p': '',
               'search': 'Search Now', 'debug': '', 'county': 'fl_lee'}
    response = session.get(url, params=payload)
    soup = BeautifulSoup(response.text)
    table = soup.find('table').find('table').find('table').find_all('td')
    name = ''
    address = ''
    ppid = ''
    counter = 0
    for item in table:
        if counter == 0:
            name = item.text.strip()
        else:
            if len(address) > 0:
                address += ' '
            address += item.text.strip()
        counter += 1
    return ppid, name, address


def run(row):
    num, predir, name, suffix, postdir, city, zipcode, county = getValues(row)
    while True:
        try:
            if county.upper() == 'PALM BEACH':
                url = 'https://www.pbcelections.org/'
                eid = '139'
                pollingInfo = precinctFinder(url, num, predir, name, suffix,
                                             postdir, city, zipcode, eid)
            elif county.upper() == 'SARASOTA':
                url = 'https://www.sarasotavotes.com/'
                eid = '82'
                pollingInfo = precinctFinder(url, num, predir, name, suffix,
                                             postdir, city, zipcode, eid)
            elif county.upper() == 'VOLUSIA':
                fullcounty = 'volusia'
                pollingInfo = voterFocus(num, predir, name, suffix, postdir,
                                         city, zipcode, fullcounty)
            elif county.upper() == 'OSCEOLA':
                fullcounty = 'osceola'
                pollingInfo = voterFocus(num, predir, name, suffix, postdir,
                                         city, zipcode, fullcounty)
            elif county.upper() == 'LEE':
                pollingInfo = getLee(num, predir, name, suffix, postdir,
                                     zipcode)
            else:
                return '', '', ''
            return pollingInfo
        except Exception as inst:
            print type(inst)
            print inst
            return '', '', ''
