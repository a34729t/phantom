from routingpath import RoutingPath, Node, NodeTypes
from crypto_factory import CryptoFactory
from dht import FakeDHT
from server_select import Server

# nacl stuff
import nacl.utils
from nacl.public import PrivateKey, Box
from nacl.hash import sha256
import nacl.signing
import nacl.secret
import nacl.encoding

def test_dht():
    # Verify the basic behavior of the fake DHT
    dht_file = 'fake_dht.json'
    dht = FakeDHT(dht_file)
    nodes = dht.get_x_and_y_nodes(Server("C").node, 1, 2)
    
    # For now, just check to make sure we generate the correct # of x and y nodes
    x_count, y_count = 0, 0
    for node in nodes:
        if node.type == NodeTypes.X: x_count += 1
        elif node.type == NodeTypes.Y: y_count += 1
    assert x_count == 1
    assert y_count == 2

def test_public_box():
    a = Server('A')
    b = Server('B')
    box_A = a.crypto.public_box(b.node.path_building_cert)
    box_B = b.crypto.public_box(a.node.path_building_cert)
    
    message = 'Kill all humans'
    encrypted = box_A.encryptn(message)
    plaintext = box_B.decrypt(encrypted)
    assert plaintext == message
   
def test_secret_box():
    # Test symmetric crypto
    crypto_factory = CryptoFactory()
    key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
    box = crypto_factory.secret_box(key)
    
    message = 'The president will be exiting through the lower levels'
    encrypted = box.encryptn(message)
    plaintext = box.decrypt(encrypted)
    assert plaintext == message
    
def test_nonce_generator():
    # basically, don't generate duplicates, so test error case
    # and working case
    pass
   
def test_signing():
    pass
   
def test_crypto_factory():
    test_public_box()
    test_secret_box()
    test_signing()
    test_nonce_generator()

def test_setup_package_creation_and_read_round1():
    # Create a single encrypted setup package, and decrypt it
    # Create a starting node and routing path
    
    server = Server("A")
    path = RoutingPath(server.node, server.dht, server.crypto, 3)
    target_node = path.nodes[1] # get first node in path
    
    pkg_plaintext = target_node.round1_setup_package()
    pkg_encrypted = target_node.box.encryptn(pkg_plaintext)
    box = Box(target_node.path_building_key, server.node.path_building_cert)
    plaintext = box.decrypt(pkg_encrypted)
    assert pkg_plaintext == plaintext

def verify_path_node_links():
    # Verify the nodes in the new routing path are linked correctly
    # i.e. node_0 -> conn_id_0_1 -> node_1 -> conn_id_1_2 -> node_2 ...
    
    a = Server('A')
    path = RoutingPath(a.node, a.dht, a.crypto, 3)
    for i in range(1, len(path.nodes)):
        prev = path.nodes[i-1]
        next = path.nodes[i]
        assert prev.next_id == next.prev_id
        assert next.prev_ip_addr == prev.ip_addr
        assert prev.next_ip_addr == next.ip_addr
        assert prev.next_port == next.port
        assert prev.next_path_building_cert_hex == next.path_building_cert_hex
        assert next.prev_path_building_cert_hex == prev.path_building_cert_hex
        assert next.path_construction_cert_hex == path.path_construction_cert_hex


def verify_target_node_can_decrypt_setup_package_round1():
    a = Server('A')
    b = Server('B')
    
    # Create a path containing 'B' and get a target node representing 'B'
    target_node = None
    path = None
    while True:
        path = RoutingPath(a.node, a.dht, a.crypto, 3)
        for node in path.nodes:
            if node.name == 'B':
                target_node = node
                break
        if target_node: break

    # Create round 1 setup packages (shuffled array)
    encrypted_pkg_str = path.round1_setup_packages()
    
    # Now, we pretend to be the first node!
    # Verify the 1st setup package is correct (assume rest are also correct)    
    box, plaintext = RoutingPath.round1_setup_packages_decode(encrypted_pkg_str, b.crypto)
    assert plaintext == target_node.round1_setup_package()
    
def test_round1_exceptions():
    # Change a char in the message and make sure there is an exception
    # TODO: Test hash mismatch exception - checksum error should get this too
    a = Server('A')
    b = Server('B')
    path = RoutingPath(a.node, a.dht, a.crypto, 3)
    encrypted_pkg_str = path.round1_setup_packages()
    if encrypted_pkg_str[128] != 'x':
        encrypted_pkg_str = encrypted_pkg_str[0:128] + 'x' + encrypted_pkg_str[129:]
    else:
        encrypted_pkg_str = encrypted_pkg_str[0:128] + 'y' + encrypted_pkg_str[129:]
        
    try:
        box, plaintext = RoutingPath.round1_setup_packages_decode(encrypted_pkg_str, b.crypto)
        assert 1 == 0
    except:
        pass
        
    
    
def test_routing_path_round1():
    test_setup_package_creation_and_read_round1()
    verify_path_node_links()
    verify_target_node_can_decrypt_setup_package_round1()
    test_round1_exceptions()
    # TODO: Verify dummy packages
    
    
test_dht()
test_crypto_factory()
test_routing_path_round1()