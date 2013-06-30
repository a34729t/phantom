#!/usr/local/bin/python2.7

import sys
import select # for select, epoll, kqueue
from socket import socket, AF_INET, SOCK_DGRAM
from multiprocessing import Process, Pipe
from server_datatypes import SetupInfo, TunnelInfo
import os
import nacl #PyNaCl - libsodium (use my python2.7 installation)
import logging
log = logging.getLogger("mylog")

# Design:
# Listens for incoming UDP data, processes it, and builds routing paths along
# which we can build UDP tunnels

class Server:
    def __init__(self, pipe, pipe_test):
        self.pipe = pipe # pipe for communication with external processes (ui)
        self.pipe_test = pipe_test # pipe for communicating with test harness
        
        # NOTE: The tunnels group of peers is a hack to make sure we can build 
        # encrypted tunnels between two nodes. Once routing path construction
        # is working, then we'll have exit, entry and intermediate peers.
        
        self.setup_peers = {} # setup connections this peer is attempting
        self.tunnels = {} # tunnels we are routing over our node

    def listen (self, ipaddress, udpport):
    
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
                    if data[0] == 'open':
                        # NOTE: For open command, data[1] and data[2] are
                        # an IP address and port, respectively
                        connId = self.generate_conn_id()
                        msg = connId + 'setup'
                        sock.sendto(msg, (data[1], data[2]))
                        self.setup_peers[connId] = SetupInfo(data[1], data[2])
            # Handle exceptional?    
    
    def generate_conn_id(self):
        return os.urandom(16).encode('hex')
        
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