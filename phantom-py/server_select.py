#!/usr/local/bin/python2.7

import sys
import select # for select, epoll, kqueue
from socket import socket, AF_INET, SOCK_DGRAM
from multiprocessing import Process, Pipe
from server_datatypes import SetupInfo, TunnelInfo
import os
import logging

from routingpath import RoutingPath, Node, NodeTypes
from crypto_factory import CryptoFactory
from dht import FakeDHT

log = logging.getLogger("mylog")

# Design:
# Listens for incoming UDP data, processes it, and builds routing paths along
# which we can build UDP tunnels

class Server:
#     def __init__(self, pipe, pipe_test, name):
#         self.pipe = pipe # pipe for communication with external processes (ui)
#         self.pipe_test = pipe_test # pipe for communicating with test harness
#         
#         # NOTE: Temporary data for node name. We use it as the key for the fake
#         # dht lookup. I'm not really sure what will replace this! Probably a
#         # curl request to whatismyip.com or something!?
#         self.name = name
#         
#         # NOTE: The tunnels group of peers is a hack to make sure we can build 
#         # encrypted tunnels between two nodes. Once routing path construction
#         # is working, then we'll have exit, entry and intermediate peers.
#         
#         self.setup_peers = {} # setup connections this peer is attempting
#         self.tunnels = {} # tunnels we are routing over our node

    def __init__(self, name, pipe=None, pipe_test=None):
        dht_file = 'fake_dht.json'
        self.pipe = pipe
        self.crypto = CryptoFactory()
        self.dht = FakeDHT(dht_file)
        self.node = self.dht.get_node(name) # The node represented by the server
        self.crypto.path_building_key = self.node.path_building_key # hide the key from operations


    def listen (self, ipaddress, udpport):    
        # NOTE: DHT and crypto perhaps should go in the constructor
        
        # Initialize the DHT and get the information for my node 
        # in the Phantom network
        dht_file = 'fake_dht.json'
        dht = FakeDHT(dht_file)
        my_node = dht.get_node(self.name)
        if not udpport:
            udpport = my_node.port
        
        # Initialize crypto factory
        crypto_factory = CryptoFactory()
        crypto_factory.path_building_key = my_node.path_building_key
        
        # Set some class vars
        self.address = ipaddress
    
        # Initialize listening non-blocking UDP socket
        sock = socket(AF_INET, SOCK_DGRAM)
        sock.setblocking(0)
        sock.bind((ipaddress, udpport))
        
        # Main loop
        inputs = [sock, self.pipe] # stuff we read
        outputs = [] # stuff we expect to write
        
        # Set up the named pipe that we use to simulate the TUN interface
        # and use to communicate with the test harness
        fifo = None
        if self.pipe_test:
            log.debug("Opening pipe="+self.pipe_test+" for IPC with test harness")
            fifo = os.open(self.pipe_test, os.O_RDWR)
            if udpport == 9000:
                inputs.append(fifo)
        
        while inputs:
            readable, writable, exceptional = select.select(inputs, outputs, inputs)
            
            for event in readable:
                if fifo and event is fifo:
                    # Handle data from test harness simulating TUN (via pipe)
                    self.handle_fifo(sock, fifo)
                if event is sock:
                    # Handle tunnel/setup request data
                    self.handle_udp(sock, fifo)
                if event is self.pipe:
                    # Handle commands from the UI in the other process (IPC)
                    data = self.pipe.recv()
                    log.debug("pipe event: "+str(data))
                    if data == 'path':
                        # Attempt to create a routing path
                        # NOTE: At this point we just create the first round setup packages
                        path = RoutingPath(my_node, dht)
                        pkgs = path.round1_setup_packages()
                        log.debug("Creating path with nodes:"+str(path.nodes))
                        
                        # Send a setup message to the first node in the path
                        target_node = path[1]
                        log.debug("len of package:"+str(len(pkgs[0]))+" dest:"+str(target_node.port))
                        sock.sendto(pkgs[0], (target_node.ip_addr, target_node.port))
                        
                    if data[0] == 'open':
                        # NOTE: For open command, data[1] and data[2] are
                        # an IP address and port, respectively
                        connId = os.urandom(16).encode('hex')
                        msg = connId + 'setup'
                        sock.sendto(msg, (data[1], data[2]))
                        self.setup_peers[connId] = SetupInfo(data[1], data[2])
            
            # Handle exceptional?    
    
    def handle_fifo (self, sock, fifo, ):
        # Send data from fifo to sock
        data = os.read(fifo, 100)
        log.debug("handle_fifo: "+str(data))
        for peerId in self.tunnels:
            log.debug("sending to peerId= "+str(peerId))
            # TODO: perhaps FIFO message should be parsed json, so we know which client to send them to?
            peer = self.tunnels[peerId]
            msg = peerId + data
            sock.sendto(msg, (peer.address, peer.port))

    def handle_udp (self, sock, fifo):
        # Decide what to do with the packet:
        (data, addr) = sock.recvfrom(1024)
        log.debug("UDP addr:"+str(addr)+" len:"+str(len(data))+": "+data)
        
        # Assume we are receiving a setup package for now
        # NOTE: We may not get all the info for a setup packet as they are >= 498 bytes long!
        
        if addr not in self.setup_peers:
            peer_path_building_cert = data[0:64]
            # public_box = crypto_factory.public_box(peer_path_building_cert)
            # message = public_box.decrypt(data[64:]) # try this
            # sha256()
            print message
        
               
    def handle_udp_old (self, sock, fifo):
        # Deprecated old version, don't delete yet!
        # Decide what to do with the packet:
        (data, addr) = sock.recvfrom(1024)
        log.debug("UDP "+str(addr)+": "+data)
        
        # NOTE: Once I've gotten the test harness working and have the tunnel
        # routing working, describe the packet handling decisions in more
        # detail.
        
        # check if valid packet
        peerId = None
        try:
            peerId = data[0:32]
            data = data[32:len(data)]
            if len(data) < 3:
                return # bad packet, too short
        except:
            return # bad packet

        # Handle the various cases
        if peerId in self.setup_peers: # We see a continued setup packet
            log.debug("packet received from peer in setup_peers!")
            if data == 'acksetup':
                # Consider as active peer
                peer = self.setup_peers[peerId]
                self.tunnels[peerId] = TunnelInfo(peer.address, peer.port)
                del self.setup_peers[peerId]
            return
        elif peerId in self.tunnels: # We are functioning as a relay for this node
            # NOTE: This is where TUN interface forwarding would happen
            log.debug("tunnel data: "+str(data))
            if fifo:
                log.debug("...writing out to fifo!"+str(data))
                os.write(fifo, data)
            return
        else: # New peer
            log.debug("new peer")
            if data == "setup":
                msg = peerId + 'acksetup'
                self.tunnels[peerId] = TunnelInfo(addr[0], addr[1])
                sock.sendto(msg, addr)
                log.debug("setup packet")
