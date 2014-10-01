from csv import DictReader, DictWriter
from bs4 import BeautifulSoup
import urllib2, xlrd, sys, os, json

def readCSV(filename):
  with open(filename) as inFile:
    drObject = DictReader(inFile)
    return list(drObject)


def writeCSV(data, filename, headers):
  with open(filename, 'w') as outFile:
    dwObject = DictWriter(outFile, headers, restval='', extrasaction='ignore')
    dwObject.writeheader()
    for row in data:
      dwObject.writerow(row)


def getFIPS(url):
  fipsDict = {}
  stateDict = {}
  text = urllib2.urlopen(url).read()
  fipsList = text.split('\n')
  header = True
  for i in range(1,len(fipsList)):
    rowValues = fipsList[i].split(',')
    state = ''
    county = ''    
    if len(rowValues) >= 4:
      state = rowValues[0].upper()
      county = rowValues[3].upper()
      county = '{0}, {1}'.format(county, state)
      fipsDict['{0}{1}'.format(rowValues[1], rowValues[2])] = {'COUNTY': county, 'STATE': state}
    if rowValues[0].upper() in stateDict:
      stateDict[state].append(county)
    else:
      stateDict[state] = [county]
  return fipsDict, stateDict


def getZipURL(linkURL):
  soup = BeautifulSoup(urllib2.urlopen(linkURL).read())
  lastDate = soup.find('select', {'id': 'year'}).find('option').get('value')
  return 'http://www.huduser.org/portal/datasets/usps/ZIP_COUNTY_{0}.xlsx'.format(lastDate)


def getZIPS(url):
  zipList = []
  zipSheet = xlrd.open_workbook(file_contents = urllib2.urlopen(url).read(), formatting_info=False).sheet_by_index(0)
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
    if item['ZIP'] in zipTranslator:
      zipTranslator[item['ZIP']]['STATE'].append(FIPS[item['FIPS']]['STATE'])
      zipTranslator[item['ZIP']]['COUNTY'].append(FIPS[item['FIPS']]['COUNTY'])
    else:
      zipTranslator[item['ZIP']] = {'STATE': [FIPS[item['FIPS']]['STATE']], 'COUNTY': [FIPS[item['FIPS']]['COUNTY']]}
  return zipTranslator


def inspectRows(regData, zipTranslator, stateDict):
  report = {'ICS': 0, 'ICZ': 0, 'IMS': 0, 'IMZ': 0, 'IPS': 0, 'IPZ': 0,
  'ECS': 0, 'EMS': 0, 'EPS': 0, 'CZIS': 0, 'MZIS': 0, 'PZIS': 0,
  'IC': 0, 'CIS': 0, 'CZIC': 0}
  for row in regData:
    #Check whether values for State and Zip (current, previous, mailing) are included 
    #Ex:'ICS' translates to 'Includes Current Statfilee'
    if 'CurrentState' not in row:
      raise Exception('No CurrentState Field included in file')
    row['ICS'] = row['CurrentState'] != '' and row['CurrentState'] is not None
    if row['ICS']:
      row['ICZ'] = row['CurrentZip'] != '' and row['CurrentZip'] is not None
      row['IMS'] = row['MailingState'] != '' and row['MailingState'] is not None
      row['IMZ'] = row['MailingZip'] != '' and row['MailingZip'] is not None
      row['IPS'] = row['PreviousState'] != '' and row['PreviousState'] is not None
      row['IPZ'] = row['PreviousZip'] != '' and row['PreviousZip'] is not None
      #Check whether values for State (current, previous, mailing) actually exist 
      #Ex: 'ECS' translates to 'Current State Exists'
      row['ECS'] = row['CurrentState'].upper() in stateDict and row['ICS']
      row['EMS'] = row['MailingState'].upper() in stateDict and row['IMS']
      row['EPS'] = row['PreviousState'].upper() in stateDict and row['IPS']
      #Check whether zip codes exist within state value
      #EX: 'CZIS' translates to 'Current Zip exists in State'
      if row['CurrentZip'] in zipTranslator:
        row['CZIS'] = row['CurrentState'].upper() in zipTranslator[row['CurrentZip']]['STATE']
      else:
        row['CZIS'] = False
      if row['MailingZip'] in zipTranslator:
        row['MZIS'] = row['MailingState'].upper() in zipTranslator[row['MailingZip']]['STATE']
      else:
        row['MZIS'] = False
      if row['PreviousZip'] in zipTranslator:
        row['PZIS'] = row['PreviousState'].upper() in zipTranslator[row['PreviousZip']]['STATE']
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
        state = row['CurrentState']
        if row['CurrentState'].upper() in ['AK', 'LA']:
          countyType = {'AK': 'BOROUGH', 'LA': 'PARISH'}[row['CurrentState'].upper()]
        else:
          countyType = 'COUNTY'
        fullCounty = '{0} {1}, {2}'.format(county, countyType, state).upper()
        row['IC'] = row['County'] != '' and row['County'] is not None
        if row['CurrentZip'] in zipTranslator:
          row['CZIC'] = fullCounty in zipTranslator[row['CurrentZip']]['COUNTY']
        else:
          row['CZIC'] = False


        if row['IC']:
          report['IC'] += 1
        if row['CZIC']:
          report['CZIC'] += 1
  return regData, report


