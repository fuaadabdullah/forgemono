#!/usr/bin/env python3
"""
Kamatera Router Network Fix Tool
Comprehensive tool to diagnose and fix router-to-inference communication issues
"""

import json
import time
import asyncio
import aiohttp
import socket
import subprocess
import re
import sys
from typing import Dict, List, Optional, Tuple
from pathlib import Path

class KamateraRouterNetworkFix:
    def __init__(self):
        self.inference_server = "192.175.23.150"
        self.router_server = "45.61.51.220"
        self.inference_port = 8002
        self.router_port = 8000
        self.inference_api_key = "206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158"
        self.internal_api_key = "dcb2546960bb963c61db8b56939e8e3c25398f073409938882d6b07a7741de89"
        self.public_api_key = "cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765"
        
        self.timeout = 30
        self.results = {}
    
    async def test_basic_connectivity(self) -> Dict:
        """Test basic network connectivity"""
        print("🔍 Testing Basic Network Connectivity...")
        print("-" * 50)
        
        # Test ping
        ping_results = {}
        for server_name, server_ip in [("Inference", self.inference_server), ("Router", self.router_server)]:
            print(f"  Pinging {server_name} ({server_ip})...")
            try:
                result = subprocess.run(
                    ["ping", "-c", "3", server_ip],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # Extract ping statistics
                    output = result.stdout
                    if "avg" in output:
                        avg_match = re.search(r'avg = ([^/]+)/', output)
                        if avg_match:
                            avg_time = avg_match.group(1)
                            ping_results[server_name] = {
                                "status": "reachable",
                                "avg_time": f"{avg_time}ms",
                                "raw_output": output
                            }
                        else:
                            ping_results[server_name] = {
                                "status": "reachable",
                                "raw_output": output
                            }
                    else:
                        ping_results[server_name] = {
                            "status": "reachable",
                            "raw_output": output
                        }
                else:
                    ping_results[server_name] = {
                        "status": "unreachable",
                        "error": result.stderr
                    }
            except Exception as e:
                ping_results[server_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        self.results["basic_connectivity"] = ping_results
        
        for server, result in ping_results.items():
            status_icon = "✅" if result["status"] == "reachable" else "❌"
            print(f"    {status_icon} {server}: {result['status']}")
            if result["status"] == "reachable" and "avg_time" in result:
                print(f"      Average latency: {result['avg_time']}")
        
        return ping_results
    
    async def test_port_connectivity(self) -> Dict:
        """Test specific port connectivity"""
        print("\n🔌 Testing Port Connectivity...")
        print("-" * 50)
        
        port_tests = [
            ("Inference Server", self.inference_server, self.inference_port),
            ("Router Server", self.router_server, self.router_port)
        ]
        
        port_results = {}
        for server_name, server_ip, port in port_tests:
            print(f"  Testing {server_name} {server_ip}:{port}...")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(10)
                result = sock.connect_ex((server_ip, port))
                sock.close()
                
                if result == 0:
                    port_results[f"{server_name}_{port}"] = {
                        "status": "open",
                        "server": server_ip,
                        "port": port
                    }
                    print(f"    ✅ {server_name} port {port}: OPEN")
                else:
                    port_results[f"{server_name}_{port}"] = {
                        "status": "closed",
                        "server": server_ip,
                        "port": port,
                        "error": "Connection refused"
                    }
                    print(f"    ❌ {server_name} port {port}: CLOSED")
            except Exception as e:
                port_results[f"{server_name}_{port}"] = {
                    "status": "error",
                    "server": server_ip,
                    "port": port,
                    "error": str(e)
                }
                print(f"    ❌ {server_name} port {port}: ERROR - {str(e)}")
        
        self.results["port_connectivity"] = port_results
        return port_results
    
    async def test_http_endpoints(self) -> Dict:
        """Test HTTP endpoints"""
        print("\n🌐 Testing HTTP Endpoints...")
        print("-" * 50)
        
        endpoints = [
            ("Inference Models", f"http://{self.inference_server}:{self.inference_port}/api/tags"),
            ("Router Health", f"http://{self.router_server}:{self.router_port}/health"),
            ("Router Chat", f"http://{self.router_server}:{self.router_port}/v1/chat/completions")
        ]
        
        http_results = {}
        
        async with aiohttp.ClientSession() as session:
            for endpoint_name, url in endpoints:
                print(f"  Testing {endpoint_name}...")
                try:
                    start_time = time.time()
                    
                    if "chat/completions" in url:
                        # Special handling for chat completions
                        payload = {
                            "model": "phi3:latest",
                            "messages": [{"role": "user", "content": "Hello"}]
                        }
                        headers = {
                            "x-api-key": self.public_api_key,
                            "Content-Type": "application/json"
                        }
                        async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=30)) as response:
                            response_time = time.time() - start_time
                            response_data = await response.text()
                            
                            http_results[endpoint_name] = {
                                "status": "success" if response.status == 200 else "failed",
                                "http_status": response.status,
                                "response_time": response_time,
                                "response_data": response_data[:500]  # First 500 chars
                            }
                    else:
                        # Regular GET request
                        headers = {}
                        if "api/tags" in url:
                            headers["x-api-key"] = self.inference_api_key
                        
                        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            response_time = time.time() - start_time
                            response_data = await response.text()
                            
                            http_results[endpoint_name] = {
                                "status": "success" if response.status == 200 else "failed",
                                "http_status": response.status,
                                "response_time": response_time,
                                "response_data": response_data[:500]
                            }
                    
                    status_icon = "✅" if http_results[endpoint_name]["status"] == "success" else "❌"
                    print(f"    {status_icon} {endpoint_name}: {http_results[endpoint_name]['http_status']} ({http_results[endpoint_name]['response_time']:.2f}s)")
                    
                except asyncio.TimeoutError:
                    http_results[endpoint_name] = {
                        "status": "timeout",
                        "error": "Request timed out"
                    }
                    print(f"    ⏰ {endpoint_name}: TIMEOUT")
                except Exception as e:
                    http_results[endpoint_name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"    ❌ {endpoint_name}: ERROR - {str(e)}")
        
        self.results["http_endpoints"] = http_results
        return http_results
    
    async def test_internal_connectivity(self) -> Dict:
        """Test internal connectivity between servers"""
        print("\n🔗 Testing Internal Server Connectivity...")
        print("-" * 50)
        
        # Simulate what the router should be doing
        internal_tests = {
            "router_to_inference_health": {
                "description": "Router checking Inference health",
                "method": "GET",
                "url": f"http://{self.inference_server}:{self.inference_port}/health",
                "headers": {"x-api-key": self.internal_api_key}
            },
            "router_to_inference_models": {
                "description": "Router getting Inference models",
                "method": "GET", 
                "url": f"http://{self.inference_server}:{self.inference_port}/api/tags",
                "headers": {"x-api-key": self.internal_api_key}
            }
        }
        
        internal_results = {}
        
        async with aiohttp.ClientSession() as session:
            for test_name, test_config in internal_tests.items():
                print(f"  Testing {test_config['description']}...")
                try:
                    start_time = time.time()
                    
                    if test_config["method"] == "GET":
                        async with session.get(
                            test_config["url"],
                            headers=test_config["headers"],
                            timeout=aiohttp.ClientTimeout(total=15)
                        ) as response:
                            response_time = time.time() - start_time
                            response_data = await response.text()
                            
                            internal_results[test_name] = {
                                "status": "success" if response.status == 200 else "failed",
                                "http_status": response.status,
                                "response_time": response_time,
                                "response_data": response_data[:500]
                            }
                    
                    status_icon = "✅" if internal_results[test_name]["status"] == "success" else "❌"
                    print(f"    {status_icon} {test_config['description']}: {internal_results[test_name]['http_status']} ({internal_results[test_name]['response_time']:.2f}s)")
                    
                except asyncio.TimeoutError:
                    internal_results[test_name] = {
                        "status": "timeout",
                        "error": "Request timed out"
                    }
                    print(f"    ⏰ {test_config['description']}: TIMEOUT")
                except Exception as e:
                    internal_results[test_name] = {
                        "status": "error",
                        "error": str(e)
                    }
                    print(f"    ❌ {test_config['description']}: ERROR - {str(e)}")
        
        self.results["internal_connectivity"] = internal_results
        return internal_results
    
    def analyze_routing_issue(self) -> Dict:
        """Analyze the routing issue based on test results"""
        print("\n🔍 Analyzing Routing Issue...")
        print("-" * 50)
        
        analysis = {
            "issue_identified": False,
            "possible_causes": [],
            "recommendations": []
        }
        
        # Check if basic connectivity works
        basic_connect = self.results.get("basic_connectivity", {})
        inference_reachable = basic_connect.get("Inference", {}).get("status") == "reachable"
        router_reachable = basic_connect.get("Router", {}).get("status") == "reachable"
        
        # Check if ports are open
        port_connect = self.results.get("port_connectivity", {})
        inference_port_open = port_connect.get("Inference Server_8002", {}).get("status") == "open"
        router_port_open = port_connect.get("Router Server_8000", {}).get("status") == "open"
        
        # Check HTTP endpoints
        http_endpoints = self.results.get("http_endpoints", {})
        inference_http_ok = http_endpoints.get("Inference Models", {}).get("status") == "success"
        router_health_ok = http_endpoints.get("Router Health", {}).get("status") == "success"
        router_chat_ok = http_endpoints.get("Router Chat", {}).get("status") == "success"
        
        # Check internal connectivity
        internal_connect = self.results.get("internal_connectivity", {})
        internal_health_ok = internal_connect.get("router_to_inference_health", {}).get("status") == "success"
        internal_models_ok = internal_connect.get("router_to_inference_models", {}).get("status") == "success"
        
        print(f"  Basic Connectivity - Inference: {'✅' if inference_reachable else '❌'}, Router: {'✅' if router_reachable else '❌'}")
        print(f"  Port Accessibility - Inference: {'✅' if inference_port_open else '❌'}, Router: {'✅' if router_port_open else '❌'}")
        print(f"  HTTP Endpoints - Inference: {'✅' if inference_http_ok else '❌'}, Router Health: {'✅' if router_health_ok else '❌'}")
        print(f"  Internal Connectivity - Health: {'✅' if internal_health_ok else '❌'}, Models: {'✅' if internal_models_ok else '❌'}")
        
        # Determine issue
        if inference_reachable and inference_port_open and inference_http_ok:
            if not (internal_health_ok and internal_models_ok):
                analysis["issue_identified"] = True
                analysis["possible_causes"] = [
                    "Firewall blocking internal traffic",
                    "Servers not on same private network/VPC",
                    "Router using wrong internal IP for inference",
                    "Internal API key mismatch"
                ]
                analysis["recommendations"] = [
                    "Configure firewall rules to allow internal traffic",
                    "Ensure servers are on same VPC/private network",
                    "Update router configuration to use internal IP",
                    "Verify internal API key configuration",
                    "Check internal DNS resolution"
                ]
            else:
                analysis["recommendations"] = ["No routing issues detected"]
        else:
            analysis["recommendations"] = [
                "Fix basic connectivity issues first",
                "Ensure inference server is running and accessible"
            ]
        
        self.results["analysis"] = analysis
        
        if analysis["issue_identified"]:
            print(f"\n🚨 ROUTING ISSUE CONFIRMED")
            for cause in analysis["possible_causes"]:
                print(f"  • {cause}")
        else:
            print(f"\n✅ No routing issues detected")
        
        return analysis
    
    async def generate_fix_scripts(self) -> Dict:
        """Generate fix scripts based on analysis"""
        print("\n🛠️  Generating Fix Scripts...")
        print("-" * 50)
        
        fix_scripts = {}
        
        # Generate firewall fix script
        firewall_script = self._generate_firewall_fix_script()
        fix_scripts["firewall_fix"] = firewall_script
        
        # Generate network configuration fix
        network_script = self._generate_network_fix_script()
        fix_scripts["network_fix"] = network_script
        
        # Generate service configuration update
        service_script = self._generate_service_fix_script()
        fix_scripts["service_fix"] = service_script
        
        # Generate deployment script
        deploy_script = self._generate_deploy_script()
        fix_scripts["deploy_script"] = deploy_script
        
        # Save scripts to files
        script_dir = Path("kamatera_fix_scripts")
        script_dir.mkdir(exist_ok=True)
        
        for script_name, script_content in fix_scripts.items():
            script_path = script_dir / f"{script_name}.sh"
            script_path.write_text(script_content)
            print(f"  ✅ Generated: {script_path}")
        
        self.results["fix_scripts"] = fix_scripts
        return fix_scripts
    
    def _generate_firewall_fix_script(self) -> str:
        """Generate firewall configuration fix script"""
        return '''#!/bin/bash
# Kamatera Firewall Fix Script
# Run this on both servers to allow internal traffic

echo "Configuring Kamatera Server Firewall..."

# Get internal IPs (adjust these if different)
INFERENCE_IP="192.175.23.150"
ROUTER_IP="45.61.51.220"

# Allow internal traffic between servers
echo "Allowing internal traffic between servers..."

# For UFW (Ubuntu/Debian)
if command -v ufw >/dev/null 2>&1; then
    echo "Using UFW..."
    
    # Allow inference server ports from router
    ufw allow from $ROUTER_IP to any port 8002
    
    # Allow router server ports from inference
    ufw allow from $INFERENCE_IP to any port 8000
    
    # Allow established connections
    ufw allow in on eth0 from $ROUTER_IP
    ufw allow in on eth0 from $INFERENCE_IP
    
    # Reload firewall
    ufw reload
    
    echo "✅ UFW firewall configured"
fi

# For iptables (CentOS/RHEL)
if command -v iptables >/dev/null 2>&1; then
    echo "Using iptables..."
    
    # Allow inference server from router
    iptables -A INPUT -s $ROUTER_IP -p tcp --dport 8002 -j ACCEPT
    
    # Allow router server from inference  
    iptables -A INPUT -s $INFERENCE_IP -p tcp --dport 8000 -j ACCEPT
    
    # Save iptables rules
    if command -v iptables-save >/dev/null 2>&1; then
        iptables-save > /etc/iptables/rules.v4 2>/dev/null || service iptables save
    fi
    
    echo "✅ iptables firewall configured"
fi

echo "✅ Firewall configuration complete"
echo "Please restart your services: sudo systemctl restart local-llm-proxy goblin-router"
'''
    
    def _generate_network_fix_script(self) -> str:
        """Generate network configuration fix script"""
        return '''#!/bin/bash
# Kamatera Network Configuration Fix Script
# Fix network routing between servers

echo "Configuring Kamatera Network..."

# Get internal network configuration
echo "Current network configuration:"
ip addr show | grep inet
echo ""

# Add static routes if needed
echo "Adding static routes for internal communication..."

# Add route from router to inference server
# (adjust interface name as needed)
ip route add 192.175.23.0/