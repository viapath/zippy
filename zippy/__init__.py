#!/usr/bin/env python

__doc__=="""Zippy"""
__author__ = "David Brawand"
__license__ = "MIT"
__version__ = "2.3.4"
__maintainer__ = "David Brawand"
__email__ = "dbrawand@nhs.net"
__status__ = "Production"

from flask import Flask, render_template, request, redirect
from celery import Celery
from werkzeug.utils import secure_filename
import os, json

def make_celery(app):
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL']
    )
    celery.conf.update(app.config)

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

app = Flask(__name__)
app.config.update(
    CELERY_BROKER_URL='amqp://guest@localhost',
    #CELERY_RESULT_BACKEND='amqp://guest@localhost',
    CELERY_RESULT_BACKEND='amqp://',
)
app.config['ALLOWED_EXTENSIONS'] = set(['txt', 'batch', 'vcf', 'bed', 'csv', 'tsv'])
app.secret_key = 'Zippy is the best handpuppet out there'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'results'
app.config['CONFIG_FILE'] = os.environ.get("CONFIG_FILE", None)
if app.config['CONFIG_FILE'] is None:
    app.config['CONFIG_FILE'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'zippy.json')
#assert 0, (app.config['CONFIG_FILE'], os.environ.get("CONFIG_FILE", None))
celery = make_celery(app)
# read password (SHA1 hash, not the safest)
with open(app.config['CONFIG_FILE']) as conf:
    #config = json.load(conf, object_hook=ascii_encode_dict)
    config = json.load(conf)
    app.config['PASSWORD'] = config['password']


# app.debug = True  # /var/log/apache2/error.log
# app.config.from_object('config')
from . import views
@celery.task()
def add_together(a, b):
    return a + b
if __name__ == "__main__":
    result = add_together.delay(23, 42)
    print("ares", result.ready())
    #resv = result.wait()  # 65
    resv = result.get(timeout=1)  # 65
    print("bres", resv)
