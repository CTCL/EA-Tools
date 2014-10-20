from bs4 import BeautifulSoup
from requests import Session
import Levenshtein


def getValues(row):
    num = row['vf_reg_cass_street_num'].strip().upper()
    predir = row['vf_reg_cass_pre_directional'].strip().upper()
    name = row['vf_reg_cass_street_name'].strip().upper()
    suffix = row['vf_reg_cass_street_suffix'].strip().upper()
    postdir = row['vf_reg_cass_post_directional'].strip().upper()
    city = row['vf_reg_cass_city'].strip().upper()
    county = row['vf_county_name'].strip().upper()
    if len(predir) > 0:
        predir += ' '
    if len(postdir) > 0:
        postdir = ' ' + postdir
    addrStr = '{0}{1} {2}{3}-{4}'.format(predir, name, suffix, postdir,
                                         city).upper()
    return county, num, name, addrStr


def getOutputValues(soup):
    ppid = ''
    name = ''
    address = ''
    name = soup.find('span', {'id': 'PollingPlaceNameLabel'}).string
    address = soup.find('span', {'id': 'PollingPlaceAddressLabel'}).string
    return ppid, name, address


def getHiddenValues(soup):
    form = soup.find('form')
    fields = {}
    for item in form.find_all('input', {'type': 'hidden'}):
        fields[item.get('name')] = item.get('value')
    return fields


def matchStreet(streetStr, soup):
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


def query(session, county, num, name, addrStr, fields, formURL):
    fields['HouseNumberTextBox'] = num
    fields['StreetNameTextBox'] = name
    fields['SelectCountyDropDownList'] = county
    fields['ImageNextButton.x'] = '30'
    fields['ImageNextButton.y'] = '30'
    action = 'WhereDoIVote.aspx'
    response = session.post(formURL + action, data=fields)
    html = response.text
    soup = BeautifulSoup(html, 'lxml')
    street = matchStreet(addrStr, soup)
    fields = getHiddenValues(soup)
    fields['ListBox1'] = street
    fields['ImageNextButton.x'] = '70'
    fields['ImageNextButton.y'] = '24'
    headers = {'Cache-Control': 'max-age=0',
               'Origin': 'http://idahovotes.gov'}
    action = soup.find('form').get('action')
    response = session.post(formURL + action, data=fields, headers=headers)
    html = response.text
    return html


def run(row):
    formURL = 'http://www.idahovotes.gov/YourPollingPlace/'
    while True:
        try:
            session = Session()
            county, num, name, addrStr = getValues(row)
            response = session.get(formURL + 'WhereDoIVote.aspx')
            html = response.text
            hiddenFields = getHiddenValues(BeautifulSoup(html, 'lxml'))
            html = query(session, county, num, name, addrStr,
                         hiddenFields, formURL)
            soup = BeautifulSoup(html, 'lxml')
            pollingInfo = getOutputValues(soup)
            return pollingInfo
        except Exception as inst:
            print type(inst)
            print inst
