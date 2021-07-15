from ipaddress import ip_address
import struct
from .enums import (
    OptionsEnum,
    SenderType,
    MessageType
)


from .exceptions import NoneOptionException


MAGIC_COOKIE = (99, 130, 83, 99)


class DHCPEncodedOptions:

    def __init__(self, id, value) -> None:

        if id == OptionsEnum.DHCPMESSAGETYPE:
            self.value = struct.pack("s", str(value).encode("ascii"))
            self.length = struct.pack("!B", 1)

        elif id in (
            OptionsEnum.IPADDRESSLEASETIME,
            OptionsEnum.SERVERIDENTIFIER
        ):
            self.value = struct.pack("!4s", str(value).encode("ascii"))
            self.length = struct.pack("!B", 4)

        self.id = id
        self.segment = struct.pack("!B", id) + self.length + self.value


class DHCPDecodedOtions:

    def __init__(self, id, value) -> None:
        self.id = id
        self.value = value


class DHCPMessage:
    op = SenderType.NONE  # client or server ?
    htype = 1  # ethernet
    hlen = 6  # ethernet
    hops = 0  # there is no relay agent in our network
    xid = 0  # random number chosen by the client
    secs = 0  # seconds from begining of process
    flags = 0  # can be set to 1 to indicate that messages to the client must be broadcast
    ciaddr = 0  # only for renew
    yiaddr = 0  # your ip address
    siaddr = 0  # ip address  of next server to use in bootstrap
    giaddr = 0  # relay agent address
    chaddr = 0  # physical address of client
    sname = 0  # optional
    message_type = 0
    lease_time = 0
    server_ip = 0
    options = []


