from readData import read
from civicInfo import getVoterInfo, getVIPValues, getEVValues
from config import vipTemplateKey, evTemplateKey
from config import vip_qa_data, ev_qa_data
import sheets
import geocode


def getRowData(row):
    address = '{0} {1} {2} {3} {4} {5} {6} {7}, {8} {9}'
    address = address.format(row['vf_reg_cass_street_num'],
                             row['vf_reg_cass_pre_directional'],
                             row['vf_reg_cass_street_name'],
                             row['vf_reg_cass_street_suffix'],
                             row['vf_reg_cass_post_directional'],
                             row['vf_reg_cass_unit_designator'],
                             row['vf_reg_cass_apt_num'],
                             row['vf_reg_cass_city'],
                             row['vf_reg_cass_state'],
                             '{:05d}'.format(int(row['vf_reg_cass_zip'])))
    address = address.replace('     ', ' ').replace('    ', ' ')
    address = address.replace('   ', ' ').replace('  ', ' ')
    county = row['vf_county_name']
    return address, county


def VIP(state, creds):
    name = state.replace('.csv', '')
    sheet = sheets.copySheet(name, vipTemplateKey, creds)
    client = sheets.getClient()
    stateData = read(vip_qa_data, state)
    exec('import ' + state)
    for row in stateData:
        address, county = getRowData(row)
        info = getVoterInfo(address)
        gppid, gaddress, gname = getVIPValues(info)
        sosppid, sosname, sosaddress = eval(state + ".run(row)")
        rowDict = {
            'County': county, 'Address Run': address, 'SOS PP ID': sosppid,
            'SOS PP NAME': sosname, 'SOS PP ADDRESS': sosaddress,
            'Google PP ID': gppid, 'Google PP Name': gname,
            'Google PP Address': gaddress
        }
        try:
            glocation = geocode.geocode(gaddress)
            soslocation = geocode.geocode(sosaddress)
            if glocation is not None and soslocation is not None:
                distance = geocode.haversine(glocation, soslocation)
                rowDict['SOS Location'] = str(soslocation)
                rowDict['Google Location'] = str(glocation)
                rowDict['Distance'] = str(distance)
        except Exception:
            pass
        while True:
            try:
                sheets.writeRow(rowDict, client, sheet['id'])
                break
            except Exception:
                pass
    return sheet['id']


def EVIP(state, creds, half=True):
    name = state.replace('.csv', '')
    sheet = sheets.copySheet(name, evTemplateKey, creds)
    client = sheets.getClient()
    stateData = read(ev_qa_data, name)
    for row in stateData:
        if not half or row['in25'] == 'TRUE':
            address, county = getRowData(row)
            info = getVoterInfo(address)
            gname, gaddress, gstart, gend, gtime = getEVValues(info)
            rowDict = {
                'County': county, 'Address Run': address,
                'Google PP Name': gname, 'Google PP Address': gaddress,
                'Google PP Start Date': gstart, 'Google PP End Date': gend,
                'Google PP Time': gtime
            }
            while True:
                try:
                    sheets.writeRow(rowDict, client, sheet['id'])
                    break
                except Exception:
                    pass
    return sheet['id']
