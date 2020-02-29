#!/usr/bin/env python

__doc__=="""Zippy"""
__author__ = "David Brawand"
__license__ = "MIT"
__version__ = "2.3.4"
__maintainer__ = "David Brawand"
__email__ = "dbrawand@nhs.net"
__status__ = "Production"

import os
from flask import Flask, render_template, request, redirect
from celery import Celery
from werkzeug.utils import secure_filename

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
celery = make_celery(app)


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
