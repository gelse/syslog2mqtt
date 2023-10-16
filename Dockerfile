FROM python:3.11.6-alpine3.18
MAINTAINER Werner Schiller <github@gelse.net>

RUN pip install paho-mqtt pyparsing
COPY ./syslog2mqtt.py /root/syslog2mqtt.py
EXPOSE 514
CMD ["python","/root/syslog2mqtt.py"]
