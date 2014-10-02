from flask.ext.wtf import Form
from wtforms import SelectField, BooleanField, TextField
from wtforms.validators import Required
from config import states, deccinputdir, ev_qa_data
import os, json

class SelectProgram(Form):
  choices = []
  for state in states:
    stateValues = (state, states[state])
    choices.append(stateValues)
  state = SelectField('state', choices = choices, validators = [Required()])


class optionSelector(Form):
  option = SelectField('option', coerce = int)


class orderSubmission(Form):
  formType = SelectField('formType', coerce = int)
  state = TextField('state')
  rush = BooleanField('rush')
  van = BooleanField('van')
  match = BooleanField('match')
  quad = BooleanField('quad')


class DECCReturned(Form):
  inFileName = SelectField('inFileName', validators = [Required()])
  outFileName = TextField('outFileName', validators = [Required()])
  isVR = BooleanField('isVR')


class VITQuery(Form):
  address = TextField('address')


class runEVQuery(Form):
  choices = []
  for filename in os.listdir(ev_qa_data):
    choices.append((filename, filename))
  state = SelectField('state', choices = choices)