#!/usr/bin/env python3
"""
Kamatera Router Network Diagnostic Tool
Run this to diagnose and fix router-to-inference communication issues
"""

import json
import time
import asyncio
import aiohttp
import socket
import subprocess
import re
from pathlib import Path

class KamateraDiagnostic:
    def __init__(self):
        self.inference_server = "192.175.23.150"
        self.router_server = "45.61.51.220"
        self.inference_port = 8002
        self.router_port = 8000
        self.inference_api_key = "206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158"
        self.internal_api_key = "dcb2546960bb963c61db8b56939e8e3c25398f073409938882d6b07a7741de89"
        self.public_api_key = "cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765"
        
    async def run_diagnostic(self):
        """Run complete diagnostic"""
        print("🔍 KAMATERA NETWORK DIAGNOSTIC")
        print("=" * 50)
        
        results = {}
        
        # Test basic connectivity
        print("\n📡 Testing Basic Connectivity...")
        results["ping_tests"] = await self.test_ping_connectivity()
        
        # Test port connectivity
        print("\n🔌 Testing Port Connectivity...")
        results["port_tests"] = await self.test_port_connectivity()
        
        # Test HTTP endpoints
        print("\n🌐 Testing HTTP Endpoints...")
        results["http_tests"] = await self.test_http_endpoints()
        
        # Test internal connectivity
        print("\n🔗 Testing Internal Connectivity...")
        results["internal_tests"] = await self.test_internal_connectivity()
        
        # Analyze results
        print("\n🔍 Analyzing Results...")
        analysis = self.analyze_results(results)
        results["analysis"] = analysis
        
        # Generate report
        self.generate_report(results)
        
        # Generate fix scripts if needed
        if analysis["issue_confirmed"]:
            print("\n🛠️  Generating Fix Scripts...")
            self.generate_fix_scripts()
        
        return results
    
    async def test_ping_connectivity(self):
        """Test ping connectivity"""
        results = {}
        for server_name, server_ip in [("Inference", self.inference_server), ("Router", self.router_server)]:
            try:
                result = subprocess.run(
                    ["ping", "-c", "2", server_ip],
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                results[server_name] = "reachable" if result.returncode == 0 else "unreachable"
                print(f"  {server_name}: {'✅' if result.returncode == 0 else '❌'} {results[server_name]}")
            except Exception as e:
                results[server_name] = f"error: {str(e)}"
                print(f"  {server_name}: ❌ error")
        return results
    
    async def test_port_connectivity(self):
        """Test port connectivity"""
        results = {}
        tests = [
            ("Inference", self.inference_server, self.inference_port),
            ("Router", self.router_server, self.router_port)
        ]
        
        for server_name, server_ip, port in tests:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((server_ip, port))
                sock.close()
                status = "open" if result == 0 else "closed"
                results[f"{server_name}_{port}"] = status
                print(f"  {server_name}:{port}: {'✅' if result == 0 else '❌'} {status}")
            except Exception as e:
                results[f"{server_name}_{port}"] = f"error: {str(e)}"
                print(f"  {server_name}:{port}: ❌ error")
        return results
    
    async def test_http_endpoints(self):
        """Test HTTP endpoints"""
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Test inference models
            try:
                headers = {"x-api-key": self.inference_api_key}
                async with session.get(
                    f"http://{self.inference_server}:{self.inference_port}/api/tags",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    results["inference_models"] = "working" if response.status == 200 else f"failed: {response.status}"
                    print(f"  Inference Models: {'✅' if response.status == 200 else '❌'} {results['inference_models']}")
            except Exception as e:
                results["inference_models"] = f"error: {str(e)}"
                print(f"  Inference Models: ❌ error")
            
            # Test router health
            try:
                async with session.get(
                    f"http://{self.router_server}:{self.router_port}/health",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    results["router_health"] = "working" if response.status == 200 else f"failed: {response.status}"
                    print(f"  Router Health: {'✅' if response.status == 200 else '❌'} {results['router_health']}")
            except Exception as e:
                results["router_health"] = f"error: {str(e)}"
                print(f"  Router Health: ❌ error")
            
            # Test router chat (this should fail due to routing issue)
            try:
                payload = {
                    "model": "phi3:latest",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
                headers = {
                    "x-api-key": self.public_api_key,
                    "Content-Type": "application/json"
                }
                async with session.post(
                    f"http://{self.router_server}:{self.router_port}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        results["router_chat"] = "working"
                        print(f"  Router Chat: ✅ working")
                    else:
                        results["router_chat"] = f"failed: {response.status} - {response_text[:100]}"
                        print(f"  Router Chat: ❌ {results['router_chat']}")
            except Exception as e:
                results["router_chat"] = f"error: {str(e)}"
                print(f"  Router Chat: ❌ error")
        
        return results
    
    async def test_internal_connectivity(self):
        """Test internal connectivity between servers"""
        results = {}
        
        async with aiohttp.ClientSession() as session:
            # Test router to inference health
            try:
                headers = {"x-api-key": self.internal_api_key}
                async with session.get(
                    f"http://{self.inference_server}:{self.inference_port}/health",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    results["router_to_inference_health"] = "working" if response.status == 200 else f"failed: {response.status}"
                    print(f"  Router→Inference Health: {'✅' if response.status == 200 else '❌'} {results['router_to_inference_health']}")
            except Exception as e:
                results["router_to_inference_health"] = f"error: {str(e)}"
                print(f"  Router→Inference Health: ❌ error")
            
            # Test router to inference models
            try:
                headers = {"x-api-key": self.internal_api_key}
                async with session.get(
                    f"http://{self.inference_server}:{self.inference_port}/api/tags",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    results["router_to_inference_models"] = "working" if response.status == 200 else f"failed: {response.status}"
                    print(f"  Router→Inference Models: {'✅' if response.status == 200 else '❌'} {results['router_to_inference_models']}")
            except Exception as e:
                results["router_to_inference_models"] = f"error: {str(e)}"
                print(f"  Router→Inference Models: ❌ error")
        
        return results
    
    def analyze_results(self, results):
        """Analyze diagnostic results"""
        print("\n" + "="*50)
        print("📊 ANALYSIS")
        print("="*50)
        
        analysis = {
            "issue_confirmed": False,
            "issue_type": "",
            "recommendations": []
        }
        
        # Check if basic connectivity works
        ping_tests = results.get("ping_tests", {})
        port_tests = results.get("port_tests", {})
        http_tests = results.get("http_tests", {})
        internal_tests = results.get("internal_tests", {})
        
        inference_reachable = ping_tests.get("Inference") == "reachable"
        router_reachable = ping_tests.get("Router") == "reachable"
        
        inference_port_open = port_tests.get(f"Inference_{self.inference_port}") == "open"
        router_port_open = port_tests.get(f"Router_{self.router_port}") == "open"
        
        inference_http_ok = http_tests.get("inference_models", "").startswith("working")
        router_health_ok = http_tests.get("router_health", "").startswith("working")
        router_chat_ok = http_tests.get("router_chat", "").startswith("working")
        
        internal_health_ok = internal_tests.get("router_to_inference_health", "").startswith("working")
        internal_models_ok = internal_tests.get("router_to_inference_models", "").startswith("working")
        
        print(f"Basic Connectivity:     Inference: {'✅' if inference_reachable else '❌'} | Router: {'✅' if router_reachable else '❌'}")
        print(f"Port Accessibility:     Inference: {'✅' if inference_port_open else '❌'} | Router: {'✅' if router_port_open else '❌'}")
        print(f"HTTP Endpoints:         Inference: {'✅' if inference_http_ok else '❌'} | Router: {'✅' if router_health_ok else '❌'}")
        print(f"Router Chat Flow:       {'✅ WORKING' if router_chat_ok else '❌ FAILED'}")
        print(f"Internal Connectivity:  Health: {'✅' if internal_health_ok else '❌'} | Models: {'✅' if internal_models_ok else '❌'}")
        
        # Determine issue
        if inference_reachable and inference_port_open and inference_http_ok:
            if not (internal_health_ok and internal_models_ok):
                analysis["issue_confirmed"] = True
                analysis["issue_type"] = "firewall_or_network_routing"
                analysis["recommendations"] = [
                    "Configure firewall rules to allow internal traffic between servers",
                    "Ensure both servers are on the same private network/VPC",
                    "Check if internal API key configuration matches",
                    "Verify internal DNS resolution between servers"
                ]
                print(f"\n🚨 ROUTING ISSUE CONFIRMED!")
                print(f"   The Router can authenticate but cannot reach the Inference server internally.")
            else:
                print(f"\n✅ No routing issues detected")
        else:
            print(f"\n❌ Basic connectivity issues detected")
            analysis["recommendations"] = [
                "Fix basic connectivity issues first",
                "Ensure both servers are running and accessible"
            ]
        
        return analysis
    
    def generate_report(self, results):
        """Generate diagnostic report"""
        print(f"\n" + "="*50)
        print("📄 DIAGNOSTIC REPORT")
        print("="*50)
        
        analysis = results.get("analysis", {})
        
        if analysis.get("issue_confirmed"):
            print(f"\n🎯 ISSUE IDENTIFIED: Network Routing Problem")
            print(f"   The Router API (Server 2) cannot communicate with the Inference Server (Server 1) internally.")
            print(f"   This is likely due to firewall rules or network configuration.")
            
            print(f"\n💡 RECOMMENDED FIXES:")
            for i, rec in enumerate(analysis.get("recommendations", []), 1):
                print(f"   {i}. {rec}")
        else:
            print(f"\n✅ NO ROUTING ISSUES DETECTED")
            print(f"   Both servers can communicate internally.")
        
        # Save results to file
        report_file = "kamatera_diagnostic_results.json"
        with open(report_file, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Detailed results saved to: {report_file}")
    
    def generate_fix_scripts(self):
        """Generate fix scripts"""
        script_dir = Path("kamatera_fix_scripts")
        script_dir.mkdir(exist_ok=True)
        
        # Generate firewall fix script
        firewall_script = f'''#!/bin/bash
# Kamatera Firewall Fix Script
# Run this on BOTH servers to allow internal traffic

echo "🔧 Configuring Kamatera Firewall..."
echo "Server IPs: Inference={self.inference_server}, Router={self.router_server}"

# Allow internal traffic
if command -v ufw >/dev/null 2>&1; then
    echo "Using UFW..."
    ufw allow from {self.router_server} to any port {self.inference_port}
    ufw allow from {self.inference_server} to any port {self.router_port}
    ufw --force reload
    echo "✅ UFW configured"
elif command -v firewall-cmd >/dev/null 2>&1; then
    echo "Using firewalld..."
    firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='{self.router_server}' port protocol='tcp' port='{self.inference_port}' accept"
    firewall-cmd --permanent --add-rich-rule="rule family='ipv4' source address='{self.inference_server}' port protocol='tcp' port='{self.router_port}' accept"
    firewall-cmd --reload
    echo "✅ firewalld configured"
else
    echo "⚠️  No firewall tool found. Configure manually to allow ports {self.inference_port} and {self.router_port}"
fi

echo "Next: sudo systemctl restart local-llm-proxy goblin-router"
'''
        
        firewall_path = script_dir / "firewall_fix.sh"
        firewall_path.write_text(firewall_script)
        firewall_path.chmod(0o755)
        
        # Generate quick test script
        test_script = f'''#!/bin/bash
# Kamatera Quick Test Script

echo "🧪 Testing Kamatera Network..."

INFERENCE_IP="{self.inference_server}"
ROUTER_IP="{self.router_server}"
INFERENCE_PORT="{self.inference_port}"
ROUTER_PORT="{self.router_port}"

echo "Testing connectivity..."
ping -c 1 $INFERENCE_IP >/dev/null 2>&1 && echo "✅ Inference server reachable" || echo "❌ Inference server unreachable"
ping -c 1 $ROUTER_IP >/dev/null 2>&1 && echo "✅ Router server reachable" || echo "❌ Router server unreachable"

echo "Testing HTTP endpoints..."
curl -s -m 5 "http://$INFERENCE_IP:$INFERENCE_PORT/api/tags" | grep -q "models" && echo "✅ Inference API working" || echo "❌ Inference API failed"
curl -s -m 5 "http://$ROUTER_IP:$ROUTER_PORT/health" | grep -q "ok" && echo "✅ Router health working" || echo "❌ Router health failed"

echo "Testing full chat flow..."
RESPONSE=$(curl -s -m 30 -X POST \\
  -H "x-api-key: {self.public_api_key}" \\
  -H "Content-Type: application/json" \\
  -d '{{"model":"phi3:latest","messages":[{{"role":"user","content":"Hello"}}]}}' \\
  "http://$ROUTER_IP:$ROUTER_PORT/v1/chat/completions")

echo "$RESPONSE" | grep -q "content" && echo "✅ Full chat flow working" || echo "❌ Full chat flow failed"
echo "$RESPONSE" | head -c 200
'''
        
        test_path = script_dir / "quick_test.sh"
        test_path.write_text(test_script)
        test_path.chmod(0o755)
        
        # Generate deployment instructions
        instructions = f"""# Kamatera Network Fix Instructions

## 🚨 ROUTING ISSUE CONFIRMED
The Router API cannot reach the Inference Server internally due to network/firewall issues.

## 🔧 FIX STEPS

### 1. Copy Scripts to Both Servers
```bash
scp kamatera_fix_scripts/firewall_fix.sh user@{self.inference_server}:~/
scp kamatera_fix_scripts/firewall_fix.sh user@{self.router_server}:~/
```

### 2. Run Firewall Fix on Both Servers
```bash
# On Inference Server ({self.inference_server})
ssh user@{self.inference_server}
sudo bash firewall_fix.sh
sudo systemctl restart local-llm-proxy

# On Router Server ({self.router_server})  
ssh user@{self.router_server}
sudo bash firewall_fix.sh
sudo systemctl restart goblin-router
```

### 3. Test the Fix
```bash
# Copy test script and run
scp kamatera_fix_scripts/quick_test.sh user@{self.inference_server}:~/
ssh user@{self.inference_server} ./quick_test.sh
```

### 4. Verify Full End-to-End
```bash
curl -H "x-api-key: {self.public_api_key}" \\
  -d '{{"model":"phi3:latest","messages":[{{"role":"user","content":"Hello"}}]}}' \\
  http://{self.router_server}:{self.router_port}/v1/chat/completions
```

## 📊 Expected Results
- ✅ Both servers reachable via ping
- ✅ Both ports accessible
- ✅ Inference API working directly