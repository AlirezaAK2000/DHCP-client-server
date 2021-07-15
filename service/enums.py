import enum 



class ClientState(enum.IntEnum):
    
    
    INIT = 0
    DISCOVER = 1
    OFFER = 2
    ACK = 3
    ASSIGNED = 4
    