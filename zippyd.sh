#!/bin/sh
python -mplatform | grep -qi Ubuntu && (service apache2 start; tail -f /var/log/apache2/error.log) || (systemctl httpd start; tail -f /var/log/httpd/error_log) 

