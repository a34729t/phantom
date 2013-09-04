import nacl.utils
from nacl.public import PrivateKey, Box
from nacl.hash import sha256
import nacl.signing
import nacl.secret
import nacl.encoding

from utils import enum
import simplejson as json
from random import randint, shuffle
from struct import *
from crypto_factory import CryptoFactory

import zlib

# Constants, put in constants/config json file???
n_tuples = 3
n_seeds = 3
# TODO: seeds and tuples in Node/Setup Package --> 
# These are for the dummy setup package creation and streaming key generation
# though we could do streaming keys in the second round, but make the setup packages
# the same size

NodeTypes = enum(X=1, Y=2)
crypto_factory = CryptoFactory()

class Node:
    def __init__(self, name, ip_addr, port, key_hex, cert_hex):
        self.name = name
        self.type = None
        self.ip_addr = ip_addr
        self.port = port # 2 bytes
        self.terminating = 0
        
        # certs
        self.path_building_key = PrivateKey(key_hex, encoder=nacl.encoding.HexEncoder)
        self.path_building_key_hex = key_hex
        self.path_building_cert = PrivateKey(cert_hex, encoder=nacl.encoding.HexEncoder)
        self.path_building_cert_hex = cert_hex # transmitted to other nodes
        self.comm_cert = None # NOTE: This would be used to verify SSL stuff, we may not need it
        self.path_construction_cert = None
        self.path_construction_cert_hex = None
        
        # for links
        self.prev_id = None # 32 bytes
        self.next_id = None
        self.prev_ip_addr = None # 4 bytes, but we store as 16
        self.next_ip_addr = None
        self.prev_path_building_cert_hex = None # 64 bytes
        self.next_path_building_cert_hex = None
        
        # TODO: Generate seeds and tuples
        
        # We generate a public box in the round1 setup
        
    def __repr__(self):
        return str(self)
        
    def __str__(self):
        s = "< name: " + self.name 
        if self.type:
            s+= ", type: " + str(self.type)
        s += ", ip/port: " + self.ip_addr + "/" + str(self.port) + " >"
        return s

    def round1_setup_package(self):
        # To generate an output string we use the struct module that converts
        # the data into a c-style btye str/array
        #   See: http://docs.python.org/2/library/struct.html
        s = pack("<15s15sH64s32s32s64s64sBB", \
            self.prev_ip_addr, \
            self.next_ip_addr, \
            self.next_port, \
            self.path_construction_cert_hex, \
            self.prev_id, \
            self.next_id, \
            self.prev_path_building_cert_hex, \
            self.next_path_building_cert_hex, \
            self.type, \
            self.terminating, \
            )
        
        s += pack("<64s", sha256(s)) # append the hash of the decrypted package
            
        # TODO: Pack seeds and tuples
        return s

    def encrypt_and_sign(self, message, signing_key):
        # deprecated, do not need (for now)
        
        # print "!!encrypt_and_sign!!"
        # Encrypt the setup package:
        # 1) Asymmetrically encrypt with the path building certificate of the individual recipient node
        # 2) Symmetrically encrypt with the 128-bit ID of its incoming connection id
        # 3) Sign with the routing path construction key from the previous step
        
        # 1)
        self.public_box = crypto_factory.public_box(self.path_building_cert)
        encrypted_1 = self.public_box.encryptn(message)
        return encrypted_1
        # return message
        
        '''
        # NOTE: I've commented out the below as it probably only applies to the 
        #   second round package setup
        # 2)
        self.secret_box = crypto_factory.secret_box(self.prev_id)
        encrypted_2 = self.secret_box.encryptn(encrypted_1)
        # 3)
        signed = signing_key.sign(encrypted_2)
        return signed
        '''
        
        
