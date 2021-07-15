

import struct
from typing import Dict, List
from .exceptions import InvalidArguments
from collections import  deque
from ipaddress import IPv4Address
RANGE = 'range'
SUBNET = 'subnet'




class AddressPool:
    
    def __init__(self ,
                 pool_mode , 
                 rangge:Dict=None ,
                 subnet:Dict=None ,
                 reservation_list:List = None) -> None:
        
        self.pool_mode = pool_mode
        self.reservation_list= reservation_list
        self.pool = deque()
        
        
        if self.pool_mode == RANGE:
            if rangge == None:
                raise InvalidArguments("range mode needs range config!!!")
            
            self.conf = rangge
            fromm = IPv4Address(rangge['from'])
            to = IPv4Address(rangge['to'])
            start = fromm
            while start != to:
                self.pool.append(str(start))
                start += 1
                
            
            
        elif self.pool_mode == SUBNET:
            if subnet == None:
                raise InvalidArguments("subnet mode needs subnet config!!!")
                
            self.conf= subnet
            start = IPv4Address(subnet['ip_block']) + 1
            subnet = subnet['subnet']
            
            subnet = (int(s) for s in subnet.split("."))
            subnet = struct.pack("!BBBB" , *subnet)
            subnet = struct.unpack("!I" , subnet)[0]
            
            number_of_addresses = 0
            i = 0
            while subnet % 2 != 1:
                number_of_addresses += 1 << i
                subnet = subnet >> 1
                i += 1
                
            for ii in range(number_of_addresses):
                self.pool.append(str(start + ii))
            
        else:
            raise InvalidArguments(f"invalid mode {self.pool_mode}!!!")
        
        for ip in reservation_list:
            self.pool.remove(ip)
        
        
        
    def get_ip(self):
        return self.pool.popleft()
    
    def add_to_pool(self, ip):
        if ip not in self.pool:
            self.pool.append(ip)
        
               
                
        