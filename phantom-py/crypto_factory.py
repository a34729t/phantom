import types

import nacl.utils
import nacl.public
import nacl.signing
import nacl.secret        

# TODO: Keep track of all nonces
def public_nonce():
    nonce = nacl.utils.random(nacl.public.Box.NONCE_SIZE)
    return nonce
    
def secret_nonce():
    nonce = nacl.utils.random(nacl.secret.SecretBox.NONCE_SIZE)
    return nonce

class PublicBox(nacl.public.Box):
    # subclass of nacl.public.Box
    # We want a central way of keeping track of used nonces
    def encryptn(self, message):
        return self.encrypt(message, public_nonce())

class SecretBox(nacl.secret.SecretBox):
    def encryptn(self, message):
        return self.encrypt(message, secret_nonce())

class CryptoFactory:
    
    def public_box(self, cert_other):
        return PublicBox(self.path_building_key, cert_other)
        
    def secret_box(self, key):
        return SecretBox(key)