class RoutingPath:
    def __init__(self, my_node, dht, crypto, length):
        self.my_node = my_node
        x_and_y_nodes = dht.get_x_and_y_nodes(my_node, 1, 2)
        self.nodes = [my_node] + x_and_y_nodes + [my_node]
        self.length = length
        
        # Generate a signing key
        # NOTE: Where the hell do I use this?
        self.path_construction_key = nacl.signing.SigningKey.generate()
        self.path_construction_cert = self.path_construction_key.verify_key
        self.path_construction_cert_hex = \
            self.path_construction_cert.encode(encoder=nacl.encoding.HexEncoder)
        
        # Create links between the nodes
        for i in range(1,len(self.nodes)):
            prev = self.nodes[i-1]
            next = self.nodes[i]
            # info specific to the link between the two nodes
            conn_id = nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)
            next.path_construction_cert_hex = self.path_construction_cert_hex
            next.path_construction_cert = nacl.signing.VerifyKey(next.path_construction_cert_hex, encoder=nacl.encoding.HexEncoder)
            prev.next_id = conn_id
            next.prev_id = conn_id
            next.prev_ip_addr = prev.ip_addr
            prev.next_ip_addr = next.ip_addr
            prev.next_port = next.port
            prev.next_path_building_cert_hex = next.path_building_cert_hex
            next.prev_path_building_cert_hex = prev.path_building_cert_hex
            
        # Create cryptographic boxes for nodes
        for node in self.nodes[1:-1]:
            node.box = crypto.public_box(node.path_building_cert)
        
    def __repr__(self):
        pass
        
    def __getitem__(self, key):
        return self.nodes[key]
        
    def round1_setup_packages(self):
        # Generate a bunch of setup package data (strings)
        pkgs_and_nodes = []
        for node in self.nodes[1:-1]:
            pkg = node.round1_setup_package()
            pkg_encrypted = node.box.encryptn(pkg)
            # pkg_encrypted = node.encrypt_and_sign(pkg, self.path_construction_key)
            pkgs_and_nodes.append( (node, pkg_encrypted)) # append the node so we know the proper crypto keys
            
        # Shuffle the order of the setup packages
        shuffle(pkgs_and_nodes)
        pkgs = [x[1] for x in pkgs_and_nodes] # separate out pkgs
        
        # compute hash on (array - package) for each package (and shuffle)
        hashes = []
        for i in range(len(pkgs_and_nodes)):
            node = pkgs_and_nodes[i][0]
            s = None
            if i == len(pkgs) - 1:
                s = ''.join(pkgs[0:i])
            else:
                s = ''.join(pkgs[0:i]+pkgs[i+1:])
            
            h = node.box.encryptn(sha256(s))
            hashes.append(h)

        shuffle(hashes)
        
        # Format:
        # 0) 64 byte transmission checksum
        # 1) 64 byte cert (hex)
        # 2) 2 byte path length (N) 
        # 3) 4 byte package length (X)
        # 4) 4 byte hash length (Y)
        # 5) N packages of length X
        # 6) N packages of length Y
        
        # 1)
        pkg_str = self.my_node.path_building_cert_hex 
        
        # 2)
        s = str(self.length)
        while len(s) < 2: s = '0' + s
        pkg_str += s
        
        # 3)
        s = str(len(pkgs[0]))
        while len(s) < 4: s = '0' + s
        pkg_str += s
        
        # 4)
        s = str(len(hashes[0]))
        while len(s) < 4: s = '0' + s
        pkg_str += s
        
        # 5 and 6)
        for pkg in pkgs: pkg_str += pkg
        for h in hashes: pkg_str += h
        
        # 0)
        out = sha256(pkg_str) + pkg_str
        return out
        
    @staticmethod
    def round1_setup_packages_decode(pkgs, crypto):
        # Break apart the received setup package packet per the above method
        # and return the unencrypted data along with the cryptographic box
        # to perform this again
        plaintext, hash_pkgs, h_target = None, -1, -2
        box = None
        pkg_data,hash_data = [], []

        chksum = pkgs[0:64]
        
        if not chksum == sha256(pkgs[64:]):
            raise Exception("Checksum does not match")
        
        cert_hex = pkgs[64:128]
        path_length = int(pkgs[128:130])
        pkg_size = int(pkgs[130:134])
        hash_size = int(pkgs[134:138])
        
        # Create a box
        box = crypto.public_box(PrivateKey(cert_hex, encoder=nacl.encoding.HexEncoder))
        
        # Now get the packages and hashes
        hash_start = 138+(path_length*pkg_size)
        for i in range(path_length):
            pkg_i = pkgs[138+(i*pkg_size):138+((i+1)*pkg_size)]
            hash_i = pkgs[hash_start+(i*hash_size):hash_start+((i+1)*hash_size)]
            pkg_data.append(pkg_i)
            hash_data.append(hash_i)

        # Attempt to decrypt the packages (and calculate the hash on other
        # encrypted packages) and decrypt the hashes one by one
        i = 0
        for pkg in pkg_data:
            try:
                plaintext = box.decrypt(pkg)
                s = None
                if i == path_length - 1:
                    s = ''.join(pkg_data[0:i])
                else:
                    s = ''.join(pkg_data[0:i]+pkg_data[i+1:path_length])
                h_target = sha256(s)
                break
            except:
                pass
            i += 1
                
        for h in hash_data:
            try:
                 hash_pkgs = box.decrypt(h)
                 break
            except:
                pass
        
        if hash_pkgs == h_target:
            return box, plaintext
        else:
            raise Exception("Hashes do not match")
    
