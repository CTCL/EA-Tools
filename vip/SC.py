from bs4 import BeautifulSoup
from requests import Session


def getValues(row):
    fname = row['tsmart_first_name']
    lname = row['tsmart_last_name']
    county = row['vf_county_name']
    dobStr = row['voterbase_dob']
    dob = '{0}/{1}/{2}'.format(int(dobStr[4:6]), int(dobStr[6:8]),
                               int(dobStr[:4]))
    return fname, lname, dob, county


def getCounties(soup):
    counties = {}
    selectName = 'ctl00$cphMain$ddlCounty$input'
    select = soup.find('select', {'name': selectName})
    for item in select.find_all('option'):
        counties[item.text.strip().upper()] = item.get('value')
    return counties


def getOutputValues(soup):
    ppid = ''
    name = ''
    address = ''
    baseName = 'ctl00_cphMain_VoterInfoUserControl_{0}_DisplayOnly'
    ppidSoup = soup.find('span', {'id': baseName.format('VotingPrecinctControl')})
    nameSoup = soup.find('span', {'id': baseName.format('PrecinctLocationControl')})
    addressSoup = soup.find('span', {'id': baseName.format('PrecinctAddress')})
    if ppidSoup is not None:
        ppid = ppidSoup.get_text().strip()
    name = nameSoup.get_text().strip()
    address = addressSoup.get_text().strip()
    return ppid, name, address


def getHiddenValues(soup):
    form = soup.find('form', {'name': 'aspnetForm'})
    fields = {}
    for item in form.find_all('input', {'type': 'hidden'}):
        fields[item.get('name')] = item.get('value')
    fields['hiddenInputToUpdateATBuffer_CommonToolkitScripts'] = '1'
    fields['ctl00$pnlMenu_CollapsiblePanelExtender_ClientState'] = 'true'
    fields['ctl00$AccordionStateBoardMenu_AccordionExtender_ClientState'] = 0
    fields['ctl00$mtbSearch'] = ''
    return fields


def query(fname, lname, dob, county, fields, counties, formURL, session):
    resultsURL = 'https://info.scvotes.sc.gov/Eng/VoterInquiry/'
    resultsURL += 'VoterInformation.aspx'
    county = counties[county.upper()]
    fields['ctl00$cphMain$txtFirstName$input'] = fname
    fields['ctl00$cphMain$txtLastName$input'] = lname
    fields['ctl00$cphMain$dobDateOfBirth$input'] = dob
    fields['ctl00$cphMain$ddlCounty$input'] = county
    fields['ctl00$buttonContent$txtHiddenCountyValue'] = county
    fields['ctl00$buttonContent$btnSubmit'] = 'Submit'
    session.post(formURL, data=fields)
    response = session.get(resultsURL)
    html = response.text
    return html


def run(row):
    formURL = 'https://info.scvotes.sc.gov/eng/voterinquiry/'
    formURL += 'VoterInformationRequest.aspx?PageMode=VoterInfo'
    try:
        session = Session()
        fname, lname, dob, county = getValues(row)
        response = session.get(formURL)
        soup = BeautifulSoup(response.text)
        hiddenFields = getHiddenValues(soup)
        counties = getCounties(soup)
        html = query(fname, lname, dob, county, hiddenFields, counties,
                     formURL, session)
        soup = BeautifulSoup(html)
        pollingInfo = getOutputValues(soup)
        return pollingInfo
    except Exception as inst:
        print type(inst)
        print inst
        return '', '', ''
