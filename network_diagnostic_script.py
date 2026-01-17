#!/usr/bin/env python3
"""
Kamatera Network Diagnostic Tool
Diagnoses network routing issues between Kamatera servers
"""

import json
import time
import asyncio
import aiohttp
import socket
from typing import Dict, List, Optional
import subprocess
import ping3

class KamateraNetworkDiagnostic:
    def __init__(self):
        self.primary_ollama = "http://192.175.23.150:8002"
        self.backup_router = "http://45.61.51.220:8000"
        self.server1_ip = "192.175.23.150"
        self.server2_ip = "45.61.51.220"
        self.timeout = 30
        
    def ping_server(self, ip: str, count: int = 3) -> Dict:
        """Ping a server to test basic connectivity"""
        try:
            result = subprocess.run(
                ["ping", "-c", str(count), ip], 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse ping output
                output_lines = result.stdout.split('\n')
                for line in output_lines:
                    if 'avg' in line or 'rtt' in line:
                        return {
                            "status": "reachable",
                            "ip": ip,
                            "ping_output": line.strip(),
                            "return_code": result.returncode
                        }
                
                return {
                    "status": "reachable", 
                    "ip": ip,
                    "return_code": result.returncode,
                    "raw_output": result.stdout
                }
            else:
                return {
                    "status": "unreachable",
                    "ip": ip,
                    "error": result.stderr,
                    "return_code": result.returncode
                }
        except Exception as e:
            return {
                "status": "error",
                "ip": ip,
                "error": str(e)
            }
    
    def check_port_connectivity(self, ip: str, port: int, timeout: int = 5) -> Dict:
        """Check if a specific port is accessible"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            return {
                "ip": ip,
                "port": port,
                "status": "open" if result == 0 else "closed",
                "error": None if result == 0 else "Connection refused"
            }
        except Exception as e:
            return {
                "ip": ip,
                "port": port,
                "status": "error",
                "error": str(e)
            }
    
    async def test_http_connectivity(self, url: str, headers: Dict = None) -> Dict:
        """Test HTTP connectivity to a URL"""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(
                    url,
                    headers=headers or {},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    response_time = time.time() - start_time
                    
                    return {
                        "url": url,
                        "status": "success",
                        "http_status": response.status,
                        "response_time": response_time,
                        "headers": dict(response.headers)
                    }
        except asyncio.TimeoutError:
            return {
                "url": url,
                "status": "timeout",
                "error": "Request timed out"
            }
        except Exception as e:
            return {
                "url": url,
                "status": "error", 
                "error": str(e)
            }
    
    async def test_router_chat_completion(self) -> Dict:
        """Test the specific endpoint that's failing"""
        payload = {
            "model": "phi3:latest",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        
        headers = {
            "x-api-key": "cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765",
            "Content-Type": "application/json"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.post(
                    f"{self.backup_router}/v1/chat/completions",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_time = time.time() - start_time
                    
                    response_data = await response.text()
                    
                    return {
                        "url": f"{self.backup_router}/v1/chat/completions",
                        "status": "success" if response.status == 200 else "failed",
                        "http_status": response.status,
                        "response_time": response_time,
                        "response_data": response_data[:500]  # First 500 chars
                    }
        except Exception as e:
            return {
                "url": f"{self.backup_router}/v1/chat/completions",
                "status": "error",
                "error": str(e)
            }
    
    async def run_comprehensive_diagnostics(self) -> Dict:
        """Run all network diagnostics"""
        print("🔍 Running Kamatera Network Diagnostics...")
        print("=" * 60)
        
        results = {}
        
        # 1. Basic ping tests
        print("\n📡 Basic Connectivity Tests...")
        results["ping_server1"] = self.ping_server(self.server1_ip)
        results["ping_server2"] = self.ping_server(self.server2_ip)
        
        print(f"   Server 1 (192.175.23.150): {results['ping_server1']['status']}")
        print(f"   Server 2 (45.61.51.220): {results['ping_server2']['status']}")
        
        # 2. Port connectivity tests
        print("\n🔌 Port Connectivity Tests...")
        results["port_8002_server1"] = self.check_port_connectivity(self.server1_ip, 8002)
        results["port_8000_server2"] = self.check_port_connectivity(self.server2_ip, 8000)
        
        print(f"   Server 1:8002: {results['port_8002_server1']['status']}")
        print(f"   Server 2:8000: {results['port_8000_server2']['status']}")
        
        # 3. HTTP connectivity tests
        print("\n🌐 HTTP Connectivity Tests...")
        results["http_server1_models"] = await self.test_http_connectivity(f"{self.primary_ollama}/api/tags")
        results["http_server2_health"] = await self.test_http_connectivity(f"{self.backup_router}/health")
        results["http_server2_chat"] = await self.test_router_chat_completion()
        
        print(f"   Server 1 Models API: {results['http_server1_models']['status']}")
        print(f"   Server 2 Health: {results['http_server2_health']['status']}")
        print(f"   Server 2 Chat Completion: {results['http_server2_chat']['status']}")
        
        # 4. Cross-server analysis
        print("\n🔗 Cross-Server Analysis...")
        server1_http_ok = results["http_server1_models"]["status"] == "success"
        server2_http_ok = results["http_server2_health"]["status"] == "success"
        chat_working = results["http_server2_chat"]["status"] == "success"
        
        results["cross_server_analysis"] = {
            "server1_direct_access": server1_http_ok,
            "server2_direct_access": server2_http_ok,
            "server2_chat_functional": chat_working,
            "routing_issue_confirmed": server2_http_ok and not chat_working,
            "inference_available": server1_http_ok,
            "router_authenticated": results["http_server2_chat"]["http_status"] != 401,
            "diagnosis": "Router can authenticate but cannot reach inference server"
        }
        
        return results
    
    def generate_report(self, results: Dict) -> str:
        """Generate a comprehensive diagnostic report"""
        report = []
        report.append("=" * 80)
        report.append("KAMATERA NETWORK DIAGNOSTIC REPORT")
        report.append("=" * 80)
        
        # Summary
        analysis = results.get("cross_server_analysis", {})
        report.append("\n🎯 SUMMARY:")
        report.append(f"   Server 1 Direct Access: {'✅ Working' if analysis.get('server1_direct_access') else '❌ Failed'}")
        report.append(f"   Server 2 Direct Access: {'✅ Working' if analysis.get('server2_direct_access') else '❌ Failed'}")  
        report.append(f"   Server 2 Chat Function: {'✅ Working' if analysis.get('server2_chat_functional') else '❌ Failed'}")
        report.append(f"   Router Authentication: {'✅ Working' if analysis.get('router_authenticated') else '❌ Failed'}")
        
        if analysis.get('routing_issue_confirmed'):
            report.append(f"\n🚨 ISSUE IDENTIFIED:")
            report.append(f"   {analysis.get('diagnosis', 'Unknown routing issue')}")
        
        # Detailed results
        report.append("\n📊 DETAILED RESULTS:")
        report.append("\nPing Tests:")
        for key in ["ping_server1", "ping_server2"]:
            result = results.get(key, {})
            report.append(f"   {key}: {result.get('status', 'unknown')}")
        
        report.append("\nPort Tests:")
        for key in ["port_8002_server1", "port_8000_server2"]:
            result = results.get(key, {})
            report.append(f"   {key}: {result.get('status', 'unknown')}")
        
        report.append("\nHTTP Tests:")
        for key in ["http_server1_models", "http_server2_health", "http_server2_chat"]:
            result = results.get(key, {})
            report.append(f"   {key}: {result.get('status', 'unknown')}")
            if "response_time" in result:
                report.append(f"      Response time: {result['response_time']:.2f}s")
        
        # Recommendations
        report.append("\n💡 RECOMMENDATIONS:")
        if not analysis.get('routing_issue_confirmed'):
            report.append("   • No obvious network routing issues detected")
            report.append("   • Check application-level configuration")
        else:
            report.append("   • Router can authenticate but cannot reach inference server")
            report.append("   • Likely internal network routing issue between servers")
            report.append("   • Check firewall rules for internal traffic")
            report.append("   • Verify internal DNS resolution")
            report.append("   • Check if servers are on same private network/VPC")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)

async def main():
    diagnostic = KamateraNetworkDiagnostic()
    results = await diagnostic.run_comprehensive_diagnostics()
    
    # Generate and display report
    report = diagnostic.generate_report(results)
    print(report)
    
    # Save detailed results
    with open("/Users/fuaadabdullah/ForgeMonorepo/network_diagnostic_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print("\n📄 Detailed results saved to: network_diagnostic_results.json")

if __name__ == "__main__":
    asyncio.run(main())