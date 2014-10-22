from requests import Session
import Levenshtein
import json
import re


def getValues(row):
    num = row['vf_reg_cass_street_num'].strip().upper()
    predir = row['vf_reg_cass_pre_directional'].strip().upper()
    name = row['vf_reg_cass_street_name'].strip().upper()
    suffix = row['vf_reg_cass_street_suffix'].strip().upper()
    postdir = row['vf_reg_cass_post_directional'].strip().upper()
    city = row['vf_reg_cass_city'].strip().upper()
    zipCode = row['vf_reg_cass_zip'].strip()
    if len(predir) > 0:
        predir += ' '
    if len(postdir) > 0:
        postdir = ' ' + postdir
    addrStr = '{0}{1} {2}{3} {4}, MS {5}'.format(predir, name, suffix, postdir,
                                                 city, zipCode).upper()
    return city, num, name, suffix, addrStr


def getOutputValues(ppData):
    ppid = ''
    name = ''
    address = ''
    options = json.loads(ppData)['d'].split(';')
    for pp in options:
        if len(ppid) > 0:
            ppid += ';'
        if len(name) > 0:
            ppid += ';'
        if len(address) > 0:
            ppid += ';'
        detail = pp.split('~')
        counter = len(detail)
        for value in detail:
            if counter == len(detail):
                name = value.strip()
            elif counter > 2:
                if len(address) > 0:
                    address += ' '
                address += value.strip()
            elif counter == 1:
                ppid = value.strip()
            counter -= 1
    return ppid, name, address


def matchString(addrStr, jsonStr):
    options = json.loads(jsonStr)['d'].split(';')
    optionList = []
    maximum = 0
    for option in options:
        text = option.replace('~~~', ' ').replace('~~', ' ').replace('~', ' ')
        text = re.sub('~[0-9]*~[0-9]*$', '', text)
        ratio = Levenshtein.ratio(str(text), str(addrStr))
        optionList.append((option, ratio))
        maximum = max(maximum, ratio)
    for option in optionList:
        if option[1] == maximum:
            rawList = option[0].split('~')
            return rawList[len(rawList) - 2]


def query(session, city, num, name, suffix, addrStr):
    url = 'http://sos.ms.gov/pollinglocator/PLWebService.asmx/'
    header = {'Content-Type': 'application/json; charset=UTF-8'}
    data = {'cityPartial': city}
    response = session.post(url + 'CityData', headers=header,
                            data=json.dumps(data))
    city = matchString(city, response.text)
    data = {'tmpCity': city, 'streetPartial': name}
    response = session.post(url + 'StreetDataWithCity', headers=header,
                            data=json.dumps(data))
    name = matchString(name, response.text)
    finalData = {'tmpCity': city, 'tmpHouseNum': num, 'tmpStreetName': name}
    action = 'SuggestedAddressesCity'
    if suffix != '':
        data = {'suffixPartial': suffix}
        response = session.post(url + 'SuffixData', headers=header,
                                data=json.dumps(data))
        suffix = matchString(suffix, response.text)
        finalData['tmpSuffix'] = suffix
        action = 'SuggestedAddressesAll'
    response = session.post(url + action, headers=header,
                            data=json.dumps(finalData))
    precinct = matchString(addrStr, response.text)
    data = {'tmpSplitId': precinct}
    response = session.post(url + 'GetLocationData', headers=header,
                            data=json.dumps(data))
    return response.text


def run(row):
    while True:
        try:
            session = Session()
            city, num, name, suffix, addrStr = getValues(row)
            ppData = query(session, city, num, name, suffix, addrStr)
            pollingInfo = getOutputValues(ppData)
            return pollingInfo
        except Exception as inst:
            print type(inst)
            print inst
