# Design of Phantom App Prototype

Startup:

0. Start with root permission so app can configure virtual network interface
1. Open a virtual network interface (tap) and configure it
2. Load internal firewall rules (to change rules, app must be restarted)
3. Construct routing paths (entry and exit)

Routing Path Construction:

0. Create a random set of nodes
1. Perform the routing operation over these nodes
2. Send keep alives once in a while?

Now the app is active and ready for operation. There are 5 modes of operation, generally speaking:

* Local request to new outbound destination (construct a new tunnel)
* Local request to existing outbound destination (utilize an existing tunnel)
* External request to local as endpoint
* External request to participate in tunnel
* External request to participate in routing path