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
# To use:
# sudo python2.7 tunproxy.py -s 9000 -t /dev/tap0 -i 10.0.0.1/24
# sudo python2.7 tunproxy.py  -c 127.0.0.1:9000 -t /dev/tap1 -i 10.0.0.2/24

import os, sys, fcntl
from socket import *
from fcntl import ioctl
from select import select
import getopt, struct
import subprocess

MAGIC_WORD = "Wazaaaaaaaaaaahhhh !"

TUNSETIFF = 0x400454ca # Linux
TUNSETIFF = 2147775584 # OSX
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

# Assign an IP to tun/tap device
device_name = TUNPATH.split('/')[-1]
subprocess.check_call('ifconfig '+device_name+' '+device_ip, shell=True)


s = socket(AF_INET, SOCK_DGRAM)

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
            s.sendto(os.read(f,1500),peer)
        else:
            buf,p = s.recvfrom(1500)
            if p != peer:
                print "Got packet from %s:%i instead of %s:%i" % (p+peer)
                continue
            if DEBUG: os.write(1,"<")
            os.write(f, buf)

except KeyboardInterrupt:
    os.close(f)
    print "Stopped by user."
