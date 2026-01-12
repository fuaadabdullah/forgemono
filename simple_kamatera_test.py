#!/usr/bin/env python3
"""
Simple Kamatera Network Test
"""

import subprocess
import socket
import requests
import json
import time

def test_ping():
    """Test ping connectivity"""
    servers = [
        ("Inference", "192.175.23.150"),
        ("Router", "45.61.51.220")
    ]
    
    results = {}
    for name, ip in servers:
        try:
            result = subprocess.run(
                ["ping", "-c", "2", ip],
                capture_output=True,
                text=True,
                timeout=10
            )
            results[name] = "reachable" if result.returncode == 0 else "unreachable"
            print(f"  {name}: {'✅' if result.returncode == 0 else '❌'} {results[name]}")
        except Exception as e:
            results[name] = f"error: {str(e)}"
            print(f"  {name}: ❌ error")
    
    return results

def test_ports():
    """Test port connectivity"""
    tests = [
        ("Inference", "192.175.23.150", 8002),
        ("Router", "45.61.51.220", 8000)
    ]
    
    results = {}
    for name, ip, port in tests:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((ip, port))
            sock.close()
            status = "open" if result == 0 else "closed"
            results[f"{name}_{port}"] = status
            print(f"  {name}:{port}: {'✅' if result == 0 else '❌'} {status}")
        except Exception as e:
            results[f"{name}_{port}"] = f"error: {str(e)}"
            print(f"  {name}:{port}: ❌ error")
    
    return results

def test_http():
    """Test HTTP endpoints"""
    results = {}
    
    # Test inference
    try:
        headers = {"x-api-key": "206e61fdeda2267c9a4ecac3997c4eae7ebd20038282445f7524a84a78ac0158"}
        response = requests.get("http://192.175.23.150:8002/api/tags", headers=headers, timeout=10)
        results["inference"] = "working" if response.status_code == 200 else f"failed: {response.status_code}"
        print(f"  Inference API: {'✅' if response.status_code == 200 else '❌'} {results['inference']}")
    except Exception as e:
        results["inference"] = f"error: {str(e)}"
        print(f"  Inference API: ❌ error")
    
    # Test router health
    try:
        response = requests.get("http://45.61.51.220:8000/health", timeout=10)
        results["router_health"] = "working" if response.status_code == 200 else f"failed: {response.status_code}"
        print(f"  Router Health: {'✅' if response.status_code == 200 else '❌'} {results['router_health']}")
    except Exception as e:
        results["router_health"] = f"error: {str(e)}"
        print(f"  Router Health: ❌ error")
    
    # Test router chat
    try:
        payload = {
            "model": "phi3:latest",
            "messages": [{"role": "user", "content": "Hello"}]
        }
        headers = {
            "x-api-key": "cef5587890c73a5316a9a2c4ed851d97beb89fd28443885aad6e570dabd5f765",
            "Content-Type": "application/json"
        }
        response = requests.post(
            "http://45.61.51.220:8000/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )
        results["router_chat"] = "working" if response.status_code == 200 else f"failed: {response.status_code}"
        print(f"  Router Chat: {'✅' if response.status_code == 200 else '❌'} {results['router_chat']}")
        if response.status_code != 200:
            print(f"    Response: {response.text[:200]}")
    except Exception as e:
        results["router_chat"] = f"error: {str(e)}"
        print(f"  Router Chat: ❌ error")
    
    return results

def main():
    print("🔍 KAMATERA NETWORK TEST")
    print("=" * 40)
    
    # Test connectivity
    print("\n📡 Testing Ping...")
    ping_results = test_ping()
    
    print("\n🔌 Testing Ports...")
    port_results = test_ports()
    
    print("\n🌐 Testing HTTP...")
    http_results = test_http()
    
    # Analyze results
    print("\n📊 ANALYSIS")
    print("=" * 40)
    
    inference_reachable = ping_results.get("Inference") == "reachable"
    router_reachable = ping_results.get("Router") == "reachable"
    inference_port_open = port_results.get("Inference_8002") == "open"
    router_port_open = port_results.get("Router_8000") == "open"
    inference_http_ok = http_results.get("inference", "").startswith("working")
    router_health_ok = http_results.get("router_health", "").startswith("working")
    router_chat_ok = http_results.get("router_chat", "").startswith("working")
    
    print(f"Basic Connectivity:     Inference: {'✅' if inference_reachable else '❌'} | Router: {'✅' if router_reachable else '❌'}")
    print(f"Port Accessibility:     Inference: {'✅' if inference_port_open else '❌'} | Router: {'✅' if router_port_open else '❌'}")
    print(f"HTTP Endpoints:         Inference: {'✅' if inference_http_ok else '❌'} | Router: {'✅' if router_health_ok else '❌'}")
    print(f"Router Chat Flow:       {'✅ WORKING' if router_chat_ok else '❌ FAILED'}")
    
    # Save results
    results = {
        "ping": ping_results,
        "ports": port_results,
        "http": http_results,
        "analysis": {
            "inference_reachable": inference_reachable,
            "router_reachable": router_reachable,
            "inference_port_open": inference_port_open,
            "router_port_open": router_port_open,
            "inference_http_ok": inference_http_ok,
            "router_health_ok": router_health_ok,
            "router_chat_ok": router_chat_ok,
            "issue_confirmed": inference_reachable and inference_port_open and inference_http_ok and not router_chat_ok
        }
    }
    
    with open("kamatera_test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: kamatera_test_results.json")
    
    if results["analysis"]["issue_confirmed"]:
        print("\n🚨 ROUTING ISSUE CONFIRMED!")
        print("   The Router can authenticate but cannot reach the Inference server internally.")
        print("   This confirms firewall/network routing issues between servers.")
    else:
        print("\n✅ NO ROUTING ISSUES DETECTED")
        print("   Both servers can communicate properly.")

if __name__ == "__main__":
    main()