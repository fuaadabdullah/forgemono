#!/usr/bin/env python3
"""
Diagnostic script for llama.cpp build issues in Kamatera
Run this in Kamatera to troubleshoot build problems
"""

import os
import subprocess


def run_command(cmd, description=""):
    """Run a command and return the result"""
    print(f"\n🔍 {description}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    try:
        result = subprocess.run(
            cmd, shell=isinstance(cmd, str), capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅ Success")
            if result.stdout:
                print(
                    "Output:",
                    result.stdout[:500] + "..."
                    if len(result.stdout) > 500
                    else result.stdout,
                )
        else:
            print("❌ Failed")
            print(
                "Error:",
                result.stderr[:500] + "..."
                if len(result.stderr) > 500
                else result.stderr,
            )
        return result
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


def diagnose_llama_build():
    """Comprehensive diagnosis of llama.cpp build issues"""

    print("🔧 llama.cpp Build Diagnostic")
    print("=" * 50)

    # Check current directory
    print(f"📂 Current working directory: {os.getcwd()}")

    # Check if llama.cpp directory exists
    if not os.path.exists("./llama.cpp"):
        print("❌ llama.cpp directory not found!")
        print("💡 Solution: Re-run cell 2 to clone and build llama.cpp")
        return

    print("✅ llama.cpp directory exists")

    # Check what's in the llama.cpp directory
    print("\n📁 Contents of llama.cpp directory:")
    try:
        result = subprocess.run(
            ["ls", "-la", "./llama.cpp"], capture_output=True, text=True
        )
        print(result.stdout)
    except Exception as e:
        print(f"Could not list directory: {e}")

    # Check if Makefile exists
    if not os.path.exists("./llama.cpp/Makefile"):
        print("❌ Makefile not found in llama.cpp directory!")
        print(
            "💡 The clone may have failed. Try: rm -rf llama.cpp && git clone https://github.com/ggerganov/llama.cpp.git"
        )
        return

    print("✅ Makefile found")

    # Check if build directory exists
    if not os.path.exists("./llama.cpp/build"):
        print("❌ build directory not found!")
        print("💡 Build hasn't started. Try: cd llama.cpp && make -j$(nproc)")
        return

    print("✅ build directory exists")

    # Check build directory contents
    print("\n📁 Contents of llama.cpp/build directory:")
    try:
        result = subprocess.run(
            ["ls", "-la", "./llama.cpp/build"], capture_output=True, text=True
        )
        print(result.stdout)
    except Exception as e:
        print(f"Could not list build directory: {e}")

    # Check for bin directory
    if os.path.exists("./llama.cpp/build/bin"):
        print("\n📁 Contents of llama.cpp/build/bin directory:")
        try:
            result = subprocess.run(
                ["ls", "-la", "./llama.cpp/build/bin"], capture_output=True, text=True
            )
            print(result.stdout)
        except Exception as e:
            print(f"Could not list bin directory: {e}")
    else:
        print("❌ build/bin directory not found!")

    # Check for llama-server binary in various locations
    binary_locations = [
        "./llama.cpp/build/bin/llama-server",
        "./llama.cpp/bin/llama-server",
        "./llama.cpp/llama-server",
        "./llama.cpp/build/llama-server",
    ]

    found_binary = None
    for location in binary_locations:
        if os.path.exists(location):
            found_binary = location
            print(f"✅ Found llama-server binary at: {location}")
            break

    if not found_binary:
        print("❌ llama-server binary not found in any expected location!")

        # Try to build it
        print("\n🔨 Attempting to build llama.cpp...")
        os.chdir("./llama.cpp")

        # Clean first
        run_command("make clean", "Cleaning previous build")

        # Build
        result = run_command("make -j$(nproc)", "Building llama.cpp")
        os.chdir("..")

        if result and result.returncode == 0:
            print("✅ Build completed successfully!")

            # Check again for binary
            for location in binary_locations:
                if os.path.exists(location):
                    found_binary = location
                    print(f"✅ Found llama-server binary at: {location}")
                    break
        else:
            print("❌ Build failed!")
            print("\n🔧 Troubleshooting steps:")
            print("1. Check if you have enough disk space: df -h")
            print("2. Check available memory: free -h")
            print("3. Try building with fewer jobs: make -j2")
            print(
                "4. Check for missing dependencies: apt-get install -y build-essential cmake"
            )
            return

    if found_binary:
        print(f"\n✅ SUCCESS: llama-server found at {found_binary}")

        # Test if binary is executable
        try:
            result = subprocess.run(
                [found_binary, "--version"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print("✅ Binary is executable")
                print("Version info:", result.stdout.strip())
            else:
                print("❌ Binary exists but not executable")
                print("Error:", result.stderr)
        except Exception as e:
            print(f"❌ Error testing binary: {e}")
    else:
        print("\n❌ FAILED: Could not find or build llama-server binary")


if __name__ == "__main__":
    diagnose_llama_build()
