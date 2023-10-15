from socket import *
from pyparsing import Word, alphas, Suppress, Combine, nums, string, Optional, Regex
from time import strftime
import paho.mqtt.client as mqtt
import syslog
import os
import json

#MQTT Parameters
mqtt_server = os.getenv('MQTT_SERVER')
mqtt_port = os.getenv('MQTT_PORT') or 1883
mqtt_client_id = os.getenv('MQTT_CLIENTID') or 'syslog2mqtt'
mqtt_username = os.getenv('MQTT_USERNAME') or None
mqtt_password = os.getenv('MQTT_PASSWORD') or None
mqtt_topic = os.getenv('MQTT_TOPIC') or 'syslog2mqtt/data'
mqtt_retain = os.getenv('MQTT_RETAIN') in ['true', 'True', '1', 1, 'y', 'Y', 'yes', 'Yes', 'YES']
mqtt_verbose = os.getenv('MQTT_VERBOSE') in ['true', 'True', '1', 1, 'y', 'Y', 'yes', 'Yes', 'YES']


print('mqtt_server: %s' % mqtt_server)
print('mqtt_port: %s' % mqtt_port)
print('mqtt_client_id: %s' % mqtt_client_id)
print('mqtt_username: %s' % mqtt_username)
print('mqtt_password: %s' % mqtt_password)
print('mqtt_topic: %s' % mqtt_topic)
print('mqtt_retain: %s' % mqtt_retain)
print('mqtt_verbose: %s' % mqtt_verbose)


class Parser(object):
  def __init__(self):
    ints = Word(nums)

    # priority
    priority = Suppress("<") + ints + Suppress(">")

    # timestamp
    month = Word(string.ascii_uppercase , string.ascii_lowercase, exact=3)
    day   = ints
    hour  = Combine(ints + ":" + ints + ":" + ints)
    
    timestamp = month + day + hour

    # hostname
    hostname = Word(alphas + nums + "_" + "-" + ".")

    # appname
    appname = Word(alphas + nums + "/" + "-" + "_" + ".") + Optional(Suppress("[") + ints + Suppress("]")) + Suppress(":")

    # message
    message = Regex(".*")
  
    # pattern build
    self.__pattern = priority + timestamp + hostname + appname + message
    
  def parse(self, line):
    parsed = self.__pattern.parseString(line)

    payload              = {}
    payload["priority"]  = parsed[0]
    payload["timestamp"] = strftime("%Y-%m-%d %H:%M:%S")
    payload["hostname"]  = parsed[4]
    payload["appname"]   = parsed[5]
    if len(parsed) == 7:
        payload["message"]   = parsed[6]
    else:
        payload["pid"]       = parsed[6]
        payload["message"]   = parsed[7]
    
    return payload

class MqttClient():
    def __init__(self):
        self.__mqttclient = mqtt.Client(client_id=mqtt_client_id, clean_session=True)
        self.__mqttclient.username_pw_set(mqtt_username,mqtt_password)
        self.__mqttclient.connect(mqtt_server,mqtt_port,keepalive=60)
    
    def publish(self, fields):
        self.__mqttclient.publish(mqtt_topic + '/' + fields['hostname'] + '/' + fields['appname'],payload=json.dumps(fields),qos=0,retain=mqtt_retain)

    def publishraw(self, data):
        self.__mqttclient.publish(mqtt_topic + '/raw',payload=data,qos=0,retain=mqtt_retain)
    
    def disconnect(self):
        if self.__mqttclient:
            self.__mqttclient.disconnect()

    def __del__(self):
        self.disconnect()

if __name__ == "__main__":
    parser = Parser()

    #Syslog Parameters
    #Insert IP of server listener. 0.0.0.0 for any
    server = "0.0.0.0"
    #syslog port
    port = 514
    buf = 8192*4
    listen_addr = (server,port)

    #Open Syslog Socket
    print('Opening syslog socket: %s/%s' % (server,port))
    try:
        TCPSock = socket(AF_INET,SOCK_DGRAM)
        TCPSock.bind(listen_addr)
        if TCPSock.bind:
            print('Opened syslog socket: %s/%s' % (server,port))

        #MQTT client
        if mqtt_server:
            print('Opening MQTT socket: %s/%s' % (mqtt_server,mqtt_port))
            mqttclient = MqttClient()
            if mqttclient:
                print('Opened MQTT socket: %s/%s' % (mqtt_server,mqtt_port))
            else:
                exit(1)
        else:
            print('Missing mqtt server address, use the MQTT_SERVER env variable. Skipping mqtt.')


        while 1:
            data,addr = TCPSock.recvfrom(buf)
            if not data:
                print ("No response from systems!")
                break
            else:
                if mqtt_verbose:
                    print("%s: %s" % (addr, data))

                try:
                    strdata = data.decode('utf-8')
                    fields = parser.parse(strdata)
                except:
                    print ('Could not parse from %s data: %s' % (addr,data))
                    if mqttclient:
                        mqttclient.publishraw(strdata)
                else:
                    if mqttclient:
                        mqttclient.publish(fields)
                
    finally:
        if TCPSock:
            TCPSock.close()
        if mqttclient:
            mqttclient.disconnect()
