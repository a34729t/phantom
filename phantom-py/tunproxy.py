#! /usr/bin/env python

#############################################################################
##                                                                         ##
## tunproxy.py --- small demo program for tunneling over UDP with tun/tap  ##
##                                                                         ##
## Copyright (C) 2003  Philippe Biondi <phil@secdev.org>                   ##
##                                                                         ##
## This program is free software; you can redistribute it and/or modify it ##
## under the terms of the GNU General Public License as published by the   ##
## Free Software Foundation; either version 2, or (at your option) any     ##
## later version.                                                          ##
##                                                                         ##
## This program is distributed in the hope that it will be useful, but     ##
## WITHOUT ANY WARRANTY; without even the implied warranty of              ##
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU       ##
## General Public License for more details.                                ##
##                                                                         ##
#############################################################################

# I have made minor modifications to this script with respect to the way it
# creates the virtual network interface.
#
# To test the system, open up four terminal windows, and start tunproxy in
# server mode, attached to tap0, tunproxy in client mode, attached to tap1,
# run my testserver.js node.js script running on port 4001 (also local), or
# an http server/service of your choice. Finall, you can do a curl against
# the http server over the tunnel, by aiming at the tap interface on one side
# of the tunnel, and the ip address on the other.
#
# server(tap0, 10.0.0.1) <-> UDP tunnel <-> client(tap1, 10.0.0.2)
#
# Here's the commands to run
#
# sudo python2.7 tunproxy.py -s 9000 -t /dev/tap0 -i 10.0.0.1/24
# sudo python2.7 tunproxy.py  -c 127.0.0.1:9000 -t /dev/tap1 -i 10.0.0.2/24
# node testserver.js
# curl --interface tap0 10.0.0.2:4001
#
# NOTE 0: The client crashes sometimes when you start it. Restart the server
# and try again.
#
# NOTE 1: If you look at the console output of the tunproxy client and server,
# you'll see lots of local network traffic across the tunnel, itunes, osx stuff,
# etc. I've verified this with tcpdump:
# (tcpdump -i lo0 -nX udp dst port [client port]). 
#
# TODO: Investigate local traffic going onto tunnel (NOTE 1).

import os, sys, fcntl
from socket import *
from fcntl import ioctl
from select import select
import getopt, struct
import subprocess
from scapy.all import IP # Packet sniffing
# see http://stackoverflow.com/questions/13035220/interfacing-with-tun-tap-for-mac-osx-lion-using-python?lq=1

MAGIC_WORD = "Wazaaaaaaaaaaahhhh !"

TUNSETIFF = 0x400454ca # Linux
# TUNSETIFF = 2147775584 # OSX
IFF_TUN   = 0x0001
IFF_TAP   = 0x0002
IFF_NO_PI = 0x1000

TUNMODE = IFF_TAP
MODE = 0
DEBUG = 0
TUNPATH = None
device_ip = None

def usage(status=0):
    print "Usage: tunproxy [-s port|-c targetip:port] [-e] [-t tunpath] [-i tunipaddr]"
    sys.exit(status)

opts = getopt.getopt(sys.argv[1:],"s:c:t:i:ehd")

for opt,optarg in opts[0]:
    if opt == "-h":
        usage()
    elif opt == "-d":
        DEBUG += 1
    elif opt == "-s":
        MODE = 1
        PORT = int(optarg)
    elif opt == "-c":
        MODE = 2
        IP,PORT = optarg.split(":")
        PORT = int(PORT)
        peer = (IP,PORT)
    elif opt == "-e":
        TUNMODE = IFF_TAP
    elif opt == "-t":
        TUNPATH = optarg
    elif opt == "-i":
        device_ip = optarg
        
if MODE == 0:
    usage(1)

f = None
os_name = os.uname()[0] # Get OS
if os_name == 'Darwin':
    f = os.open(TUNPATH, os.O_RDWR)
else: # Linux
    f = os.open('/dev/net/tun', os.O_RDWR)
    ifr = struct.pack('16sH', TUNPATH, IFF_TAP | IFF_NO_PI)
    fcntl.ioctl(f, TUNSETIFF, ifr)
# fcntl.ioctl(tun, TUNSETOWNER, 1000)

# Assign an IP to tun/tap device
device_name = TUNPATH.split('/')[-1]
subprocess.check_call('ifconfig '+device_name+' '+device_ip, shell=True)


s = socket(AF_INET, SOCK_DGRAM)
# maybe set it to O_NONBLOCK

try:
    if MODE == 1:
        s.bind(("", PORT))
        while 1:
            word,peer = s.recvfrom(1500)
            if word == MAGIC_WORD:
                break
            print "Bad magic word for %s:%i" % peer
        s.sendto(MAGIC_WORD, peer)
    else:
        s.sendto(MAGIC_WORD, peer)
        word,peer = s.recvfrom(1500)
        if word != MAGIC_WORD:
            print "Bad magic word for %s:%i" % peer
            sys.exit(2)
    print "Connection with %s:%i established" % peer
    
    while 1:
        r = select([f,s],[],[])[0][0]
        if r == f:
            if DEBUG: os.write(1,">")
            packet_from_os = os.read(f,1500)
            #print "from vni:", packet_from_os
            #ip = IP(packet_from_os)
            #ip.show()
            s.sendto(packet_from_os,peer)
        else:
            buf,p = s.recvfrom(1500)
            print "from sock:", buf
            # ip = IP(buf)
            # ip.show()
            if p != peer:
                print "Got packet from %s:%i instead of %s:%i" % (p+peer)
                continue
            if DEBUG: os.write(1,"<")
            if f: # make sure tun is up when we write
                os.write(f, buf)

except KeyboardInterrupt:
    os.close(f)
    print "Stopped by user."
