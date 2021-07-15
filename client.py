from service.service import DHCPClient
import json
import random

with open("sc_config.json" , 'r') as f:
    conf = json.load(f)
    

mac_address= f'54:e1:ad:e9:8d:{random.randint(10,99)}'

print(mac_address)    

client = DHCPClient(mac_address=mac_address,
                    client_port=conf['client_port'],
                    server_port=conf['server_port'],
                    buffer_size=conf['buffer_size'])

client.start()