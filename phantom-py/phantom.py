#!/usr/local/bin/python2.7

import sys, signal
from multiprocessing import Process, Pipe
from server_select import Server
import BaseHTTPServer, handler # HTTP UI
from optparse import OptionParser

# Configure logger
# see http://stackoverflow.com/questions/4722745/logging-between-classes-in-python
import logging
log = logging.getLogger("mylog")
log.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s")

# Log to file
filehandler = logging.FileHandler("debug.log", "w")
filehandler.setLevel(logging.DEBUG)
filehandler.setFormatter(formatter)
log.addHandler(filehandler)

# Log to stdout too
streamhandler = logging.StreamHandler()
streamhandler.setLevel(logging.DEBUG)
streamhandler.setFormatter(formatter)
log.addHandler(streamhandler)


def start_server(name, pipe, port, pipe_test):
    s = Server(name, pipe, pipe_test)
    s.listen('127.0.0.1', port)

def start_ui(pipe, HTTP_PORT):
    # For UI, use simple HTTP server with various endpoints
    # open a connection: localhost:[PORT]/open/[TARGET_IP]
    server_class = BaseHTTPServer.HTTPServer
    myHandler = handler.handleRequestsUsing(pipe)
    httpd = server_class(('localhost', HTTP_PORT), myHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
          pass
    httpd.server_close()

def main():
    # Parse command line options
    usage = "usage: %prog [options] arg"
    parser = OptionParser(usage)
    parser.add_option('-n', '--name', dest='name', default='A') # This is our DHT key - temporary!!!
    parser.add_option('-p', '--httpport', dest='http_port', default=None)
    parser.add_option('-u', '--udpport', dest='udp_port', default=None)
    parser.add_option('-f', '--pipe', dest='pipe_test', default=None)
    (options, args) = parser.parse_args()
    
    name = options.name
    http_port = None
    if options.http_port:
        http_port = int(options.http_port)
    udp_port = None
    if options.udp_port:
        udp_port = int(options.udp_port)
    pipe_test = options.pipe_test # Pipe for talking to test harness
    http_ui = True
    
    log.info("server listening on udp_port="+str(udp_port)+", http_port="+str(http_port))
    
    # Named full duplex pipe for communicating between main process and UI/UDP
    # server subprocess
    pipe_server, pipe_ui = Pipe()
    
    # Start UDP server subprocess
    p_server = Process(target=start_server, args=(name, pipe_server, udp_port, pipe_test))
    p_server.start()
    
    # Choose which UI to use (http is better for testing multiple instances on same machine)
    if http_ui and http_port:
        p_ui = Process(target=start_ui, args=(pipe_ui, http_port))
        p_ui.start()
        p_ui.join()
        p_ui.kill()
    # else:
    #     # OSX status bar version not working with python 2.7 on OSX 10.6
    #     from userinterface import OSXstatusbaritem
    #     OSXstatusbaritem.start(pipeUI)
    #     return
    
    p_server.join()
    p_server.kill()
    

if __name__ == "__main__": sys.exit(main())