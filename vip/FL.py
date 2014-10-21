from bs4 import BeautifulSoup
from requests import Session
import Levenshtein
import re


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


def getOutputValues(soup):
    ppid = ''
    name = ''
    address = ''
    return ppid, name, address


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
    string = string.upper()
    optionList = []
    for text in stringList:
        score = Levenshtein.ratio(string, text)
        print text, score
        maximum = max(maximum, score)
        optionList.append((score, text))
    for option in optionList:
        if maximum == option[0]:
            return str(option[1])


def hyphenateBlanks(value):
    if value == '':
        value = '--'
    return value


def precinctFinder(url, num, predir, name, suffix, postdir, city, zipcode, eid):
    session = Session()
    action = 'precinctfinder.aspx'
    fixedpredir = hyphenateBlanks(predir)
    fixedsuffix = hyphenateBlanks(suffix)
    fixedpostdir = hyphenateBlanks(postdir)
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
    with open('/home/michael/Desktop/output.html', 'w') as outFile:
        outFile.write(html)
    soup = BeautifulSoup(response.text, 'lxml')
    addrStr = 'AddrNum={0}:PreDir={1}:StreetName={2}:Type={3}:PostDir={4}:PrecinctID='
    addrStr = addrStr.format(str(int(num)), predir, name, suffix, postdir)
    values = []
    for item in soup.find_all('input', {'type': 'radio'}):
        values.append(item.get('value'))
    finalStr = matchString(addrStr, values)
    precinct = re.sub('^.*PrecinctID=(.*)$', '\\1', finalStr)
    data = {'PrecinctID': precinct, 'eid': eid}
    action = 'PollingPlace.aspx'
    response = session.get(url + action, params=data)
    soup = BeautifulSoup(response.text.replace('<br />', ' '))
    name = soup.find('span', {'id': 'ppControl_lblName'}).string
    address = soup.find('span', {'id': 'ppControl_lblAddress1'}).string
    ppid = ''
    return ppid, address, name


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
                county = 'VOL'
                fullcounty = 'volusia'
                ##Voter Focus
            elif county.upper() == 'OSCEOLA':
                county = 'OSC'
                fullcounty = 'osceola'
                ##Voter Focus
            elif county.upper() == 'LEE':
                pass
                #special lee get request function
            elif county.upper() == 'MANATEE':
                pass
                #weird partial street name request
            elif county.upper() == 'CHARLOTTE':
                pass
                #weird partial street name request
            else:
                return '', '', ''
            return pollingInfo
        except Exception as inst:
            print type(inst)
            print inst
            return '', '', ''
