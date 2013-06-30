class SetupInfo:
    def __init__(self, address, port):
        self.address = address
        self.port = port # NOTE: Somewhat redundant, but if we allow different ports in future, it's useful
        
        # NOTE: This object should contain all the information we need to keep
        # track of during routing path construction, including keys and such
        
        return
    
    def __str__(self):
        return ""
        
class TunnelInfo:
    def __init__(self, address, port):
        self.address = address
        self.port = port # NOTE: Somewhat redundant, but if we allow different ports in future, it's useful
        self.failures = 0 # Keep track of failed packets, remove tunnel after certain threshold
        return

    def __str__(self):
        return ""

