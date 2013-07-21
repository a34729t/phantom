# Python Prototype
=======

## Usage of the main app (phantom.py)

Currently, we can build an unencrypted tunnel between two instances and forward UDP data over the tunnel.

To fire up the test harness, type `py test_harness.py`. Or you are not inclined towards automation...

Launch two phantom instances in two separate terminal windows:

    py phantom.py
    py phantom.py -p 4568 -u 9001 -t 8001

Test that the first instance is accepting UDP data by sending UDP packets over command line:

    echo -n 0114821482741248621486812964862890helloworld > /dev/udp/127.0.0.1/9000

Ask the first instance to open a connection to the second:

    http://localhost:4567/open/127.0.0.1:9001

Send a message from test port to the tunnel (from first to second instance):

    echo -n hello world > /dev/udp/127.0.0.1/8000

## Usage of the example app (tunproxy.py) - Building a local UDP tunnel

I have made some modifications to Philippe Biondi's script to make it work on OSX and to avoid having to externally assign a virtual network interface and ip address.

To test the system, open up four terminal windows, and start tunproxy in server mode, attached to tap0, tunproxy in client mode, attached to tap1, run my testserver.js node.js script running on port 4001 (also local), or an http server/service of your choice. Finall, you can do a curl against the http server over the tunnel, by aiming at the tap interface on one side of the tunnel, and the ip address on the other.

    server(tap0, 10.0.0.1) <-> UDP tunnel <-> client(tap1, 10.0.0.2)

Here's the commands to run

    sudo python2.7 tunproxy.py -s 9000 -t /dev/tap0 -i 10.0.0.1/24
    sudo python2.7 tunproxy.py  -c 127.0.0.1:9000 -t /dev/tap1 -i 10.0.0.2/24
    node testserver.js
    curl --interface tap0 10.0.0.2:4001
    
We can also run `tunproxy.py` as server on a separate machine (or VM), let's say the ip is 10.0.1.24:

    server$ node testserver.js
    server$ sudo python2.7 tunproxy.py -s 9000 -t tunX -i 10.0.0.1/24
    local$ sudo python2.7 tunproxy.py  -c 10.0.1.24:9000 -t /dev/tap1 -i 10.0.0.2/24
    local$ curl 10.0.0.1:4001

### OSX Note

* On OSX, Bonjour announces all sort of stuff on the local network on port 5353, among other things. Feel the pain with `tcpdump -i tap1 -nX udp dst port 5353`. To see all the other non-Bonjour traffic, filter out port 5353 with `tcpdump -i tap1 -nX not udp dst port 5353`.

### Using the IPFW Firewall in OSX to block unwanted traffic on tunnel

Here we add a rule (with id=9000) that stops all outgoing traffic over our virtual network interface:

    sudo ipfw add 9000 deny out via tap1
    
We want a rule that allow tcp/udp traffic on a limited basis, and block all other IP traffic. We could go further and only allow several ports, but the basic setup is as follows:
  
    sudo ipfw add 9000 allow tcp from any to any via tap1
    sudo ipfw add 9002 deny ip from any to any via tap1 # block all other incoming and outboung traffic
    
And we can also delete the rules:

    sudo ipfw del 9000 9001 9002

## Status

### v0.1 - Unencrypted tunnel between two instances

- Select-based UDP server in a subprocess
- Simple http interface in a subprocess
- HTTP command open/IP:PORT - UDP server attempts to send setup packet to another Phantom instance
- Receive setup packet on 2nd instance, return setup acknowledged
- Use the setup process to construct a basic, unencrypted UDP tunnel
- Use a named pipe to simulate the TUN interface and communicate with the test harness
- Added logging
- Write a simple test harness to send data through the tunnel (and receive it)

### v0.2 - Use TUN interface
- make sample tun/udp code work properly
- make sample code build a local tunnel
- figure out why local traffic goes onto the local tunnel
- figure out how to use ipfw firewall on OSX
- create app internal firewall `firewall.py`

TODO:
- make app firewall allow ARP, TCP, UDP, ICMP but block other stuff

### v0.2 - Use TUN interface
- integrate tun stuff into main code and modify test harness accordingly
- think about privilege separation so we don't need to give the main app root access 
- try testing data throughput --> 10mbps

### v0.3 - Expand the test harness functionality
- other instance attempts to open up a tunnel when there already is a tunnel established
- other instance is not there in the first place (no connection in first place)
- other instance goes down during setup process
- other instance goes down during tunnel mode
- own instance goes down during setup
- own instance goes down during tunnel mode

### v0.4 - Encrypted tunnel between two instances with key generation, nonces, etc

- Figure out a mock DHT/public key database, possibly a little node.js json service on LAN
- Add NaCL key exchange to tunnel setup
- Add full encryption to tunnel
- Use packet sniffer to verify tunnel data is encrypted
- Modify test harness to sniff packets from the encrypted to tunnel
- Add client nonce to key exchange

## Notes

### Kill dangling python processes in OSX

    ps ax | grep python | awk '{print $1}' | xargs kill -9

### Checking listening ports in OSX

    lsof -i -P | grep -i "listen"

### Client nonces

http://security.stackexchange.com/questions/3001/what-is-the-use-of-a-client-nonce

### Sending UDP packets via command line

You can use echo (without newline using `-n` option) and send it to your `/dev/udp` device:

    echo -n 0114821482741248621486812964862890helloworld > /dev/udp/127.0.0.1/9000

### Use tcpdump to sniff packets

To capture UDP packets on the loopback interface with destination port 9001, use:

    tcpdump -i lo0 -nX udp dst port 9001

### Opening a TUN interface in py

https://gist.github.com/glacjay/585369

### Using NACL in py

https://github.com/jedisct1/libsodium
https://github.com/dstufft/pynacl
https://github.com/dstufft/pynacl/blob/master/docs/public.rst # docs on how to use PyNaCL

You can get the text of public key like so:
nacl.encoding.RawEncoder.decode(myPK.__bytes__())

### Making menu bar items in OSX with python

Doesn't work with python 2.7 and OSX 10.6 on my machine- see userinterface.py

http://stackoverflow.com/questions/8544853/how-to-make-an-menu-bar-system-tray-app-for-osx-in-python
http://taoofmac.com/space/blog/2007/04/22/1745

### How to package a python program to run in OSX

http://svn.pythonmac.org/py2app/py2app/trunk/doc/index.html#abstract

### Level Triggered vs Edge Triggered IO

http://stackoverflow.com/questions/1966863/level-vs-edge-trigger-network-event-mechanisms
http://stackoverflow.com/questions/13848143/is-level-triggered-or-edge-triggered-more-performant?rq=1

The bottom line is there's very little info on this and people aren't sure what the kernel behavior really is, or at least maybe only a few people do, for UDP sockets. In the OpenSSL discussion, someone suggested using edge-triggered, but who knows if that makes a difference. This would be something to experiment with in the future.

### Installing Scapy

https://gist.github.com/benhagen/5257516
