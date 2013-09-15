#!/usr/local/bin/python2.7

import sys
import select # for select, epoll, kqueue
from socket import socket, AF_INET, SOCK_DGRAM
from multiprocessing import Process, Pipe
from server_datatypes import SetupInfo, TunnelInfo
import os
import logging
from listener import UDPListener, TCPListener
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
        self.pipe_test = pipe_test
        
        self.dht = FakeDHT(dht_file)
        self.node = self.dht.get_node(name) # The node represented by the server
        

        # hashes to hold info on peers
        self.setup_peers = {}


    def listen (self, ipaddress, udpport):    
        
        if not udpport:
            udpport = self.node.port
        
        #udp_listener = UDPListener((ipaddress, udpport), self.dht, self.node)
        listener = TCPListener((ipaddress, udpport), self.dht, self.node)
        
        # Main loop
        inputs = [listener.sock, self.pipe] # stuff we read
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
                print "select(event) type:", type(event)
                
                # IPC
                if fifo and event is fifo:
                    # Handle data from test harness simulating TUN (via pipe)
                    self.handle_fifo(sock, fifo)
                elif event is self.pipe:
                    # Handle commands from the UI in the other process (IPC)
                    data = self.pipe.recv()
                    log.debug("pipe event: "+str(data))
                    if data == 'path':
                        # Attempt to create a routing path
                        listener.setup_round_1()
                
                # Phantom network and Adverseries
                elif event is listener.sock: # Incoming request
                    # 1) Handle tunnel/setup request data
                    # 2) Process tunnel data (udp)
                    listener.handle_incoming(inputs)
                else:
                    # Handle individual connections (such as TCP, but never UDP)
                    listener.handle_conn_data(event, inputs)
                    
                    # TODO: Problem is that I'm somehow getting this
                    # event is <type '_multiprocessing.Connection'>
                    # instead of a regular socket connection (is it the pipe?)
                    
            
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
