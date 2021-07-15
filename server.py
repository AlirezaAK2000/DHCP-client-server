from peewee import with_metaclass
from service.service import DHCPServer
import json

with open("config.json" , 'r') as file:
    config = json.load(file)

with open("sc_config.json" , 'r') as f:
    conf = json.load(f)
    

DHCPServer(config,ip=conf['server_ip'],
           server_port=conf['server_port'],
           client_port=conf['client_port'],
           buffer_size=conf['buffer_size']
           ).listen()