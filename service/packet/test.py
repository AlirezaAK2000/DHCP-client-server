from parsers import PacketParser, DHCPMessage, DHCPEncodedOptions, DHCPDecodedOtions


parser = PacketParser()

msg = DHCPMessage()

msg.op = 1
msg.xid = 1234
msg.secs = 321
msg.flags = 1
msg.ciaddr = parser._ipaddressToDecimal('123.123.123.123')
msg.yiaddr = parser._ipaddressToDecimal('21.21.21.21')
msg.siaddr = parser._ipaddressToDecimal("23.23.32.23")
msg.giaddr = parser._ipaddressToDecimal("12.32.12.32")
msg.chaddr = parser._MACAddressToDecimal("12:32:23:12:12:12")

msg.options.append(DHCPEncodedOptions(53,7))

res = parser.DHCPDISCOVER(
                xid=msg.xid,
                flags = msg.flags,
                mac_address = "12:32:23:12:12:12",
                client_address = 0
                )

msg = parser.unpack(res)

print(f"op : {msg.op}")
print(f"xid : {msg.xid}")
print(f"secs : {msg.secs}")
print(f"flags : {msg.flags}")
print(f"ciaddr : {msg.ciaddr}")
print(f"yiaddr : {msg.yiaddr}")
print(f"siaddr : {msg.siaddr}")
print(f"giaddr : {msg.giaddr}")
print(f"chaddr : {msg.chaddr}")

for option in msg.options:
    print(f"code : {option.id} , value : {option.value}")
