from PyPDF2 import PdfFileReader
from csv import DictReader, DictWriter
import os
import psycopg2
import psycopg2.extras
import re
import shutil


def findClients(cursor):
    cursor.execute('''SELECT id, org_name
                      FROM decc_form_client''')
    table = cursor.fetchall()
    clientDict = {}
    for item in table:
        clientDict[item[1]] = item[0]
    return clientDict


def getProject(clientID, cursor):
    cursor.execute('''SELECT project_id
                    FROM decc_form_client
                    WHERE id = {0}
                    '''.format(clientID))
    value = cursor.fetchall()[0][0]
    return value


def findOrders(projectID, cursor):
    cursor.execute('''SELECT id AS ID, order_date AS DATE
                      FROM decc_form_order
                      WHERE project_id = {0}
                      '''.format(projectID))
    table = cursor.fetchall()
    orderDict = {}
    for item in table:
        orderDict[item[1].strftime('%m/%d/%Y')] = item[0]
    return orderDict


def createOrder(projectID, cursor):
    cursor.execute('''INSERT INTO decc_form_order
                      (order_date, project_id, digital)
                      VALUES (current_date, {0}, TRUE);
                      '''.format(projectID))


def findTypes(projectID, cursor):
    cursor.execute('''SELECT id AS ID, type_name AS NAME
                      FROM decc_form_type
                      WHERE project_id = {0}
                      '''.format(projectID))
    table = cursor.fetchall()
    typeDict = {}
    for item in table:
        typeDict[item[1]] = item[0]
    return typeDict


def createPart(orderID, typeID, state, rush, van, match, quad, cursor, db):
    cursor.execute('''INSERT INTO decc_form_part
                      (state, item_count, order_id, form_type_id, rush, van,
                       quad, "match", destroy_files, return_files, batch_count)
                      VALUES ('{0}', 0, {1}, {2}, bool({3}), bool({4}),
                              bool({5}), bool({6}), bool(0), bool(0), 0)
                      '''.format(state, orderID, typeID, rush, van, quad,
                                 match))
    db.commit()
    cursor.execute('''SELECT MAX(id)
                                            FROM decc_form_part
                                            WHERE order_id = {0}
                                            '''.format(orderID))
    result = cursor.fetchall()[0][0]
    return result


def obtainStartNum(clientID, cursor):
    cursor.execute('''SELECT MAX(decc_form_batch.id) + 1 AS ID
                      FROM decc_form_batch
                      INNER JOIN decc_form_part
                      ON decc_form_batch.part_id = decc_form_part.id
                      INNER JOIN decc_form_order
                      ON decc_form_part.order_id = decc_form_order.id
                      INNER JOIN decc_form_client
                      ON decc_form_order.project_id =
                         decc_form_client.project_id
                      WHERE decc_form_client.id = {0}
                      '''.format(clientID))
    value = cursor.fetchall()[0][0]
    if value is not None:
        batchID = value
    else:
        batchID = int(clientID) * 10000000 + 1
    return batchID


def processPDF(PATH, outputPATH, startNum, partID, cursor, db):
    files = []
    for dp, dn, filenames in os.walk(PATH):
        for f in filenames:
            files.append(os.path.join(dp, f))
    batchID = startNum
    totalPages = 0
    print 'Starting ID:\t', startNum
    if not os.path.exists(outputPATH):
        os.makedirs(outputPATH)
    for item in files:
        clientFilename = re.sub(r'^/', '', item.replace(PATH, ''))
        extension = re.sub(r'^.*\.(.*?)$', r'\1', item).lower()
        vendorFilename = str("%010d" % (batchID,)) + "." + extension
        if extension == 'pdf':
            try:
                input = PdfFileReader(item)
                page_count = input.getNumPages()
            except Exception:
                print 'error counting pages in', item
                page_count = 1
        else:
            page_count = 1
        totalPages += int(page_count)
        if re.search(r'(/)|(\\)$', item):
            outfile = outputPATH + vendorFilename
        else:
            outfile = outputPATH + '/' + vendorFilename
        cursor.execute('''INSERT INTO decc_form_batch
                          (id, client_filename, vendor_filename, item_count,
                           submission_date, processed_date, part_id,
                           original_filename)
                          VALUES ({0}, '{1}', '{2}', {3}, current_date,
                                  current_date, {4}, '{1}')
                          '''.format(batchID,
                                     clientFilename.replace("'", "''"),
                                     vendorFilename, page_count, partID))
        shutil.move(item, outfile)
        batchID += 1
    db.commit()
    print 'Total Pages:\t', totalPages
    print 'Ending ID:\t', batchID - 1
    endNum = batchID - 1
    return endNum, totalPages


def processPhysical(PATH, outputPATH, partID, startNum, db, cursor):
    dictList = []
    ID = int(startNum)
    with open(PATH, 'r') as file:
        input = DictReader(file)
        for item in input:
            rowInfo = item
            cursor.execute('''INSERT INTO decc_form_batch (id, vendor_filename,
                                                           client_filename,
                                                           submission_date,
                                                           processed_date,
                                                           part_id,
                                                           original_filename)
                              VALUES ('{0}', '{0}', '{1}', current_date,
                              current_date, {2}, '{1}');
                              '''.format(ID, item['Batch Name'], partID))
            db.commit()
            rowInfo['Batch ID'] = "%010d" % ID
            dictList.append(rowInfo)
            ID += 1
    with open(outputPATH, 'w') as file:
        output = DictWriter(file, fieldnames=['Batch ID', 'Batch Name'],
                            restval='', delimiter=',')
        output.writeheader()
        for row in dictList:
            output.writerow(row)


def getCursor(HOST, DB, USER):
    db = psycopg2.connect(host=HOST, database=DB, user=USER)
    cursor = db.cursor()
    return cursor, db
