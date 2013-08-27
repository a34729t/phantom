# Lightweight Firewall for Phantom

# Note:
# This code operates on ethernet frames, so there are > 2 layers of headers to
# examine- ethernet, ip, and possibly tcp/udp headers. The Firewall.examine()
# function is provided to help understand the packet structure without having
# to resort to scapy.
# See:
#   http://networkstatic.net/what-are-ethernet-ip-and-tcp-headers-in-wireshark-captures/

# Note:
# For converting the binary packet data into hex- use binascii python module 
# for optimal performance.
# Alternatively, to do it yourself, check out the following pieces of code:
#   http://mail.python.org/pipermail/tutor/2003-August/024701.html
#   https://gist.github.com/sbz/1080258

from binascii import hexlify

class Firewall:
    def __init__(self):
        # Protocol numbers
        # 6 - TCP
        # 17 - UDP
        # See:
        #   http://www.iana.org/assignments/protocol-numbers/protocol-numbers.xhtml
        self.allowed_protocols = set([6, 17])
    
    def arp_packet(self, frame):
        # TODO:
        return True
    
    def filter_outbound(self, frame):
        # Return False if we want to block the ethernet frame
        
        protocol = int(hexlify(frame[23:24]), 16)
        src_port = int(hexlify(frame[34:36]), 16)
        dst_port = int(hexlify(frame[36:38]), 16)
        print "filter_outbound:", "protocol=", protocol, "src_port=", src_port, "dst_port=", dst_port
        
        # TODO: Don't block ARP packets, which are a different format than the other stuff we expect
        # See: https://en.wikipedia.org/wiki/Ethertype
        if arp_packet(frame):
            return True
        elif protocol in allowed_protocols:
            return True
        else:
            return False
        
    def filter_inbound(self, frame):
        # Return False if we want to block the ethernet frame
        
        protocol = int(hexlify(frame[23:24]), 16)
        src_port = int(hexlify(frame[34:36]), 16)
        dst_port = int(hexlify(frame[36:38]), 16)
        print "filter_inbound:", "protocol=", protocol, "src_port=", src_port, "dst_port=", dst_port  
        
        return True

    @classmethod
    def examine(self, frame):
        # Get ethernet frame info, in hex. To get an integer, use:
        #   int(hex_value, 16)

        # Ethernet header
        print "Ethernet header (frame[0:14]):", hexlify(frame[0:14])
        print "dst_mac=", hexlify(frame[0:6])
        print "src_mac=", hexlify(frame[6:12])
        print "p_type=", hexlify(frame[12:14])

        # IP header
        print "IP header (frame[14:34]):", hexlify(frame[14:34])
        print "protocol=", hexlify(frame[23:24])
        print "src ip_addr=", hexlify(frame[26:30])
        print "dst ip_addr=", hexlify(frame[30:34])

        # TCP/UDP header (have src/dst port in same location)
        try:
            print "src_port", hexlify(frame[34:36])
            print "dst_port", hexlify(frame[36:38])
        except:
            pass