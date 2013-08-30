import BaseHTTPServer
import simplejson as json

# Simple HTTP endpoints for controlling prototype Phantom implementation.
# The following commands are supported:
# 1. Open a connection via /open/[IP]:[PORT]
# 2. Create a routing path via /path

class RequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    pipe = None
    
    def __init__(self, pipe, *args):
        RequestHandler.pipe = pipe
        BaseHTTPServer.BaseHTTPRequestHandler.__init__(self, *args)
    
    # Don't log anything
    def log_message(self, format, *args):
        return
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        
        # Open connection command
        if self.path.startswith('/open/'):
            addrStr = self.path[6:len(self.path)]
            (address, port) = tuple(filter(None, addrStr.split(':')))
            port = int(port)
            RequestHandler.pipe.send(('open', address, port))
            message = {'address': address, 'port': port}
            self.wfile.write(json.dumps(message))
        if self.path.startswith('/path'):
            RequestHandler.pipe.send(('path'))
            message = {'msg': 'attempting to open routing path'}
            self.wfile.write(json.dumps(message))
        elif self.path.startswith('/restart'):
            # print "restarting UDP subprocess"
            # RequestHandler.pipe.send(('restart', None, None))
            pass
        
def handleRequestsUsing(logic):
    return lambda *args: RequestHandler(logic, *args)