def report(reportData):
  print reportData['ICS'], 'current state values included,', reportData['ECS'], 'of those actually exist'
  print reportData['ICZ'], 'current zip values included,', reportData['CZIS'], 'of those actually in corresponding state'
  print reportData['IMS'], 'mailing state values included,', reportData['EMS'], 'of those actually exist'
  print reportData['IMZ'], 'mailing zip values included,', reportData['MZIS'], 'of those actually in corresponding state'
  print reportData['IPS'], 'previous state values included,', reportData['EPS'], 'of those actually exist'
  print reportData['IPZ'], 'previous zip values included,', reportData['PZIS'], 'of those actually in corresponding state'
  print reportData['IC'], 'counties included,', reportData['CZIC'], 'of those correspond to included zipcodes'


def concatenateFields(regData):
  for row in regData:
    row['FullCurrentStreetAddress'] = '{0} {1}'.format(row['CurrentStreetAddress1'].strip(), row['CurrentStreetAddress2'].strip()).strip()
    row['FullMailingStreetAddress'] = '{0} {1}'.format(row['MailingAddress1'].strip(), row['MailingAddress2'].strip()).strip()
    row['FullPreviousStreetAddress'] = '{0} {1}'.format(row['PreviousStreetAddress1'].strip(), row['PreviousStreetAddress2'].strip()).strip()
    if 'HomeAreaCode' in row and 'HomePhone' in row:
      row['FullHomePhone'] = str(row['HomeAreaCode'].strip()) + str(row['HomePhone'].strip())
    if 'MobilePhoneAreaCode' in row and 'MobilePhone' in row:
      row['FullMobilePhone'] = str(row['MobilePhoneAreaCode'].strip()) + str(row['MobilePhone'].strip())
    if row['DOBmm'] != '' and row['DOBdd'] != '' and row['DOByy'] != '':
      row['FullDOB'] = '{0}/{1}/{2}'.format(row['DOBmm'], row['DOBdd'], row['DOByy'])
    if row['DateSignedmm'] != '' and row['Datesigneddd'] != '' and row['Datesignedyy'] != '':
      row['FullDateSigned'] = '{0}/{1}/{2}'.format(row['DateSignedmm'], row['Datesigneddd'], row['Datesignedyy'])
  return regData


def run(regData):
  FIPS, stateDict = getFIPS('https://www.census.gov/geo/reference/codes/files/national_county.txt')
  zipURL = getZipURL('http://www.huduser.org/portal/datasets/usps_crosswalk.html')
  ZIP = getZIPS(zipURL)
  zipTranslator = buildZipTranslator(FIPS, ZIP)
  regData, reportData = inspectRows(regData, zipTranslator, stateDict)
  report(reportData)
  finalData = concatenateFields(regData)
  return finalData


if __name__ == '__main__':
  headers = [
  'Batch_Name', 'Citizenship', 'AGE', 'FullDOB', 'DOBmm', 'DOBdd', 'DOByy', 'FirstName', 'MiddleName', 'LastName', 'Suffix', 'FullHomePhone', 
  'HomeAreaCode', 'HomePhone', 'FullCurrentStreetAddress', 'CurrentStreetAddress1', 'CurrentStreetAddress2', 'CurrentCity', 
  'CurrentState', 'CurrentZip', 'FullMailingStreetAddress', 'MailingAddress1', 'MailingAddress2', 'MailingCity', 'MailingState', 'MailingZip', 'Race', 
  'Party', 'Gender', 'FullDateSigned', 'DateSignedmm', 'Datesigneddd', 'Datesignedyy', 'FullMobilePhone', 'MobilePhoneAreaCode', 'MobilePhone', 
  'EmailAddress', 'Batch_ID', 'County', 'PreviousCounty', 'Voulnteer', 'License', 'PreviousName', 'FullPreviousStreetAddress', 'PreviousStreetAddress1', 
  'PreviousStreetAddress2', 'PreviousCity', 'PreviousState', 'PreviousZip', 'BadImage', 'Date', 'QC_I', 'IC', 'ICS', 'ICZ', 'IMS', 'IMZ', 'IPS', 'IPZ', 'ECS', 
  'EMS', 'EPS', 'CIS', 'CZIS', 'MZIS', 'PZIS', 'CZIC'
  ]
  data = run(readCSV(sys.argv[1]))
  writeCSV(data, sys.argv[2], headers)
