from bs4 import BeautifulSoup
from requests import Session
import Levenshtein
import json


def getValues(row):
    suffixList = ['ARTERY', 'AVE', 'BLVD', 'CIR', 'CT', 'DR', 'FRWY', 'HWY',
                  'LN', 'PARK', 'PKWY', 'PIKE', 'PL', 'RD', 'ST', 'SQ', 'TER',
                  'TRL', 'WAY']
    dirDict = {'': '', 'W': 'West ', 'S': 'South ',
               'N': 'North ', 'E': 'East '}
    num = row['vf_reg_cass_street_num'].strip().upper()
    name = '{0}{1}'.format(dirDict[row['vf_reg_cass_pre_directional']],
                           row['vf_reg_cass_street_name'].strip().upper())
    suffix = row['vf_reg_cass_street_suffix'].strip().upper()
    zipCode = '{:05d}'.format(int(row['vf_reg_cass_zip']))
    if suffix not in suffixList:
        suffix = ''
    return num, name, suffix, zipCode


def getOutputValues(soup):
    ppid = ''
    name = ''
    address = ''
    nameID = 'MainContent_lblPollPlaceName'
    addrID = 'ctl00$MainContent$txtPollPlaceAddress'
    name = soup.find('span', {'id': nameID}).string
    address = soup.find('textarea', {'name': addrID}).string
    return ppid, name, address


def getHiddenValues(soup):
    form = soup.find('form', {'id': 'Form1'})
    fields = {}
    for item in form.find_all('input', {'type': 'hidden'}):
        fields[item.get('name')] = item.get('value')
    return fields


def matchStreet(streetStr, soup):
    print streetStr
    options = soup.find('select').find_all('option')
    optionList = []
    maximum = 0
    for option in options:
        value = option.get('value').upper()
        ratio = Levenshtein.ratio(value, streetStr)
        optionList.append((value, ratio))
        maximum = max(maximum, ratio)
    for option in optionList:
        if option[1] == maximum:
            return option[0]


def query(session, num, name, suffix, zipCode, fields, formURL):
    baseName = 'ctl00$MainContent$'
    fields[baseName + 'txtStreetNo'] = num
    fields[baseName + 'txtStreetName'] = name
    fields[baseName + 'ddlStreetSuffix'] = suffix
    fields[baseName + 'txtZip'] = zipCode
    fields[baseName + 'btnSearch'] = 'Show my results'
    fields[baseName + 'HiddenWDIVMappingPageURL'] = ''
    with open('/home/michael/Desktop/output.json', 'w') as outFile:
        outFile.write(json.dumps(fields, indent=2))
    response = session.post(formURL, data=fields)
    html = response.text
    with open('/home/michael/Desktop/output.html', 'w') as outFile:
        outFile.write(html)
    return html


def run(row):
    formURL = 'http://www.wheredoivotema.com/bal/MyElectionInfo.aspx'
    session = Session()
    while True:
        try:
            num, name, suffix, zipCode = getValues(row)
            response = session.get(formURL)
            soup = BeautifulSoup(response.text, 'lxml')
            hiddenFields = getHiddenValues(soup)
            html = query(session, num, name, suffix, zipCode,
                         hiddenFields, formURL)
            soup = BeautifulSoup(html, 'lxml')
            pollingInfo = getOutputValues(soup)
            return pollingInfo
        except Exception as inst:
            print type(inst)
            print inst
            return '', '', ''
