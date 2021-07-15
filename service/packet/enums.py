import enum


class MessageType(enum.IntEnum):
    DHCPDISCOVER = 1
    # Client broadcast to locate available servers.

    DHCPOFFER = 2
    # Server to client in response to DHCPDISCOVER with
    # offer of configuration parameters.

    DHCPREQUEST = 3
    # Client message to servers either (a) requesting
    # offered parameters from one server and implicitly
    # declining offers from all others, (b) confirming
    # correctness of previously allocated address after,
    # e.g., system reboot, or (c) extending the lease on a
    # particular network address.

    DHCPACK = 4
    # Server to client with configuration parameters,
    # including committed network address.

    DHCPNAK = 5
    # Server to client indicating client's notion of network
    # address is incorrect (e.g., client has moved to new
    # subnet) or client's lease as expired

    DHCPDECLINE = 6
    # Client to server indicating network address is already
    # in use.

    DHCPRELEASE = 7
    # Client to server relinquishing network address and
    # cancelling remaining lease.
    
    
    DHCPINFORM = 8
    # Client to server, asking only for local configuration
    # parameters; client already has externally configured
    # network address.
    
    NONE = 9
    
    
    
class SenderType(enum.IntEnum):
    
    SERVER = 2
    
    CLIENT = 1
    
    NONE = 3
    
    
    
class OptionsEnum(enum.IntEnum):
    DHCPMESSAGETYPE = 53
#       Code   Len  Type
#    +-----+-----+-----+
#    |  53 |  1  | 1-7 |
#    +-----+-----+-----+
    
    
    IPADDRESSLEASETIME = 51
#       Code   Len         Lease Time
#    +-----+-----+-----+-----+-----+-----+
#    |  51 |  4  |  t1 |  t2 |  t3 |  t4 |
#    +-----+-----+-----+-----+-----+-----+


    SERVERIDENTIFIER = 54 
#     Code   Len            Address
#    +-----+-----+-----+-----+-----+-----+
#    |  54 |  4  |  a1 |  a2 |  a3 |  a4 |
#    +-----+-----+-----+-----+-----+-----+


    END = 255
    
    PAD = 0