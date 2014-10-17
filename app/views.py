from flask import render_template, flash, redirect, request, url_for
from config import HOST, DB, USER, PASSWORD, deccinputdir, deccoutputdir, flow
from vip.execute import VIP, EVIP
from vip import civicInfo
from forms import SelectProgram, optionSelector, orderSubmission
from forms import DECCReturned, VITQuery, runEVQuery
from oauth2client.file import Storage
from app import app
import decc.processScans
import decc.processXLSX
import json
import os
import os.path


@app.route('/')
@app.route('/index')
def index():
    return render_template("index.html",
                           title='Home')


@app.route('/vip/e-day-qa', methods=['GET', 'POST'])
def VIPqa():
    form = SelectProgram()
    sheetURL = 'https://docs.google.com/a/neworganizing.com/spreadsheets/d/'
    if form.validate_on_submit():
        creds = Storage('.cred').get()
        sheetKey = VIP(form.state.data, creds)
        return redirect('{0}{1}'.format(sheetURL, sheetKey))
    return render_template('qa.html',
                           title='Select Program',
                           form=form)


@app.route('/vip/early-vote-qa', methods=['GET', 'POST'])
def EVqa():
    form = runEVQuery()
    sheetURL = 'https://docs.google.com/a/neworganizing.com/spreadsheets/d/'
    if form.validate_on_submit():
        creds = Storage('.cred').get()
        sheetKey = EVIP(form.state.data, creds)
        return redirect('{0}{1}'.format(sheetURL, sheetKey))
    return render_template('qa.html',
                           title='Select Program',
                           form=form)


@app.route('/auth')
def auth():
    auth_uri = flow.step1_get_authorize_url()
    return redirect(auth_uri)


@app.route('/auth_return', methods=['GET'])
def auth_return():
    authCode = request.args['code']
    credentials = flow.step2_exchange(authCode)
    storage = Storage('.cred')
    storage.put(credentials)
    return redirect('/credcheck')


@app.route('/credcheck')
def checkForCredentials():
    if os.path.isfile('.cred'):
        return redirect('/vip')
    else:
        return redirect('/auth')


@app.route('/vip')
def vip():
    return render_template("vip.html")


@app.route('/decc')
def deccSelect():
    return render_template("decc.html")


@app.route('/decc/scanstep1', methods=['GET', 'POST'])
def scanOne():
    cursor, db = decc.processScans.getCursor(HOST, DB, USER, PASSWORD)
    clients = decc.processScans.findClients(cursor)
    db.close()
    form = optionSelector()
    options = []
    for client in clients:
        option = (clients[client], client)
        options.append(option)
    form.option.choices = options
    if form.validate_on_submit():
        return redirect(url_for('.scanTwo', client=form.option.data))
    return render_template('deccstart.html',
                           form=form,
                           type='client',
                           options=clients)


@app.route('/decc/scanstep2', methods=['GET', 'POST'])
def scanTwo():
    client = request.args['client']
    cursor, db = decc.processScans.getCursor(HOST, DB, USER, PASSWORD)
    project = decc.processScans.getProject(client, cursor)
    orders = decc.processScans.findOrders(project, cursor)
    form = optionSelector()
    options = [(0, 'New Order'), ]
    for order in orders:
        option = (orders[order], order)
        options.append(option)
    form.option.choices = options
    if form.validate_on_submit():
        if form.option.data == 0:
            decc.processScans.createOrder(project, cursor)
            db.commit()
            db.close()
            flash('Order created', 'message')
            return redirect(url_for('.scanTwo',
                                    client=client))
        else:
            db.close()
            return redirect(url_for('.scanThree',
                                    client=client,
                                    project=project,
                                    order=form.option.data))
    db.close()
    return render_template('deccstart.html',
                           form=form,
                           type='order',
                           options=orders)


@app.route('/decc/scanstep3', methods=['GET', 'POST'])
def scanThree():
    cursor, db = decc.processScans.getCursor(HOST, DB, USER, PASSWORD)
    client = request.args['client']
    project = request.args['project']
    order = request.args['order']
    types = decc.processScans.findTypes(project, cursor)
    options = []
    db.close()
    for item in types:
        option = (types[item], item)
        options.append(option)
    form = orderSubmission()
    form.formType.choices = options
    typeName = ''
    if form.validate_on_submit():
        for item in types:
            if int(types[item]) == int(form.formType.data):
                typeName = item
        return redirect(url_for('.processScans',
                                client=client,
                                project=project,
                                order=order,
                                formType=form.formType.data,
                                state=form.state.data,
                                rush=form.rush.data,
                                van=form.van.data,
                                match=form.match.data,
                                quad=form.quad.data,
                                typeName=typeName))
    return render_template('deccSubmit.html',
                           form=form,
                           types=types)


@app.route('/decc/scanform')
def processScans():
    cursor, db = decc.processScans.getCursor(HOST, DB, USER, PASSWORD)
    client = request.args['client']
    order = request.args['order']
    formType = request.args['formType']
    state = request.args['state']
    rush = request.args['rush']
    van = request.args['van']
    match = request.args['match']
    quad = request.args['quad']
    typeName = request.args['typeName']
    part = decc.processScans.createPart(order, formType, state, rush, van,
                                        match, quad, cursor, db)
    startNum = decc.processScans.obtainStartNum(client, cursor)
    endNum, totalPages = decc.processScans.processPDF(deccinputdir,
                                                      deccoutputdir, startNum,
                                                      part, cursor, db)
    db.close()
    flash('Processing part complete', 'message')
    return redirect(url_for('.email',
                            typeName=typeName,
                            startNum=startNum,
                            endNum=endNum,
                            numRecords=totalPages,
                            numFiles=endNum - startNum + 1,
                            client=client,
                            rush=rush))


