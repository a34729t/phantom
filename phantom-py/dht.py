from routingpath import RoutingPath, Node, NodeTypes
import simplejson as json

class FakeDHT:
    def __init__(self, filename):
        f = open(filename)
        db = json.loads(f.read())
        f.close()
        
        self.nodes = {}
        for node_name in db:
            if node_name != '_comment':
                ip_addr = db[node_name]['ip_addr']
                port = db[node_name]['port']
                cert_hex = db[node_name]['path_building_certificate']
                key_hex = db[node_name]['path_building_key']
                node = Node(node_name, ip_addr, port, key_hex, cert_hex)
                self.nodes[node_name] = node
    
    def get_node(self, node_name):
        if node_name not in self.nodes:
            raise Exception("Unable to find node "+node_name+" in fake DHT!!!")
        else:
            return self.nodes[node_name]
    
    def get_x_and_y_nodes(self, my_node, x=1, y=2):
        x_and_y_nodes = []
        prev_type = None
        for node_name in self.nodes:
            if node_name != '_comment' and node_name != my_node.name:
                node = self.nodes[node_name]
                
                if x > 0 and prev_type == NodeTypes.Y:
                    node.type = NodeTypes.X
                    x_and_y_nodes.append(node)
                    prev_type = node.type
                    x -= 1
                    if x == 0: node.terminating = True
                elif y > 0:
                    node.type = NodeTypes.Y
                    x_and_y_nodes.append(node)
                    prev_type = node.type
                    y -= 1
                else:
                    break
        
        return x_and_y_nodes