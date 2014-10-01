import xlrd, sys, re, psycopg2, psycopg2.extras
from csv import DictWriter
from config import HOST, DB, USER
import vrqc


def getBatches(cursor):
  cursor.execute('''SELECT id, original_filename
                    FROM decc_form_batch''')
  result = cursor.fetchall()
  batchDict = {}
  for item in result:
    batchDict[str(int(item[0]))] = str(item[1])
  return batchDict


def writeFile(dictList, outputFile, headerList):
  with open(outputFile, 'w') as output:
    for field in dictList[0]:
      if field not in headerList:
        headerList.append(field)

    dwObject = DictWriter(output, headerList, restval = '', delimiter = ',')
    dwObject.writeheader()
    for row in dictList:
      dwObject.writerow(row)


def processXLSX(inputFile, db, cursor):
  worksheet = xlrd.open_workbook(inputFile).sheet_by_index(0)
  headers = dict( (i, worksheet.cell_value(0, i) ) for i in range(worksheet.ncols) ) 
  drObject = ( dict( (headers[j], worksheet.cell_value(i, j)) for j in headers ) for i in range(0, worksheet.nrows) )
  headerList = []
  for key in headers:
    headerList.append(headers[key])
  headerList.insert(0, 'Batch_Name')
  batchDict = getBatches(cursor)
  dictList = []
  countDict = {}
  batchIDfieldName = ''
  for item in drObject:
    for key in item:
      if re.search('[Bb][Aa][Tt][Cc][Hh]', str(key)):
        batchIDfieldName = key
        break
    break
  for item in drObject:
    batchID = int(item[batchIDfieldName])

    item['Batch_Name'] = batchDict[str(batchID)]
    if str(batchID) not in countDict.keys():
      countDict[str(batchID)] = 1
    else:
      countDict[str(batchID)] += 1
    dictList.append(item)
  for key in countDict:
    cursor.execute('''UPDATE decc_form_batch
                      SET final_item_count = {0},
                      return_date = current_date
                      WHERE id = {1};
                      '''.format(countDict[key], key))
    db.commit()
  return dictList, headerList
  

def main(vr, inFile, outFile):
  headers = [
  'Batch_Name', 'Citizenship', 'AGE', 'FullDOB', 'DOBmm', 'DOBdd', 'DOByy', 'FirstName', 'MiddleName', 'LastName', 'Suffix', 'FullHomePhone', 
  'HomeAreaCode', 'HomePhone', 'FullCurrentStreetAddress', 'CurrentStreetAddress1', 'CurrentStreetAddress2', 'CurrentCity', 
  'CurrentState', 'CurrentZip', 'FullMailingStreetAddress', 'MailingAddress1', 'MailingAddress2', 'MailingCity', 'MailingState', 'MailingZip', 'Race', 
  'Party', 'Gender', 'FullDateSigned', 'DateSignedmm', 'Datesigneddd', 'Datesignedyy', 'FullMobilePhone', 'MobilePhoneAreaCode', 'MobilePhone', 
  'EmailAddress', 'Batch_ID', 'County', 'PreviousCounty', 'Vote Mail', 'Voulnteer', 'License', 'PreviousName', 'FullPreviousStreetAddress', 'PreviousStreetAddress1', 
  'PreviousStreetAddress2', 'PreviousCity', 'PreviousState', 'PreviousZip', 'Former County', 'BadImage', 'Date', 'QC_I', 'IC', 'ICS', 'ICZ', 'IMS', 'IMZ', 'IPS', 'IPZ', 'ECS', 
  'EMS', 'EPS', 'CIS', 'CZIS', 'MZIS', 'PZIS', 'CZIC'
  ]
  db = psycopg2.connect(host = HOST, database = DB, user = USER)
  cursor = db.cursor()
  dictList, headerList = processXLSX(inFile, db, cursor)
  if vr: 
    dictList = vrqc.run(dictList)
    writeFile(dictList, outFile, headers)
  else:
    writeFile(dictList, outFile, headerList)
