#!/usr/bin/env python3
"""
Comprehensive Kamatera Router & Chat Health Diagnostic Tool
Performs deep network analysis and API testing to identify the root cause of routing issues.
"""

import json
import time
import asyncio
import aiohttp
import socket
import subprocess
import re
import sys
import traceback
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime

class ComprehensiveKamateraDiagnostic:
    def __init__(self):
        # Server Configuration
        self.inference_server = "192.175.23.150"
        self.router_server = "45.61.51.220"
        self.inference_port = 8002
        self.router_port = 8000
        
        # API Keys
        self.inference_api_key = "206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158"
        self.internal_api_key = "dcb2546960bb963c61db8b56939e8e3c25398f073409938882d6b07a7741de89"
        self.public_api_key = "cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765"
        
        # Configuration
        self.timeout = 30
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "servers": {
                "inference": {"ip": self.inference_server, "port": self.inference_port},
                "router": {"ip": self.router_server, "port": self.router_port}
            },
            "tests": {}
        }
        
    async def run_full_diagnostic(self) -> Dict:
        """Run complete diagnostic suite"""
        print("🚀 Starting Comprehensive Kamatera Diagnostic")
        print("=" * 60)
        print(f"Inference Server: {self.inference_server}:{self.inference_port}")
        print(f"Router Server: {self.router_server}:{self.router_port}")
        print(f"Timestamp: {self.results['timestamp']}")
        print()
        
        try:
            # Phase 1: Basic Network Connectivity
            await self._test_basic_connectivity()
            
            # Phase 2: Port & Service Testing
            await self._test_port_connectivity()
            
            # Phase 3: HTTP API Testing
            await self._test_http_endpoints()
            
            # Phase 4: Internal Routing Analysis
            await self._test_internal_routing()
            
            # Phase 5: Authentication Testing
            await self._test_authentication()
            
            # Phase 6: Chat Flow Testing
            await self._test_chat_flow()
            
            # Phase 7: Analysis & Recommendations
            self._analyze_results()
            
            # Phase 8: Generate Report
            self._generate_report()
            
        except Exception as e:
            print(f"❌ Diagnostic failed: {str(e)}")
            traceback.print_exc()
            self.results["error"] = str(e)
        
        return self.results
    
    async def _test_basic_connectivity(self):
        """Test basic network connectivity with detailed analysis"""
        print("🔍 PHASE 1: Basic Network Connectivity")
        print("-" * 40)
        
        connectivity_tests = {
            "ping_inference": {"server": self.inference_server, "name": "Inference Server"},
            "ping_router": {"server": self.router_server, "name": "Router Server"},
            "traceroute_inference": {"server": self.inference_server, "name": "Inference Server Route"},
            "traceroute_router": {"server": self.router_server, "name": "Router Server Route"}
        }
        
        results = {}
        
        # Ping tests
        for test_name, config in connectivity_tests.items():
            if "ping" in test_name:
                results[test_name] = await self._run_ping_test(config["server"], config["name"])
            elif "traceroute" in test_name:
                results[test_name] = await self._run_traceroute_test(config["server"], config["name"])
        
        self.results["tests"]["connectivity"] = results
        
        # Summary
        successful_pings = sum(1 for test in results.values() if test.get("status") == "success")
        print(f"📊 Ping Results: {successful_pings}/{len([k for k in results.keys() if 'ping' in k])} successful")
        print()
    
    async def _test_port_connectivity(self):
        """Test port connectivity with detailed analysis"""
        print("🔌 PHASE 2: Port & Service Connectivity")
        print("-" * 40)
        
        port_tests = [
            {"name": "Inference Port 8002", "server": self.inference_server, "port": self.inference_port},
            {"name": "Router Port 8000", "server": self.router_server, "port": self.router_port},
            {"name": "Inference Alt Port 8000", "server": self.inference_server, "port": 8000},
            {"name": "Router Alt Port 8002", "server": self.router_server, "port": 8002}
        ]
        
        results = {}
        
        for test in port_tests:
            results[test["name"]] = await self._test_port(test["server"], test["port"])
        
        self.results["tests"]["port_connectivity"] = results
        
        # Summary
        open_ports = sum(1 for test in results.values() if test.get("status") == "open")
        print(f"📊 Port Results: {open_ports}/{len(results)} ports open")
        print()
    
    async def _test_http_endpoints(self):
        """Test HTTP endpoints with comprehensive analysis"""
        print("🌐 PHASE 3: HTTP API Endpoint Testing")
        print("-" * 40)
        
        endpoints = [
            {
                "name": "Inference Models API",
                "url": f"http://{self.inference_server}:{self.inference_port}/api/tags",
                "method": "GET",
                "headers": {"x-api-key": self.inference_api_key}
            },
            {
                "name": "Inference Health",
                "url": f"http://{self.inference_server}:{self.inference_port}/health",
                "method": "GET"
            },
            {
                "name": "Router Health",
                "url": f"http://{self.router_server}:{self.router_port}/health",
                "method": "GET"
            },
            {
                "name": "Router Chat Completions",
                "url": f"http://{self.router_server}:{self.router_port}/v1/chat/completions",
                "method": "POST",
                "headers": {"x-api-key": self.public_api_key},
                "json": {
                    "model": "phi3:latest",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
            }
        ]
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for endpoint in endpoints:
                results[endpoint["name"]] = await self._test_http_endpoint(session, endpoint)
        
        self.results["tests"]["http_endpoints"] = results
        
        # Summary
        successful_requests = sum(1 for test in results.values() if test.get("status") == "success")
        print(f"📊 HTTP Results: {successful_requests}/{len(results)} endpoints accessible")
        print()
    
    async def _test_internal_routing(self):
        """Test internal routing between servers"""
        print("🔗 PHASE 4: Internal Server Routing Analysis")
        print("-" * 40)
        
        internal_tests = [
            {
                "name": "Router → Inference (Direct)",
                "description": "Direct HTTP request from Router server to Inference server",
                "url": f"http://{self.inference_server}:{self.inference_port}/api/tags",
                "headers": {"x-api-key": self.internal_api_key}
            },
            {
                "name": "Router → Inference Health",
                "description": "Router server checking Inference health",
                "url": f"http://{self.inference_server}:{self.inference_port}/health",
                "headers": {"x-api-key": self.internal_api_key}
            }
        ]
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for test in internal_tests:
                results[test["name"]] = await self._test_http_endpoint(session, test)
        
        self.results["tests"]["internal_routing"] = results
        
        # Summary
        successful_internal = sum(1 for test in results.values() if test.get("status") == "success")
        print(f"📊 Internal Routing: {successful_internal}/{len(results)} internal connections successful")
        print()
    
    async def _test_authentication(self):
        """Test API authentication comprehensively"""
        print("🔐 PHASE 5: Authentication Testing")
        print("-" * 40)
        
        auth_tests = [
            {
                "name": "Inference API Key",
                "url": f"http://{self.inference_server}:{self.inference_port}/api/tags",
                "headers": {"x-api-key": self.inference_api_key}
            },
            {
                "name": "Internal API Key (Inference)",
                "url": f"http://{self.inference_server}:{self.inference_port}/api/tags",
                "headers": {"x-api-key": self.internal_api_key}
            },
            {
                "name": "Public API Key (Router)",
                "url": f"http://{self.router_server}:{self.router_port}/v1/chat/completions",
                "headers": {"x-api-key": self.public_api_key},
                "json": {"model": "phi3:latest", "messages": [{"role": "user", "content": "Test"}]}
            }
        ]
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for test in auth_tests:
                results[test["name"]] = await self._test_http_endpoint(session, test)
        
        self.results["tests"]["authentication"] = results
        
        # Summary
        successful_auth = sum(1 for test in results.values() if test.get("status") == "success")
        print(f"📊 Authentication: {successful_auth}/{len(results)} auth tests successful")
        print()
    
    async def _test_chat_flow(self):
        """Test complete chat flow end-to-end"""
        print("💬 PHASE 6: Chat Flow Testing")
        print("-" * 40)
        
        chat_tests = [
            {
                "name": "Direct Inference Chat",
                "description": "Direct chat with Inference server",
                "url": f"http://{self.inference_server}:{self.inference_port}/api/chat",
                "headers": {"x-api-key": self.inference_api_key},
                "json": {
                    "model": "phi3:latest",
                    "messages": [{"role": "user", "content": "Hello from direct test"}]
                }
            },
            {
                "name": "Router Chat (Expected to Fail)",
                "description": "Chat through Router API (likely to show 'All servers unavailable')",
                "url": f"http://{self.router_server}:{self.router_port}/v1/chat/completions",
                "headers": {"x-api-key": self.public_api_key},
                "json": {
                    "model": "phi3:latest",
                    "messages": [{"role": "user", "content": "Hello from router test"}]
                }
            }
        ]
        
        results = {}
        async with aiohttp.ClientSession() as session:
            for test in chat_tests:
                results[test["name"]] = await self._test_http_endpoint(session, test)
        
        self.results["tests"]["chat_flow"] = results
        
        # Summary
        successful_chats = sum(1 for test in results.values() if test.get("status") == "success")
        print(f"📊 Chat Flow: {successful_chats}/{len(results)} chat tests successful")
        print()
    
    async def _run_ping_test(self, server_ip: str, server_name: str) -> Dict:
        """Run detailed ping test"""
        try:
            print(f"  📡 Pinging {server_name} ({server_ip})...")
            start_time = time.time()
            
            result = subprocess.run(
                ["ping", "-c", "5", "-W", "10", server_ip],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            response_time = time.time() - start_time
            
            if result.returncode == 0:
                # Parse ping results
                output = result.stdout
                
                # Extract statistics
                packet_loss_match = re.search(r'(\d+)% packet loss', output)
                packet_loss = packet_loss_match.group(1) if packet_loss_match else "0"
                
                # Extract times
                times = re.findall(r'time=([0-9.]+)', output)
                avg_time = sum(float(t) for t in times) / len(times) if times else 0
                
                return {
                    "status": "success",
                    "server_ip": server_ip,
                    "packet_loss": f"{packet_loss}%",
                    "avg_time": f"{avg_time:.2f}ms",
                    "min_time": f"{min(float(t) for t in times):.2f}ms" if times else "N/A",
                    "max_time": f"{max(float(t) for t in times):.2f}ms" if times else "N/A",
                    "response_time": response_time,
                    "raw_output": output
                }
            else:
                return {
                    "status": "failed",
                    "server_ip": server_ip,
                    "error": result.stderr,
                    "response_time": response_time
                }
                
        except Exception as e:
            return {
                "status": "error",
                "server_ip": server_ip,
                "error": str(e)
            }
    
    async def _run_traceroute_test(self, server_ip: str, server_name: str) -> Dict:
        """Run traceroute test"""
        try:
            print(f"  🛣️  Tracerouting {server_name} ({server_ip})...")
            
            result = subprocess.run(
                ["traceroute", "-w", "2", "-m", "15", server_ip],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "server_ip": server_ip,
                    "hops": result.stdout,
                    "raw_output": result.stdout
                }
            else:
                return {
                    "status": "failed",
                    "server_ip": server_ip,
                    "error": result.stderr,
                    "raw_output": result.stdout
                }
                
        except Exception as e:
            return {
                "status": "error",
                "server_ip": server_ip,
                "error": str(e)
            }
    
    async def _test_port(self, server_ip: str, port: int) -> Dict:
        """Test port connectivity"""
        try:
            print(f"  🔌 Testing port {server_ip}:{port}...")
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            start_time = time.time()
            
            result = sock.connect_ex((server_ip, port))
            response_time = time.time() - start_time
            sock.close()
            
            if result == 0:
                return {
                    "status": "open",
                    "server_ip": server_ip,
                    "port": port,
                    "response_time": response_time
                }
            else:
                return {
                    "status": "closed",
                    "server_ip": server_ip,
                    "port": port,
                    "response_time": response_time,
                    "error": "Connection refused"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "server_ip": server_ip,
                "port": port,
                "error": str(e)
            }
    
    async def _test_http_endpoint(self, session: aiohttp.ClientSession, endpoint: Dict) -> Dict:
        """Test HTTP endpoint with comprehensive error handling"""
        try:
            name = endpoint["name"]
            url = endpoint["url"]
            method = endpoint["method"]
            headers = endpoint.get("headers", {})
            json_data = endpoint.get("json")
            
            print(f"  🌐 Testing {name}...")
            start_time = time.time()
            
            if method == "GET":
                async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    response_time = time.time() - start_time
                    response_data = await response.text()
                    
                    return {
                        "status": "success" if response.status < 400 else "failed",
                        "http_status": response.status,
                        "response_time": response_time,
                        "headers": dict(response.headers),
                        "response_data": response_data[:1000],  # First 1000 chars
                        "url": url
                    }
                    
            elif method == "POST":
                async with session.post(url, headers=headers, json=json_data, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                    response_time = time.time() - start_time
                    response_data = await response.text()
                    
                    return {
                        "status": "success" if response.status < 400 else "failed",
                        "http_status": response.status,
                        "response_time": response_time,
                        "headers": dict(response.headers),
                        "response_data": response_data[:1000],
                        "url": url,
                        "json_sent": json_data
                    }
                    
        except asyncio.TimeoutError:
            return {
                "status": "timeout",
                "url": url,
                "error": "Request timed out"
            }
        except Exception as e:
            return {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    def _analyze_results(self):
        """Analyze all test results and
    def _analyze_results(self):
        """Analyze all test results and provide recommendations"""
        print("🔍 PHASE 7: Analysis & Recommendations")
        print("-" * 40)
        
        analysis = {
            "root_cause": None,
            "issue_confirmed": False,
            "network_issues": [],
            "application_issues": [],
            "authentication_issues": [],
            "recommendations": [],
            "confidence_score": 0
        }
        
        # Analyze connectivity results
        connectivity = self.results.get("tests", {}).get("connectivity", {})
        ping_results = {k: v for k, v in connectivity.items() if "ping" in k}
        
        all_servers_reachable = all(test.get("status") == "success" for test in ping_results.values())
        if not all_servers_reachable:
            analysis["network_issues"].append("Basic connectivity failure between servers")
            analysis["recommendations"].append("Check network routing and firewall rules")
        
        # Analyze port connectivity
        port_tests = self.results.get("tests", {}).get("port_connectivity", {})
        inference_port_open = port_tests.get("Inference Port 8002", {}).get("status") == "open"
        router_port_open = port_tests.get("Router Port 8000", {}).get("status") == "open"
        
        if not inference_port_open:
            analysis["network_issues"].append("Inference server port 8002 not accessible")
        if not router_port_open:
            analysis["network_issues"].append("Router server port 8000 not accessible")
        
        # Analyze HTTP endpoints
        http_tests = self.results.get("tests", {}).get("http_endpoints", {})
        inference_http_ok = http_tests.get("Inference Models API", {}).get("status") == "success"
        router_chat_ok = http_tests.get("Router Chat Completions", {}).get("status") == "success"
        
        # Check for "All servers unavailable" response
        router_chat_response = http_tests.get("Router Chat Completions", {}).get("response_data", "")
        if "all servers unavailable" in router_chat_response.lower():
            analysis["issue_confirmed"] = True
            analysis["root_cause"] = "Router cannot reach Inference server internally"
            analysis["application_issues"].append("Router API returns 'All servers unavailable'")
            analysis["recommendations"].append("Fix internal network routing between servers")
            analysis["confidence_score"] = 90
        
        # Analyze internal routing
        internal_tests = self.results.get("tests", {}).get("internal_routing", {})
        internal_working = any(test.get("status") == "success" for test in internal_tests.values())
        
        if inference_http_ok and not internal_working:
            analysis["issue_confirmed"] = True
            analysis["network_issues"].append("External access works but internal routing fails")
            analysis["recommendations"].append("Check internal network configuration and firewall rules")
            if not analysis["root_cause"]:
                analysis["root_cause"] = "Internal network routing issue"
            analysis["confidence_score"] = max(analysis["confidence_score"], 80)
        
        # Analyze authentication
        auth_tests = self.results.get("tests", {}).get("authentication", {})
        auth_working = any(test.get("status") == "success" for test in auth_tests.values())
        
        if not auth_working:
            analysis["authentication_issues"].append("API authentication not working")
            analysis["recommendations"].append("Verify API keys and authentication headers")
        
        # Generate final analysis summary
        if analysis["confidence_score"] >= 80:
            print(f"✅ HIGH CONFIDENCE: Root cause identified")
            print(f"   Root Cause: {analysis['root_cause']}")
        elif analysis["confidence_score"] >= 50:
            print(f"⚠️ MEDIUM CONFIDENCE: Likely cause identified")
            print(f"   Likely Cause: {analysis['root_cause']}")
        else:
            print(f"❌ LOW CONFIDENCE: Need more diagnostics")
        
        print(f"   Network Issues: {len(analysis['network_issues'])}")
        print(f"   Application Issues: {len(analysis['application_issues'])}")
        print(f"   Authentication Issues: {len(analysis['authentication_issues'])}")
        print(f"   Recommendations: {len(analysis['recommendations'])}")
        
        self.results["analysis"] = analysis
        return analysis
    
    def _generate_report(self):
        """Generate comprehensive diagnostic report"""
        print("\n📄 PHASE 8: Generating Report")
        print("-" * 40)
        
        report = {
            "executive_summary": self._generate_executive_summary(),
            "detailed_results": self.results,
            "next_steps": self._generate_next_steps(),
            "fix_scripts": self._generate_fix_scripts_list()
        }
        
        # Save JSON report
        report_file = f"kamatera_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Generate Markdown report
        md_report_file = f"kamatera_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        self._generate_markdown_report(report, md_report_file)
        
        print(f"✅ JSON Report saved: {report_file}")
        print(f"✅ Markdown Report saved: {md_report_file}")
        print()
        
        return report
    
    def _generate_executive_summary(self) -> Dict:
        """Generate executive summary of findings"""
        analysis = self.results.get("analysis", {})
        
        summary = {
            "issue_status": "IDENTIFIED" if analysis.get("issue_confirmed") else "INVESTIGATING",
            "root_cause": analysis.get("root_cause", "Unknown"),
            "confidence": analysis.get("confidence_score", 0),
            "impact": "HIGH" if analysis.get("issue_confirmed") else "MEDIUM",
            "urgency": "IMMEDIATE" if analysis.get("confidence_score", 0) >= 80 else "NORMAL",
            "affected_services": ["Router API", "Chat Completions"],
            "current_availability": "PARTIAL" if analysis.get("issue_confirmed") else "UNKNOWN"
        }
        
        return summary
    
    def _generate_next_steps(self) -> List[str]:
        """Generate prioritized next steps"""
        analysis = self.results.get("analysis", {})
        
        steps = []
        
        if analysis.get("confidence_score", 0) >= 80:
            steps.extend([
                "Deploy firewall configuration fixes to both servers",
                "Update network routing rules for internal communication",
                "Restart Router and Inference services",
                "Verify end-to-end chat functionality"
            ])
        else:
            steps.extend([
                "Run additional network diagnostics",
                "Check server configurations manually",
                "Verify firewall rules on both servers",
                "Test internal API communication directly"
            ])
        
        steps.extend([
            "Implement enhanced monitoring",
            "Set up automated health checks",
            "Create maintenance procedures"
        ])
        
        return steps
    
    def _generate_fix_scripts_list(self) -> Dict:
        """Generate list of needed fix scripts"""
        analysis = self.results.get("analysis", {})
        
        scripts = {
            "firewall_fix": {
                "required": analysis.get("network_issues", []),
                "status": "pending",
                "priority": "HIGH"
            },
            "network_config": {
                "required": analysis.get("network_issues", []),
                "status": "pending", 
                "priority": "HIGH"
            },
            "service_restart": {
                "required": ["Service restart after config changes"],
                "status": "pending",
                "priority": "MEDIUM"
            },
            "validation_test": {
                "required": ["End-to-end testing after fixes"],
                "status": "pending",
                "priority": "MEDIUM"
            }
        }
        
        return scripts
    
    def _generate_markdown_report(self, report: Dict, filename: str):
        """Generate detailed markdown report"""
        summary = report["executive_summary"]
        analysis = self.results.get("analysis", {})
        
        md_content = f"""# Kamatera Router Diagnostic Report

## Executive Summary

**Issue Status**: {summary['issue_status']}  
**Root Cause**: {summary['root_cause']}  
**Confidence Level**: {summary['confidence']}%  
**Impact**: {summary['impact']}  
**Urgency**: {summary['urgency']}  

## Test Results Summary

### Network Connectivity
"""
        
        # Add connectivity results
        connectivity = self.results.get("tests", {}).get("connectivity", {})
        for test_name, result in connectivity.items():
            status = "✅" if result.get("status") == "success" else "❌"
            md_content += f"- {test_name}: {status}\n"
        
        md_content += "\n### Port Connectivity\n"
        
        # Add port results
        port_tests = self.results.get("tests", {}).get("port_connectivity", {})
        for test_name, result in port_tests.items():
            status = "✅" if result.get("status") == "open" else "❌"
            md_content += f"- {test_name}: {status}\n"
        
        md_content += "\n### HTTP Endpoints\n"
        
        # Add HTTP results
        http_tests = self.results.get("tests", {}).get("http_endpoints", {})
        for test_name, result in http_tests.items():
            status = "✅" if result.get("status") == "success" else "❌"
            md_content += f"- {test_name}: {status}\n"
        
        md_content += "\n### Internal Routing\n"
        
        # Add internal routing results
        internal_tests = self.results.get("tests", {}).get("internal_routing", {})
        for test_name, result in internal_tests.items():
            status = "✅" if result.get("status") == "success" else "❌"
            md_content += f"- {test_name}: {status}\n"
        
        md_content += f"\n## Issues Identified\n\n"
        
        # Add identified issues
        if analysis.get("network_issues"):
            md_content += "**Network Issues:**\n"
            for issue in analysis["network_issues"]:
                md_content += f"- {issue}\n"
            md_content += "\n"
        
        if analysis.get("application_issues"):
            md_content += "**Application Issues:**\n"
            for issue in analysis["application_issues"]:
                md_content += f"- {issue}\n"
            md_content += "\n"
        
        if analysis.get("authentication_issues"):
            md_content += "**Authentication Issues:**\n"
            for issue in analysis["authentication_issues"]:
                md_content += f"- {issue}\n"
            md_content += "\n"
        
        md_content += "## Recommendations\n\n"
        
        # Add recommendations
        for i, rec in enumerate(analysis.get("recommendations", []), 1):
            md_content += f"{i}. {rec}\n"
        
        md_content += f"\n## Next Steps\n\n"
        
        # Add next steps
        for i, step in enumerate(report["next_steps"], 1):
            md_content += f"{i}. {step}\n"
        
        md_content += f"\n---\n\n*Report generated at {self.results['timestamp']}*"
        
        # Save markdown report
        with open(filename, 'w') as f:
            f.write(md_content)

async def main():
    """Main function to run the diagnostic"""
    diagnostic = ComprehensiveKamateraDiagnostic()
    results = await diagnostic.run_full_diagnostic()
    
    # Print final summary
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSTIC COMPLETE")
    print("=" * 60)
    
    analysis = results.get("analysis", {})
    if analysis.get("issue_confirmed"):
        print(f"✅ ROOT CAUSE IDENTIFIED: {analysis['root_cause']}")
        print(f"📊 CONFIDENCE: {analysis['confidence_score']}%")
        print(f"🔧 RECOMMENDATIONS: {len(analysis['recommendations'])} items")
    else:
        print("⚠️ ISSUE NOT FULLY DIAGNOSED")
        print("📊 ADDITIONAL TESTING REQUIRED")
    
    print(f"📄 Reports generated in current directory")
    print(f"📈 Total tests run: {sum(len(tests) for tests in results.get('tests', {}).values())}")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
