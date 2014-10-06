from flask import Flask

app = Flask(__name__)
app.config.from_object('config')
app.debug = False

#if not app.debug:
import logging
from logging.handlers import RotatingFileHandler
file_handler = RotatingFileHandler('/tmp/ea-errors.log')
file_handler.setLevel(logging.WARNING)
app.logger.addHandler(file_handler)

from app import views
