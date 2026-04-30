 # Encrypt payload with AES
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
    
    # Generate encryption key
key = get_random_bytes(32)
    
    