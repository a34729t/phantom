from routingpath import RoutingPath, Node, NodeTypes
from crypto_factory import CryptoFactory
from dht import FakeDHT

# nacl stuff
import nacl.utils
from nacl.public import PrivateKey, Box
from nacl.hash import sha256
import nacl.signing
import nacl.secret
import nacl.encoding

def create_node():
    sk_txt = 'b732e47809f8dba48a29c38a716ab4a9578b50eaa3da72228596dbbeb21be8de'
    pk_txt = 'c6861dbb1627927ce1e6e01d26506f6035627479ecad3998d5d93d22117bf706'
    return Node('Z', '127.0.0.1', 7999, sk_txt, pk_txt)

def test_dht():
    # Verify the basic behavior of the fake DHT
    my_node = create_node()
    dht_file = 'fake_dht.json'
    dht = FakeDHT(dht_file)
    nodes = dht.get_x_and_y_nodes(my_node, 1, 2)
    
    # For now, just check to make sure we generate the correct # of x and y nodes
    x_count, y_count = 0, 0
    for node in nodes:
        if node.type == NodeTypes.X: x_count += 1
        elif node.type == NodeTypes.Y: y_count += 1
    
    assert x_count == 1
    assert y_count == 2

def test_public_box():
    # test assymmetric crypto
    # Use our node to initialize a factory
    my_node = create_node()
    my_key = my_node.path_building_key
    my_cert = my_node.path_building_cert
    
    # and another pair to verify against
    other_key = PrivateKey.generate()
    other_cert = other_key.public_key
    
    # Create factory and generate a box
    crypto_factory = CryptoFactory()
    crypto_factory.path_building_key = my_key
    my_box = crypto_factory.public_box(other_cert)
    
    # And roundtrip a message
    message = "Kill all humans"
    encrypted = my_box.encryptn(message)
    other_box = Box(other_key, my_cert)
    plaintext = other_box.decrypt(encrypted)
    assert plaintext == message
   
def test_secret_box():
    # Test symmetric crypto
    crypto_factory = CryptoFactory()
    
    # Given our factory, generate a key and a corresponding box
    key = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
    box = crypto_factory.secret_box(key)
    
    message = "The president will be exiting through the lower levels"
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
    my_node = create_node()
    my_key = my_node.path_building_key
    crypto_factory = CryptoFactory()
    crypto_factory.path_building_key = my_key
    path = RoutingPath(my_node, FakeDHT('fake_dht.json'))
    
    target_node = path.nodes[1] # get first node in path
    pkg_plaintext = target_node.round1_setup_package()
    pkg_encrypted = target_node.encrypt_and_sign(pkg_plaintext, path.path_construction_key)
    
    '''
    # NOTE: I've commented out the below as it probably only applies to the 
    #   second round package setup
    # 1) Verify signature
    pkg_verified = path.path_construction_cert.verify(pkg_encrypted)
    
    # 2) Decrypt using conn_id (symmetric)
    secret_box = crypto_factory.secret_box(target_node.prev_id)
    pkg_decrypted_secret = secret_box.decrypt(pkg_verified)
    '''
    
    # 3) Decrypt using key of target_node and cert of my_node (asymmetric)
    public_box = Box(target_node.path_building_key, my_node.path_building_cert)
    # plaintext = public_box.decrypt(pkg_decrypted_secret)
    plaintext = public_box.decrypt(pkg_encrypted)
    
    assert pkg_plaintext == plaintext
    
def test_routing_path():
    # Initialize our node, crypto and dht
    my_node = create_node()
    crypto_factory = CryptoFactory()
    crypto_factory.path_building_key = my_node.path_building_key
    dht_file = 'fake_dht.json'
    dht = FakeDHT(dht_file)
    
    # Create a routing path
    path = RoutingPath(my_node, dht, 3)
    
    # Verify the nodes in the new routing path are linked correctly
    # i.e. node_0 -> conn_id_0_1 -> node_1 -> conn_id_1_2 -> node_2 ...
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
        
    # Create round 1 setup packages (shuffled array)
    pkgs = path.round1_setup_packages()
    
    # Verify the 1st setup package is correct (assume rest are also correct)
    # TODO: This logic should be in the phantom app itself, so we use the same code
    # to validate incoming setup packages in the tests and the app
    target_node = path.nodes[1]
    plaintext, hash_pkgs, h_target = None, None, None
    
    for i in range(path.length):
        pkg = pkgs[i]
        try:
            # pkg_verified = target_node.path_construction_cert.verify(pkg)
            # pkg_decrypted_secret = target_node.secret_box.decrypt(pkg_verified)
            # plaintext = target_node.public_box.decrypt(pkg_decrypted_secret)
            plaintext = target_node.public_box.decrypt(pkg)
            
            s = None
            if i == path_length - 1:
                s = ''.join(pkgs[0:i])
            else:
                s = ''.join(pkgs[0:i]+pkgs[i+1:path_length])
            h_target = sha256(s)
            
            break
        except:
            pass
    
    for h in pkgs[path.length:]:
        # attempt to decrypt - we should get a 64 bytes sha256
        try:
            # h_verified = target_node.path_construction_cert.verify(h)
            # h_decrypted_secret = target_node.secret_box.decrypt(h_verified)
            # hash_pkgs = target_node.public_box.decrypt(h_decrypted_secret)
            hash_pkgs = target_node.public_box.decrypt(h)
            break
        except:
            pass
    
    assert plaintext == target_node.round1_setup_package()
    assert hash_pkgs == h_target
    
    
test_dht()
test_crypto_factory()
test_setup_package_creation_and_read_round1()
test_routing_path()