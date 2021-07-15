import socket

import threading

from .packet import PacketParser
from .packet import MessageType

from .model.db import Mapping

from .tools.addressing import AddressPool

from datetime import datetime, timedelta
import random
import time
from .enums import ClientState

import datetime

class DHCPServer:

    def __init__(self, config , ip , server_port , client_port , buffer_size) -> None:
        self.server_info = (ip, server_port)
        
        self.buffer_size = buffer_size
        
        self.config = config
        
        self.socket_lock = threading.Lock()
        
        self.lease_time = timedelta(seconds=self.config['lease_time'])

        self.parser = PacketParser()

        self.sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_DGRAM,
            socket.IPPROTO_UDP
        )
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        self.sock.bind(('' , server_port))
        
        if config['pool_mode'] == 'range':
            self.pool = AddressPool(
                pool_mode=config['pool_mode'],
                rangge=config['range'],
                reservation_list=config['reservation_list'].values(),
            )
        else:
            self.pool = AddressPool(
                pool_mode=config['pool_mode'],
                rangge=config['subnet'],
                reservation_list=config['reservation_list'].values(),
            )
            
        self.black_list= set(self.config['black_list'])
        
        self.offered = set()
        
        self.expire_handler = threading.Thread(target=self.handle_expired)
        
        self.expire_handler.start()
        
        self.broadcast_ip = '<broadcast>'
            
        self.client_port = client_port

    def handle_request(self, data):
        
        msg = self.parser.unpack(data)
        
        if msg.chaddr in self.black_list:
            return
        
        if msg.message_type == MessageType.DHCPDISCOVER:
            mac_address = msg.chaddr
            mapped_ip = Mapping.select().where(Mapping.mac_address == mac_address)
            offered_ip = None
            if len(mapped_ip) == 0:
                offered_ip = self.pool.get_ip()
            else:
                offered_ip = mapped_ip[0].ip_address
            self.offered.add(offered_ip)
            response = self.parser.DHCPOFFER(
                msg.xid,
                offerted_ip=offered_ip,
                flags=msg.flags,
                mac_address=mac_address,
                server_ip=self.server_info[0],
                lease_time=self.config['lease_time']
                
            )
            
            self._send_response(response)
        
        elif msg.message_type == MessageType.DHCPREQUEST:
            server_ip = msg.siaddr
            mac_address = msg.chaddr
            # if server_ip != self.server_info[0]:
            #     return
            # add to database 
            self.offered.remove(msg.yiaddr)
            
            q = Mapping.select().where(
                Mapping.ip_address == msg.yiaddr
            )
            occupied = False
            if q:
                occupied = q[0].mac_address != mac_address
            if not occupied:
                mapped_ip = Mapping.select().where(Mapping.mac_address == mac_address)
                if len(mapped_ip) == 0:
                    Mapping.create(
                    mac_address = msg.chaddr,
                    ip_address = msg.yiaddr,
                    lease_time= self.config['lease_time'] 
                    )
                else:
                    Mapping.update({Mapping.map_date : datetime.now()}).where(
                        Mapping.mac_address == mac_address
                    )
                
                response = self.parser.DHCPACK(
                    xid=msg.xid,
                    offerted_ip=msg.yiaddr,
                    server_ip=msg.siaddr,
                    flags=msg.flags,
                    mac_address=msg.chaddr,
                    lease_time=self.config['lease_time'],
                    
                )
                
                self._send_response(response)
            else:
                print(f"ip {msg.yiaddr} is in use")
                for i in q:
                    print(f"mac {i.mac_address} ip : {i.ip_address}")
                response = self.parser.DHCPNACK(
                    xid=msg.xid,
                    offerted_ip=msg.yiaddr,
                    server_ip=msg.siaddr,
                    flags=msg.flags,
                    mac_address=msg.chaddr,
                    
                )
                self._send_response(response)
                
        
        else:
            print("not emplemented DHCP message !!! ")
        

    def _send_response(self, response):
        with self.socket_lock:
            self.sock.sendto(response, (self.broadcast_ip,self.client_port))
        

    def listen(self):

        print("listening : ")
        try:
            while True:
                data, _ = self.sock.recvfrom(self.buffer_size)


                client_handler = threading.Thread(
                    target=self.handle_request,
                    args=(data,)
                )

                client_handler.daemon = True

                client_handler.start()
            

        except KeyboardInterrupt:
            self.sock.close()
            
        
        
    def handle_expired(self):
        while True:    
            expired = Mapping.select().where(Mapping.map_date <  datetime.now() - self.lease_time)
            
            for ex in expired:
                self.pool.add_to_pool(ex.ip_address)
                print(f"ip {ex.ip_address} is expired")
                ex.delete_instance()
                
            # time.sleep(1)
            time.sleep(self.lease_time.seconds * 10)
        
