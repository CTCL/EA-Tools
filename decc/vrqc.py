from csv import DictReader, DictWriter
from bs4 import BeautifulSoup
import urllib2
import xlrd
import sys
import time
import json


def readCSV(filename):
    with open(filename) as inFile:
        drObject = DictReader(inFile)
        return list(drObject)


def writeCSV(data, filename, headers):
    with open(filename, 'w') as outFile:
        dwObject = DictWriter(outFile, headers, restval='',
                              extrasaction='ignore')
        dwObject.writeheader()
        for row in data:
            dwObject.writerow(row)


def getFIPS(url):
    fipsDict = {}
    stateDict = {}
    text = urllib2.urlopen(url).read()
    fipsList = text.split('\n')
    for i in range(1, len(fipsList)):
        rowValues = fipsList[i].split(',')
        state = ''
        county = ''
        if len(rowValues) >= 4:
            state = rowValues[0].upper()
            county = rowValues[3].upper()
            county = '{0}, {1}'.format(county, state)
            fipsDict['{0}{1}'.format(rowValues[1],
                                     rowValues[2])] = {'COUNTY': county,
                                                       'STATE': state}
        if rowValues[0].upper() in stateDict:
            stateDict[state].append(county)
        else:
            stateDict[state] = [county]
    return fipsDict, stateDict


def getZipURL(linkURL):
    site = 'http://www.huduser.org/portal/datasets/usps/ZIP_COUNTY_{0}.xlsx'
    soup = BeautifulSoup(urllib2.urlopen(linkURL).read())
    lastDate = soup.find('select', {'id': 'year'}).find('option').get('value')
    return site.format(lastDate)


def getZIPS(url):
    zipList = []
    zipSheet = xlrd.open_workbook(file_contents=urllib2.urlopen(url).read(),
                                  formatting_info=False).sheet_by_index(0)
    for i in range(1, zipSheet.nrows):
        zipInfo = {}
        rowValues = zipSheet.row_values(i, start_colx=0, end_colx=None)
        if rowValues[0] != '':
            zipInfo['ZIP'] = str(rowValues[0])
            zipInfo['FIPS'] = str(rowValues[1])
            zipList.append(zipInfo)
    return zipList


def buildZipTranslator(FIPS, ZIP):
    zipTranslator = {}
    for item in ZIP:
        fips = item['FIPS']
        if item['ZIP'] in zipTranslator:
            zipTranslator[item['ZIP']]['STATE'].append(FIPS[fips]['STATE'])
            zipTranslator[item['ZIP']]['COUNTY'].append(FIPS[fips]['COUNTY'])
        else:
            zipTranslator[item['ZIP']] = {'STATE': [FIPS[fips]['STATE']],
                                          'COUNTY': [FIPS[fips]['COUNTY']]}
    return zipTranslator


def inspectRows(regData, zipTranslator, stateDict):
    report = {'ICS': 0, 'ICZ': 0, 'IMS': 0, 'IMZ': 0, 'IPS': 0, 'IPZ': 0,
              'ECS': 0, 'EMS': 0, 'EPS': 0, 'CZIS': 0, 'MZIS': 0, 'PZIS': 0,
              'IC': 0, 'CIS': 0, 'CZIC': 0}
    for row in regData:
        #Check whether values for State and Zip
        #(current, previous, mailing) are included
        #Ex:'ICS' translates to 'Includes Current Statfilee'
        if 'CurrentState' not in row:
            raise Exception('No CurrentState Field included in file')
        cstate = row['CurrentState']
        row['ICS'] = cstate != '' and cstate is not None
        if row['ICS']:
            czip = row['CurrentZip']
            mzip = row['MailingZip']
            pzip = row['PreviousZip']
            mstate = row['MailingState']
            pstate = row['PreviousState']
            row['ICZ'] = czip != '' and czip is not None
            row['IMS'] = mstate != '' and mstate is not None
            row['IMZ'] = mzip != '' and mzip is not None
            row['IPS'] = pstate != '' and pstate is not None
            row['IPZ'] = pzip != '' and pzip is not None
            #Check whether values for State
            #(current, previous, mailing) actually exist
            #Ex: 'ECS' translates to 'Current State Exists'
            row['ECS'] = cstate.upper() in stateDict and row['ICS']
            row['EMS'] = mstate.upper() in stateDict and row['IMS']
            row['EPS'] = pstate.upper() in stateDict and row['IPS']
            #Check whether zip codes exist within state value
            #EX: 'CZIS' translates to 'Current Zip exists in State'
            if czip in zipTranslator:
                row['CZIS'] = cstate.upper() in zipTranslator[czip]['STATE']
            else:
                row['CZIS'] = False
            if mzip in zipTranslator:
                row['MZIS'] = mstate.upper() in zipTranslator[mzip]['STATE']
            else:
                row['MZIS'] = False
            if pzip in zipTranslator:
                row['PZIS'] = pstate.upper() in zipTranslator[pzip]['STATE']
            else:
                row['PZIS'] = False
            if row['ICS']:
                report['ICS'] += 1
            if row['ICZ']:
                report['ICZ'] += 1
            if row['IMS']:
                report['IMS'] += 1
            if row['IMZ']:
                report['IMZ'] += 1
            if row['IPS']:
                report['IPS'] += 1
            if row['IPZ']:
                report['IPZ'] += 1
            if row['ECS']:
                report['ECS'] += 1
            if row['EMS']:
                report['EMS'] += 1
            if row['EPS']:
                report['EPS'] += 1
            if row['CZIS']:
                report['CZIS'] += 1
            if row['MZIS']:
                report['MZIS'] += 1
            if row['PZIS']:
                report['PZIS'] += 1
            ##Relevant checks for county if county exists.
            if 'County' in row:
                county = row['County']
                state = cstate
                if cstate.upper() in ['AK', 'LA']:
                    countyType = {'AK': 'BOROUGH',
                                  'LA': 'PARISH'}[cstate.upper()]
                else:
                    countyType = 'COUNTY'
                fullCounty = '{0} {1}, {2}'.format(county, countyType,
                                                   state).upper()
                row['IC'] = row['County'] != '' and row['County'] is not None
                if czip in zipTranslator:
                    row['CZIC'] = fullCounty in zipTranslator[czip]['COUNTY']
                else:
                    row['CZIC'] = False
                if row['IC']:
                    report['IC'] += 1
                if row['CZIC']:
                    report['CZIC'] += 1
    return regData, report


