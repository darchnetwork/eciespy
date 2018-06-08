import hashlib

from Cryptodome.Cipher import AES

from coincurve import PrivateKey, PublicKey
from coincurve.utils import get_valid_secret

from eth_keys import keys
from eth_utils import decode_hex

AES_CIPHER_MODE = AES.MODE_GCM


def sha256(msg: bytes) -> bytes:
    '''
    >>> sha256(b'0'*16).hex()[:8] == 'fcdb4b42'
    True
    '''
    h = hashlib.sha256()
    h.update(msg)
    return h.digest()


def generate_key() -> PrivateKey:
    '''
    Generate random (or disposable) EC private key
    '''
    return PrivateKey(get_valid_secret())


def generate_eth_key() -> keys.PrivateKey:
    return keys.PrivateKey(get_valid_secret())


def hex2pub(pub_hex: str) -> PublicKey:
    '''
    Convert ethereum hex to EllipticCurvePublicKey
    The hex should be 65 bytes, but ethereum public key only has 64 bytes
    So have to add \x04
    >>> data = b'0'*32
    >>> data_hash = sha256(data)
    >>> eth_prv = generate_eth_key()
    >>> cc_prv = hex2prv(eth_prv.to_hex())
    >>> eth_prv.sign_msg_hash(data_hash).to_bytes() == cc_prv.sign_recoverable(data)
    True
    >>> pubhex = eth_prv.public_key.to_hex()
    >>> computed_pub = hex2pub(pubhex)
    >>> computed_pub == cc_prv.public_key
    True
    '''
    uncompressed = decode_hex(pub_hex)
    if len(uncompressed) == 64:
        uncompressed = b'\x04' + uncompressed

    return PublicKey(uncompressed)


def hex2prv(prv_hex: str) -> PrivateKey:
    '''
    Convert ethereum hex to EllipticCurvePrivateKey
    >>> k = generate_eth_key()
    >>> prvhex = k.to_hex()
    >>> pubhex = k.public_key.to_hex()
    >>> computed_prv = hex2prv(prvhex)
    >>> computed_prv.to_int() == int(k.to_hex(), 16)
    True
    '''
    return PrivateKey(decode_hex(prv_hex))


def derive(private_key: PrivateKey, peer_public_key: PublicKey) -> bytes:
    '''
    Key exchange
    >>> from coincurve import PrivateKey
    >>> ke1 = generate_eth_key()
    >>> ke2 = generate_eth_key()
    >>> k1 = hex2prv(ke1.to_hex())
    >>> k2 = hex2prv(ke2.to_hex())
    >>> derive(k1, k2.public_key) == derive(k2, k1.public_key)
    True
    >>> k1 = generate_eth_key()
    >>> k2 = generate_eth_key()
    '''
    return private_key.ecdh(peer_public_key.format())


def aes_encrypt(key: bytes, plain_text: bytes) -> bytes:
    '''
    AES-GCM encryption with initial vector

    Returns: nonce + tag + encrypted data
    '''
    aes_cipher = AES.new(key, AES_CIPHER_MODE)

    encrypted, tag = aes_cipher.encrypt_and_digest(plain_text)
    cipher_text = bytearray()
    cipher_text.extend(aes_cipher.nonce)
    cipher_text.extend(tag)
    cipher_text.extend(encrypted)
    return bytes(cipher_text)


def aes_decrypt(key: bytes, cipher_text: bytes) -> bytes:
    '''
    AES-GCM decryption

    Returns: plain text
    >>> data = b'this is test data'
    >>> key = get_valid_secret()
    >>> aes_decrypt(key, aes_encrypt(key, data)) == data
    True
    >>> import os
    >>> key = os.urandom(32)
    >>> aes_decrypt(key, aes_encrypt(key, data)) == data
    True
    '''
    nonce = cipher_text[:16]
    tag = cipher_text[16:32]
    ciphered_data = cipher_text[32:]

    aes_cipher = AES.new(key, AES_CIPHER_MODE, nonce=nonce)
    return aes_cipher.decrypt_and_verify(ciphered_data, tag)


if __name__ == '__main__':
    import doctest
    doctest.testmod()