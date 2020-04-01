# file gunicorn.conf.py
# coding=utf-8

import os
import multiprocessing

_VAR = '/var'
errorlog = os.path.join(_VAR, 'log/zippy_error.log')
accesslog = os.path.join(_VAR, 'log/zippy_access.log')
loglevel = 'info'
bind = '0.0.0.0:5000'
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 3 * 60  # timeout 3 minutes
keepalive = 24 * 60 * 60  # keep connections alive for 1 day
capture_output = True

