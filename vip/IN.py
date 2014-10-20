from bs4 import BeautifulSoup
from requests import Session
import Levenshtein


def getValues(row):
    fname = row['tsmart_first_name']
    lname = row['tsmart_last_name']
    county = row['vf_county_name']
    date = row['voterbase_dob']
    dob = '{0}/{1}/{2}'.format(date[4:6], date[6:8], date[:4])
    return fname, lname, county, dob


def getOutputValues(soup):
    ppid = ''
    street2 = ''
    IDBase = 'ctl00_ContentPlaceHolder1_'
    name = soup.find('span', {'id': IDBase + 'lblPollName'}).string
    IDBase += 'usrAddressView_'
    street1 = soup.find('span', {'id': IDBase + 'lblAddressLine1'}).string
    street2Soup = soup.find('span', {'id': IDBase + 'lblAddressLine2'})
    if street2Soup is not None:
        street2 = street2Soup.text
    city = soup.find('span', {'id': IDBase + 'lblCity'}).string
    zipCode = soup.find('span',
                        {'id': IDBase + 'usrZipCode_lblZipText'}).string
    address = '{0} {1} {2}, IN {3}'.format(street1.strip(), street2.strip(),
                                           city.strip(), zipCode)
    return ppid, name, address


def getHiddenValues(soup):
    form = soup.find('form', {'name': 'aspnetForm'})
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


def verifyCounty(counties, county):
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


def query(session, fname, lname, county, dob, fields, formURL):
    baseName = 'ctl00$ContentPlaceHolder1'
    fields[baseName + '_pnlSearch_CurrentState'] = 'false'
    fields[baseName + '_pnlSearchResults_CurrentState'] = 'true'
    fields[baseName + '_pnlPollingPlace_CurrentState'] = 'true'
    fields[baseName + '_pnlProvisionalBallot_CurrentState'] = 'true'
    fields[baseName + '_pnlOnBallot_CurrentState'] = 'true'
    fields[baseName + '_pnlOfficeContactInfo_CurrentState'] = 'true'
    fields[baseName + '_pnlDistricts_CurrentState'] = 'true'
    fields[baseName + '_pnlAbsentee_CurrentState'] = 'true'
    fields[baseName + '$txtFirst'] = fname
    fields[baseName + '$txtLast'] = lname
    fields[baseName + '$usrDOB$txtDate'] = dob
    fields[baseName + '$usrCounty$cboCounty'] = county
    fields[baseName + '$btnSearch'] = 'Find'
    response = session.post(formURL, data=fields, )
    html = response.text.encode('windows-1252')
    return html


def run(row):
    formURL = 'https://indianavoters.in.gov/PublicSite/Public/FT1'
    formURL += '/PublicLookupMain.aspx?Link=Polling'
    session = Session()
    while True:
        try:
            fname, lname, county, dob = getValues(row)
            response = session.get(formURL)
            soup = BeautifulSoup(response.text)
            counties = getCounties(soup)
            countyValue = verifyCounty(counties, county)
            hiddenFields = getHiddenValues(BeautifulSoup(response.text))
            html = query(session, fname, lname, countyValue,
                         dob, hiddenFields, formURL)
            soup = BeautifulSoup(html)
            with open('/home/michael/Desktop/output.html', 'w') as outFile:
                outFile.write(str(soup))
            pollingInfo = getOutputValues(soup)
            return pollingInfo
        except Exception as inst:
            print type(inst)
            print inst
            return '', '', ''
