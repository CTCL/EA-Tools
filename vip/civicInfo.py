from config import api_key
import requests
import json


def getVoterInfo(address, electionID=4100):
    payload = {
        'address': address, 'key': api_key, 'productionDataOnly': 'false'
    }
    if electionID:
        payload['electionId'] = electionID
    r = requests.get('https://www.googleapis.com/civicinfo/v2/voterinfo',
                     params=payload)
    return json.loads(r.text)


def getVIPValues(data):
    ppid = ''
    name = ''
    address = ''
    if 'pollingLocations' in data:
        pollingList = data['pollingLocations']
        for item in pollingList:
            if len(ppid) > 0:
                ppid += ';'
            if len(name) > 0:
                name += ';'
            if len(address) > 0:
                address += ';'
            values = item['address']
            line2 = ''
            line3 = ''
            if 'line2' in values:
                line2 = values['line2']
            if 'line3' in values:
                line3 = values['line3']
            zipCode = '{:05d}'.format(int(values['zip']))
            address = '{0} {1} {2} {3}, {4} {5}'.format(values['line1'],
                                                        line2, line3,
                                                        values['city'],
                                                        values['state'],
                                                        zipCode)
            address += address.replace('     ', ' ').replace('    ', ' ')
            name += values['locationName']
    return ppid, address, name


def getEVValues(data):
    name = ''
    address = ''
    startDate = ''
    endDate = ''
    hours = ''
    count = 0
    if 'earlyVoteSites' in data:
        evInfo = data['earlyVoteSites']
        for place in evInfo:
            addressValues = place['address']
            if count > 0:
                address += ';'
                startDate += ';'
                endDate += ';'
                hours += ';'
                name += ';'
            count += 1
            line1 = addressValues['line1']
            line2 = ''
            line3 = ''
            city = addressValues['city']
            state = addressValues['state']
            zip = addressValues['zip']
            if 'line2' in addressValues:
                line2 = addressValues['line2']
            if 'line3' in addressValues:
                line3 = addressValues['line3']
            address += '{0} {1} {2} {3}, {4} {5}'.format(line1, line2, line3,
                                                         city, state, zip)
            address = address.replace('     ', ' ').replace('    ', ' ')
            address = address.replace(';', '\;')
            hours += place['pollingHours'].replace(';', '\;')
            startDate += place['startDate'].replace(';', '\;')
            endDate += place['endDate'].replace(';', '\;')
            name += place['name']
    return name, address, startDate, endDate, hours
