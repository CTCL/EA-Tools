from csv import DictReader

def read(path, state):
  with open('{0}/{1}.csv'.format(path, state)) as inFile:
    drObject = DictReader(inFile)
    return list(drObject)
