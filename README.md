# syslog2mqtt
A simple rsyslog server that forwards syslog entries to an MQTT server.

You can use the example docker compose file after changing (or removing) the template environment values accordingly.  

The server tries to do very basic parsing of the log messages and pushes the MQTT messages to <<base_topic>>/data/<<source>>/<<appname>>. If parsing fails, the message as a whole is pushed to <<base_topic>>/raw.

## planned features
- Extending the parsing possibilites with plugins.
