from bs4 import BeautifulSoup
from requests import Session
import Levenshtein
import json


def getValues(row):
    finit = row['tsmart_first_name'].strip()[:1].upper()
    lname = row['tsmart_last_name'].strip().upper()
    county = row['vf_county_name'].strip().upper()
    rawdob = row['voterbase_dob'].strip()
    dob = '{0}/{1}/{2}'.format(rawdob[4:6], rawdob[6:8], rawdob[:4])
    return finit, lname, county, dob


def getOutputValues(soup):
    ppid = ''
    name = ''
    address = ''
    nameID = 'MainContentPlaceHolder_lblPrecinctName'
    addrID = 'MainContentPlaceHolder_lblPrecinctStreet'
    cityID = 'MainContentPlaceHolder_lblPrecinctCity'
    name = soup.find('span', {'id': nameID}).string
    address = '{0} {1}'.format(soup.find('span', {'id': addrID}).string,
                               soup.find('span', {'id': cityID}).string)
    return ppid, name, address


def getHiddenValues(soup):
    form = soup.find('form', {'id': 'form1'})
    fields = {}
    for item in form.find_all('input', {'type': 'hidden'}):
        fields[item.get('name')] = item.get('value')
    return fields


def getCounties(soup):
    counties = {}
    selectID = 'ctl00$MainContentPlaceHolder$ddlCounty'
    select = soup.find('select', {'name': selectID})
    for option in select.find_all('option'):
        counties[option.text.strip()] = option.get('value')
    return counties


def selectCounty(counties, county):
    maximum = 0
    county = str(county.upper())
    optionList = []
    for option in counties:
        text = str(option.strip().upper())
        value = counties[option]
        score = Levenshtein.ratio(county, text)
        maximum = max(maximum, score)
        optionList.append((score, value))
    for option in optionList:
        if maximum == option[0]:
            return str(option[1])


def getVoterID(finit, lname, county, dob, session):
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    action = 'http://www.mvp.sos.ga.gov/Service/MVPService.asmx/GetVoterCount'
    fields = {'FirstInitial': finit, 'LastName': lname, 'date': dob,
              'county': county, 'zip': '', 'streetname': '', 'streetno': '',
              'flag': 'dob'}
    request = session.post(action, data=json.dumps(fields), headers=headers)
    return json.loads(request.text)['d'][0]['Registration_Number']


def query(finit, lname, county, dob, fields, formURL, session):
    nameBase = 'ctl00$MainContentPlaceHolder$'
    voterID = getVoterID(finit, lname, county, dob, session)
    fields[nameBase + 'ddlCounty'] = county
    fields[nameBase + 'txtLastName'] = lname
    fields[nameBase + 'txtFirstInitial'] = finit
    fields[nameBase + 'btnSubmit'] = 'Submit'
    fields[nameBase + 'hdnVoterRegistrationNumber'] = voterID
    fields[nameBase + 'hdnCountyID'] = ''
    fields[nameBase + 'txtZip'] = ''
    response = session.post(formURL, data=fields)
    html = response.text.encode('windows-1252')
    with open('/home/michael/Desktop/output.html', 'w') as outFile:
        outFile.write(html)
    return html


def run(row):
    formURL = 'http://www.mvp.sos.ga.gov/LoginPage.aspx'
    session = Session()
    while True:
        try:
            finit, lname, county, dob = getValues(row)
            response = session.get(formURL)
            soup = BeautifulSoup(response.text, 'lxml')
            counties = getCounties(soup)
            countyValue = selectCounty(counties, county)
            hiddenFields = getHiddenValues(soup)
            html = query(finit, lname, countyValue, dob,
                         hiddenFields, formURL, session)
            soup = BeautifulSoup(html, 'lxml')
            pollingInfo = getOutputValues(soup)
            return pollingInfo
        except Exception as inst:
            print type(inst)
            print inst
            return '', '', ''