@app.route('/decc/checkprocessing')
def checkProcessing():
    files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(deccinputdir) for f in filenames]
    for i in range(0, len(files)):
        files[i] = files[i].replace(
            deccinputdir,
            '')
    return render_template("fileList.html",
                           files=files,
                           fileNum=len(files))


@app.route('/decc/shipstep1', methods=['GET', 'POST'])
def shipOne():
    cursor, db = decc.processScans.getCursor(HOST, DB, USER, PASSWORD)
    clients = decc.processScans.findClients(cursor)
    db.close()
    form = optionSelector()
    options = []
    for client in clients:
        option = (clients[client], client)
        options.append(option)
    form.option.choices = options
    if form.validate_on_submit():
        return redirect(url_for('.shipTwo',
                                client=form.option.data))
    return render_template('deccstart.html',
                           form=form,
                           type='client',
                           options=clients)


@app.route('/decc/shipstep2', methods=['GET', 'POST'])
def shipTwo():
    client = request.args['client']
    cursor, db = decc.processScans.getCursor(HOST, DB, USER, PASSWORD)
    project = decc.processScans.getProject(client, cursor)
    orders = decc.processScans.findOrders(project, cursor)
    form = optionSelector()
    options = [(0, 'New Order'), ]
    for order in orders:
        option = (orders[order], order)
        options.append(option)
    form.option.choices = options
    if form.validate_on_submit():
        if form.option.data == 0:
            decc.processScans.createOrder(project, cursor)
            db.commit()
            db.close()
            flash('Order created', 'message')
            return redirect(url_for('.scanTwo',
                                    client=client))
        else:
            db.close()
            return redirect(url_for('.shipThree',
                                    client=client,
                                    project=project,
                                    order=form.option.data))
    db.close()
    return render_template('deccstart.html',
                           form=form,
                           type='order',
                           options=orders)


@app.route('/decc/shipstep3', methods=['GET', 'POST'])
def shipThree():
    cursor, db = decc.processScans.getCursor(HOST, DB, USER, PASSWORD)
    client = request.args['client']
    project = request.args['project']
    order = request.args['order']
    types = decc.processScans.findTypes(project, cursor)
    options = []
    db.close()
    for item in types:
        option = (types[item], item)
        options.append(option)
    form = orderSubmission()
    form.formType.choices = options
    if form.validate_on_submit():
        return redirect(url_for('.processShipment',
                                client=client,
                                project=project,
                                order=order,
                                formType=form.formType.data,
                                state=form.state.data,
                                rush=form.rush.data,
                                van=form.van.data,
                                match=form.match.data,
                                quad=form.quad.data))
    return render_template('deccSubmit.html',
                           form=form,
                           types=types)


@app.route('/decc/shipform')
def processShipment():
    cursor, db = decc.processScans.getCursor(HOST, DB, USER, PASSWORD)
    client = request.args['client']
    order = request.args['order']
    formType = request.args['formType']
    state = request.args['state']
    rush = request.args['rush']
    van = request.args['van']
    match = request.args['match']
    quad = request.args['quad']
    part = decc.processScans.createPart(order, formType, state, rush, van,
                                        match, quad, cursor, db)
    startNum = decc.processScans.obtainStartNum(client, cursor)
    try:
        decc.processScans.processPhysical(deccinputdir + 'input.csv',
                                          deccoutputdir + 'output.csv', part,
                                          startNum, db, cursor)
        flash('Processing shipment complete', 'message')
        db.close()
    except IOError:
        db.close()
        flash('Error reading/writing file', 'error')
    return redirect('/decc')


@app.route('/decc/returned', methods=['GET', 'POST'])
def returned():
    files = os.listdir(deccinputdir)
    choices = []
    for file in files:
        choices.append((file, file))
    form = DECCReturned()
    form.inFileName.choices = choices
    if form.validate_on_submit():
        inFile = deccinputdir + form.inFileName.data
        outFile = deccoutputdir + form.outFileName.data + '.csv'
        isVR = form.isVR.data
        try:
            decc.processXLSX.main(isVR, inFile, outFile)
            flash('File output', 'message')
            return redirect('/decc')
        except (UnicodeError, KeyError) as error:
            flash('Error: ' + str(error), 'error')
        except IOError:
            flash('Error reading/writing file', 'error')
    return render_template('deccReturned.html',
                           form=form)


@app.route('/decc/email')
def email():
    typeName = request.args['typeName']
    startNum = '{:010}'.format(int(request.args['startNum']))
    endNum = '{:010}'.format(int(request.args['endNum']))
    numRecords = request.args['numRecords']
    numFiles = request.args['numFiles']
    client = request.args['client']
    rush = request.args['rush']
    return render_template('deccEmail.html',
                           typeName=typeName,
                           startNum=startNum,
                           endNum=endNum,
                           numRecords=numRecords,
                           numFiles=numFiles,
                           client=client,
                           rush=rush)


@app.route('/vip/query', methods=['GET', 'POST'])
def query():
    form = VITQuery()
    if form.validate_on_submit():
        voterInfo = civicInfo.getVoterInfo(form.address.data)
        return json.dumps(voterInfo, indent=4)
    return render_template('vitquery.html', form=form)