def report(reportData):
    name = str(time.strftime('%Y-%m-%d %H:%M:%S')) + '.json'
    with open(name, 'w') as outFile:
        outFile.write(json.dumps(reportData))


def concatenateFields(regData):
    for row in regData:
        cs1 = row['CurrentStreetAddress1'].strip()
        cs2 = row['CurrentStreetAddress2'].strip()
        ms1 = row['MailingAddress1'].strip()
        ms2 = row['MailingAddress2'].strip()
        ps1 = row['PreviousStreetAddress1'].strip()
        ps2 = row['PreviousStreetAddress2'].strip()
        row['FullCurrentStreetAddress'] = '{0} {1}'.format(cs1, cs2).strip()
        row['FullMailingStreetAddress'] = '{0} {1}'.format(ms1, ms2).strip()
        row['FullPreviousStreetAddress'] = '{0} {1}'.format(ps1, ps2).strip()
        if 'HomeAreaCode' in row and 'HomePhone' in row:
            hac = str(row['HomeAreaCode'].strip())
            hp = str(row['HomePhone'].strip())
            row['FullHomePhone'] = hac + hp
        if 'MobilePhoneAreaCode' in row and 'MobilePhone' in row:
            mac = str(row['MobilePhoneAreaCode'].strip())
            mp = str(row['MobilePhone'].strip())
            row['FullMobilePhone'] = mac + mp
        bm = row['DOBmm']
        bd = row['DOBdd']
        by = row['DOByy']
        if bm != '' and bd != '' and by != '':
            row['FullDOB'] = '{0}/{1}/{2}'.format(bm, bd, by)
        sm = row['DateSignedmm']
        sd = row['Datesigneddd']
        sy = row['Datesignedyy']
        if sm != '' and sd != '' and sy != '':
            row['FullDateSigned'] = '{0}/{1}/{2}'.format(sm, sd, sy)
    return regData


def run(regData):
    census = '''https://www.census.gov/geo/reference/codes/files/
                national_county.txt'''.replace('\n', '').replace(' ', '')
    hud = 'http://www.huduser.org/portal/datasets/usps_crosswalk.html'
    FIPS, stateDict = getFIPS(census)
    zipURL = getZipURL(hud)
    ZIP = getZIPS(zipURL)
    zipTranslator = buildZipTranslator(FIPS, ZIP)
    regData, reportData = inspectRows(regData, zipTranslator, stateDict)
    report(reportData)
    finalData = concatenateFields(regData)
    return finalData


if __name__ == '__main__':
    headers = [
        'Batch_Name', 'Citizenship', 'AGE', 'FullDOB', 'DOBmm', 'DOBdd',
        'DOByy', 'FirstName', 'MiddleName', 'LastName', 'Suffix',
        'FullHomePhone', 'HomeAreaCode', 'HomePhone',
        'FullCurrentStreetAddress', 'CurrentStreetAddress1',
        'CurrentStreetAddress2', 'CurrentCity', 'CurrentState', 'CurrentZip',
        'FullMailingStreetAddress', 'MailingAddress1', 'MailingAddress2',
        'MailingCity', 'MailingState', 'MailingZip', 'Race', 'Party', 'Gender',
        'FullDateSigned', 'DateSignedmm', 'Datesigneddd', 'Datesignedyy',
        'FullMobilePhone', 'MobilePhoneAreaCode', 'MobilePhone',
        'EmailAddress', 'Batch_ID', 'County', 'PreviousCounty', 'Voulnteer',
        'License', 'PreviousName', 'FullPreviousStreetAddress',
        'PreviousStreetAddress1', 'PreviousStreetAddress2', 'PreviousCity',
        'PreviousState', 'PreviousZip', 'BadImage', 'Date', 'QC_I', 'IC',
        'ICS', 'ICZ', 'IMS', 'IMZ', 'IPS', 'IPZ', 'ECS', 'EMS', 'EPS', 'CIS',
        'CZIS', 'MZIS', 'PZIS', 'CZIC'
    ]
    data = run(readCSV(sys.argv[1]))
    writeCSV(data, sys.argv[2], headers)
