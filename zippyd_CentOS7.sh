#!/bin/sh
systemctl httpd start
tail -f /var/log/httpd/error_log
