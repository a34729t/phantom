
### Alternate tunnel construction mechanisms alongside UDP

UDP is blocked by some firewalls, so we need alternate ways to tunnel between nodes

1. TCP
2. DNS - http://svn.kryo.se/iodine/README

A major benefit of DNS is operating on WiFi networks with a web validation/proxy, but that let you perform DNS queries:

http://www.richardosgood.com/2012/10/05/tunneling-tcp-over-dns/

### Bandwidth Limiting

Token buckets: Fill up an outgoing packet within a certain time period before sending out data

See:

http://stackoverflow.com/questions/235762/how-do-you-throttle-the-bandwidth-of-a-socket-connection-in-c

### Use Path MTU Discovery to get optimal UDP packet size
