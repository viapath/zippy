# file gunicorn.conf.py
# coding=utf-8

import os
import multiprocessing

_LOGS = '/var/local/zippy'
errorlog = os.path.join(_LOGS, 'zippy_error.log')
accesslog = os.path.join(_LOGS, 'zippy_access.log')
loglevel = 'debug'
reload = False  # no autoreload to prevent code injection into running server
bind = '0.0.0.0:5000'
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 3 * 60  # timeout 3 minutes
keepalive = 24 * 60 * 60  # keep connections alive for 1 day
capture_output = True