class PacketParser:

    def pack(self, msg: DHCPMessage):
        res = bytearray(bytes(240))  # length of header

        # first pack header

        if msg.op == SenderType.NONE:
            raise NoneOptionException("select your option")

        struct.pack_into("!BBBB", res, 0, msg.op,
                         msg.htype, msg.hlen, msg.hops)

        struct.pack_into("!L", res, 4, msg.xid)

        struct.pack_into("!HH", res, 8, msg.secs, msg.flags)

        

        struct.pack_into("!LLLL", res, 12,
                         msg.ciaddr,
                         msg.yiaddr,
                         msg.siaddr,
                         msg.giaddr)
        

        struct.pack_into("!8xQ", res, 28, msg.chaddr)
        

        struct.pack_into("64s", res, 44, str(msg.sname).encode('ascii'))

        # no file field :)))

        struct.pack_into("!BBBB", res, 236, *MAGIC_COOKIE)

        for option in msg.options:
            res += option.segment

        res += struct.pack("!B", OptionsEnum.END)

        if len(res) < 300:
            res += (300 - len(res)) * struct.pack("!B", OptionsEnum.PAD)

        return res

    def unpack(self, data):
        msg = DHCPMessage()

        index = 0

        msg.op, msg.htype, msg.hlen, msg.hops = struct.unpack_from(
            "!BBBB", data, index)
        index = 4

        msg.xid = struct.unpack_from(
            "!L", data, index
        )[0]

        index = 8

        msg.secs, msg.flags = struct.unpack_from(
            "!HH", data, index
        )

        index = 12

        msg.ciaddr, msg.yiaddr, msg.siaddr, msg.giaddr = struct.unpack_from(
            "!LLLL", data, index
        )

        msg.ciaddr = self._decimalToIPAddress(msg.ciaddr) 
        msg.yiaddr = self._decimalToIPAddress(msg.yiaddr)
        msg.siaddr = self._decimalToIPAddress(msg.siaddr)
        msg.giaddr = self._decimalToIPAddress(msg.giaddr)



        index = 28

        msg.chaddr = struct.unpack_from("!8xQ", data, index)[0]
        msg.chaddr = self._decimalToMacAddress(msg.chaddr)


        index = 44

        msg.sname = struct.unpack_from("64s", data, index)

        index = 240

        while index < len(data):

            id = struct.unpack_from("!B", data, index)[0]
            index += 1

            if id == OptionsEnum.END:
                break

            if id == OptionsEnum.PAD:
                continue

            length = struct.unpack_from("!B", data, index)[0]

            index += 1

            value = struct.unpack_from(f"!{length}s", data, index)[0]

            index += length
            # print(id)
            # value = value.remove(b"\x00")
            # print(value)
            if id == OptionsEnum.DHCPMESSAGETYPE:
                msg.message_type = int(str(value , encoding="ascii"))
            elif id == OptionsEnum.IPADDRESSLEASETIME:
                msg.lease_time = int(str(value , encoding="ascii").strip("\x00"))
            elif id == OptionsEnum.SERVERIDENTIFIER:
                msg.server_ip = self._decimalToIPAddress(int(str(value , encoding="ascii")))
            else:
                msg.options.append(DHCPDecodedOtions(id, int(str(value , encoding="ascii"))))

        return msg

    def _ipaddressToDecimal(self, ip):
        return int(''.join(["{:02x}".format(int(i)) for i in ip.split(".")]), 16)

    def _MACAddressToDecimal(self, mac_address):
        return int(''.join(mac_address.split(":")), 16)

    def _decimalToIPAddress(self, data):
        packed = struct.pack("!L" , data)
        data = struct.unpack("!BBBB" , packed)
        
        return ".".join([str(int(d)) for d in data])
        
    def _decimalToMacAddress(self,data):
        packed = struct.pack("!Q" , data)
        data = struct.unpack("!2x6B" , packed)
        return ":".join(["{:02x}".format(int(d)) for d in data])

    def DHCPOFFER(self,
                  xid,
                  offerted_ip,
                  server_ip,
                  flags,
                  mac_address,
                  lease_time,
                  host_name=""):
        msg = DHCPMessage()

        msg.op = SenderType.SERVER
        msg.xid = xid
        msg.secs = 0
        msg.ciaddr = 0
        msg.yiaddr = self._ipaddressToDecimal(offerted_ip)
        msg.siaddr = self._ipaddressToDecimal(server_ip)
        msg.flags = flags
        msg.giaddr = 0
        msg.chaddr = self._MACAddressToDecimal(mac_address)
        msg.sname = host_name
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.IPADDRESSLEASETIME), lease_time))
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.DHCPMESSAGETYPE), int(MessageType.DHCPOFFER)))
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.SERVERIDENTIFIER), self._ipaddressToDecimal(server_ip)))

        return self.pack(msg)

    def DHCPACK(self,
                xid,
                offerted_ip,
                server_ip,
                flags,
                mac_address,
                lease_time,
                # client_addres , # only for renew 
                host_name=""
                ):

        msg = DHCPMessage()

        msg.op = SenderType.SERVER
        msg.xid = xid
        msg.secs = 0
        msg.ciaddr = 0
        msg.yiaddr = self._ipaddressToDecimal(offerted_ip)
        msg.siaddr = self._ipaddressToDecimal(server_ip)
        msg.flags = flags
        msg.giaddr = 0
        msg.chaddr = self._MACAddressToDecimal(mac_address)
        msg.sname = host_name
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.IPADDRESSLEASETIME), lease_time))
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.DHCPMESSAGETYPE), int(MessageType.DHCPACK)))
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.SERVERIDENTIFIER), self._ipaddressToDecimal(server_ip)))

        return self.pack(msg)
    
    def DHCPNACK(self,
                xid,
                offerted_ip,
                server_ip,
                flags,
                mac_address,
                # client_addres , # only for renew 
                host_name=""
                ):

        msg = DHCPMessage()

        msg.op = SenderType.SERVER
        msg.xid = xid
        msg.secs = 0
        msg.ciaddr = 0
        msg.yiaddr = self._ipaddressToDecimal(offerted_ip)
        msg.siaddr = self._ipaddressToDecimal(server_ip)
        msg.flags = flags
        msg.giaddr = 0
        msg.chaddr = self._MACAddressToDecimal(mac_address)
        msg.sname = host_name
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.DHCPMESSAGETYPE), int(MessageType.DHCPNAK)))
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.SERVERIDENTIFIER), self._ipaddressToDecimal(server_ip)))

        return self.pack(msg)


    def DHCPDISCOVER(self,
                xid,
                flags,
                mac_address,
                client_address = 0
                ):

        msg = DHCPMessage()

        msg.op = SenderType.CLIENT
        msg.xid = xid
        msg.secs = 0
        msg.ciaddr = 0
        msg.yiaddr = 0
        msg.siaddr = 0
        msg.flags = flags
        msg.giaddr = 0
        msg.chaddr = self._MACAddressToDecimal(mac_address)
        msg.sname = ""
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.DHCPMESSAGETYPE), int(MessageType.DHCPDISCOVER)))

        return self.pack(msg)


    def DHCPREQUEST(self,
                xid,
                server_ip,
                flags,
                mac_address,
                client_addres , # only for renew 
                ):

        msg = DHCPMessage()

        msg.op = SenderType.SERVER
        msg.xid = xid
        msg.secs = 0
        msg.ciaddr = self._ipaddressToDecimal(client_addres)
        msg.yiaddr = self._ipaddressToDecimal(client_addres)
        msg.siaddr = self._ipaddressToDecimal(server_ip)
        msg.flags = flags
        msg.giaddr = 0
        msg.chaddr = self._MACAddressToDecimal(mac_address)
        msg.sname = ""
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.DHCPMESSAGETYPE), int(MessageType.DHCPREQUEST)))
        msg.options.append(DHCPEncodedOptions(
            int(OptionsEnum.SERVERIDENTIFIER), self._ipaddressToDecimal(server_ip)))

        return self.pack(msg)
    
    
    