class DHCPClient:
    
    def __init__(self,mac_address , client_port , server_port , buffer_size) -> None:
        self.mac_address = mac_address
        
        self.buffer_size = buffer_size
        
        self.state = ClientState.INIT
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        self.client_port = client_port
        
        self.server_port= server_port
        
        self.lock = threading.Lock()
        
        self.sock.bind(("0.0.0.0" , self.client_port))
        
        self.initial_invterval = 10
        
        self.backoff_cutoff = 120
        
        self.parser = PacketParser()
        
        self.xid_generator = random.SystemRandom()
        
        self.xid = 0
        
        self.dis_time = None
        
        self.lease_time = 0
        
        self.ip = '0.0.0.0'
        
        self.broadcast_ip = '<broadcast>'
        
        self.assignment_time = 0
        
        self.choosed_server = 0
        
        
    def start(self):
        print("*** starting address assignment ***")
        self._set_state(ClientState.DISCOVER)
        
        try:
            while True:
                
                if self.state == ClientState.DISCOVER:
                    print('state : discover')
                    self.xid = self.xid_generator.randint(0 , 2**32)
                    print(f"xid : {self.xid}")
                    pak = self.parser.DHCPDISCOVER(
                        xid=self.xid,
                        flags=1,
                        mac_address=self.mac_address
                    )
                    
                    self.sock.sendto(pak , (self.broadcast_ip , self.server_port))
                    
                    self._set_state(ClientState.OFFER)
                    self.dis_time = datetime.datetime.now()
                    
                    threading.Timer(self.initial_invterval , self.timeout_handler).start()
                    
                
                elif self.state == ClientState.OFFER:
                    print('state : offer')
                    
                    try:
                        self.sock.settimeout(self.initial_invterval)
                        res = self.sock.recv(self.buffer_size)
                        msg = self.parser.unpack(res)
                        if msg.message_type == MessageType.DHCPOFFER and msg.xid == self.xid:
                            # self.ip = msg.yiaddr
                            # self.lease_time = msg.lease_time
                            self.choosed_server = msg.server_ip
                            pak = self.parser.DHCPREQUEST(
                                xid = self.xid,
                                server_ip=msg.server_ip,
                                flags=1,
                                mac_address=self.mac_address,
                                client_addres=msg.yiaddr
                            )
                            self.sock.sendto(pak , (self.broadcast_ip , self.server_port))
                            self._set_state(ClientState.ACK)
                        
                    except socket.timeout:
                        print("time out !!!")
                
                elif self.state == ClientState.ACK:
                    print("state : ack")
                    try:
                        self.sock.settimeout(self.initial_invterval)
                        res = self.sock.recv(self.buffer_size)
                        msg = self.parser.unpack(res)
                        if msg.message_type == MessageType.DHCPACK and msg.xid == self.xid and self.choosed_server==msg.server_ip:
                            print("new address !!!")
                            self.ip = msg.yiaddr
                            self.lease_time = datetime.timedelta(seconds = msg.lease_time)
                            self.assignment_time = datetime.datetime.now()
                            self._set_state(ClientState.ASSIGNED)
                            print(f"your address is {self.ip}")
                        
                    except socket.timeout:
                        print("time out !!!")
                
                elif self.state == ClientState.ASSIGNED:
                    pass
                
        
        except KeyboardInterrupt:
            self.sock.close()
        
        
    def timeout_handler(self):
        if self.state != ClientState.ASSIGNED:
            self._set_state(ClientState.DISCOVER)
            self.initial_invterval = min(self.backoff_cutoff , 2 * self.initial_invterval * random.random())    
        else:
            if datetime.datetime.now() - self.assignment_time > self.lease_time:
                self._set_state(ClientState.DISCOVER)
            else:
                threading.Timer(self.initial_invterval , self.timeout_handler).start()
                
        
        
        
    
    def _set_state(self,state):
        with self.lock:
            self.state = state