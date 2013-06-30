# Python Prototype
=======

## Usage

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

## Status

### v0.1 - Unencrypted tunnel between two instances

- Select-based UDP server in a subprocess
- Simple http interface in a subprocess
- HTTP command open/IP:PORT - UDP server attempts to send setup packet to another Phantom instance
- Receive setup packet on 2nd instance, return setup acknowledged
- Use the setup process to construct a basic, unencrypted UDP tunnel
- Use a named pipe to simulate the TUN interface and communicate with the test harness
- Added logging

TODO:

- Write a simple test harness to send data through the tunnel (and receive it)
- Look into using a LoggerAdapter to add the process name to log output

### v0.2 - Expand the test harness functionality

- other instance attempts to open up a tunnel when there already is a tunnel established
- other instance is not there in the first place (no connection in first place)
- other instance goes down during setup process
- other instance goes down during tunnel mode
- own instance goes down during setup
- own instance goes down during tunnel mode

### v0.3 - Encrypted tunnel between two instances with key generation, nonces, etc

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