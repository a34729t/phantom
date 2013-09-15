import logging
from socket import socket, AF_INET, SOCK_DGRAM, SOCK_STREAM
from routingpath import RoutingPath, Node, NodeTypes
from crypto_factory import CryptoFactory
from dht import FakeDHT

log = logging.getLogger("mylog")
MAX_BUFFER_SIZE = 65535
BACKLOG = 5 

class Listener(object):
    def __init__(self, addr, dht, node):
        # Initialize vars
        self.addr = addr
        self.dht = dht
        self.node = node
        
        # Initialize data structures
        self.peers = {}
        self.conns = {}
        self.entry_paths = []
        self.exit_paths = []
        # NOTE: We do a crypto factory per listener, as a listener is kind of like a phantom
        # instance within a phantom instance
        self.crypto = CryptoFactory()
        self.crypto.path_building_key = self.node.path_building_key # hide the key from operations
        
        # Creat a listening socket
        self.init_socket()
        
    def init_socket(self):
        pass
        
    def generate_path(self):
        path = RoutingPath(self.node, self.dht, self.crypto, 3)
        self.exit_paths.append(path)
        
        msg = path.round1_setup_packages()
        log.debug("Creating path with nodes:"+str(path.nodes))
        
        # Send a setup message to the first node in the path
        target_node = path[1]
        log.debug("len of package:"+str(len(msg))+" dest:"+str(target_node.port))
        return target_node, msg

class TCPListener(Listener):
    
    # Path Setup:
    # Basically, the node that wants to build a path fires setup_round_1(). The
    # target node receives the incoming data via handle_conn_data() after the
    # TCP conection has been established and then checks to see if the node
    # which has made the request is already a peer. If not, the node then 
    # performs it's portion of the round 1 setup.
    
    def init_socket(self):
        # Initialize listening non-blocking UDP socket
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setblocking(0)
        sock.bind(self.addr)
        sock.listen(BACKLOG) 
        self.sock = sock
        log.debug("Opening TCP Listener on" + str(self.addr))
        
    def handle_incoming(self, event_loop_inputs):
        conn, addr = self.sock.accept() 
        event_loop_inputs.append(conn)
        print "Accepted connection:", addr
            
    def handle_conn_data(self, conn, event_loop_inputs):
        print "Type of conn.recv", type(conn)
        data = conn.recv(MAX_BUFFER_SIZE)
        if not data:
            conn.close() 
            event_loop_inputs.remove(conn) 
        else:
            # log.debug("TCP len:"+str(len(data))+": "+data)
            if conn not in self.peers:
                # Assume round 1 setup
                box, plaintext = RoutingPath.round1_setup_packages_decode(data, self.crypto)
                print "plaintext", plaintext
                
                # Open up package and examine it? How do we store the path component info?
                # 1) Parse the incoming packet
                # 2) Process the info
                # 3) Send the package to the next node in the path
                
                
            else:
                print "peer known", addr
            
    def setup_round_1(self):
        target_node, msg = self.generate_path()
        # TODO: Open a connection to other node!
        client_sock = socket(AF_INET, SOCK_STREAM)
        client_sock.connect((target_node.ip_addr, target_node.port))
        
        log.debug("Open TCP conn to:"+ str((target_node.ip_addr, target_node.port)))
        client_sock.sendall(msg)
        self.peers[client_sock] = (target_node.ip_addr, target_node.port)



class UDPListener(Listener):
    # NOTE: Incomplete- we'll need some sort of pseudo-TCP implementation to make the setup
    # portion reliable. This is probably a pain in the ass to implement

    def init_socket(self):
        # Initialize listening non-blocking UDP socket
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.setblocking(0)
        sock.bind(self.addr)
        self.sock = sock
        
    def handle_incoming(self):
        (data, addr) = self.sock.recvfrom(MAX_BUFFER_SIZE)
        log.debug("UDP addr:"+str(addr)+" len:"+str(len(data))+": "+data)
        
        if addr not in self.peers:
            box, plaintext = RoutingPath.round1_setup_packages_decode(data, self.crypto)
            print "plaintext", plaintext
        else:
            print "peer known", addr
        
    def setup_round_1(self):
        target_node, msg = self.generate_path()
        self.sock.sendto(msg, (target_node.ip_addr, target_node.port))
        
        
        
    def setup_round_2(self):
        pass
        
    def respond_setup_round_1(self):
        pass
        
    def respond_setup_round_1(self):
        pass