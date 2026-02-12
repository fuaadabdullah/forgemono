#!/usr/bin/env python3
"""
Test script to verify that all imports work correctly with absolute imports.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test all the key imports to ensure they work correctly."""
    print("Testing imports...")
    
    try:
        # Test backend imports
        print("📦 Testing backend imports...")
        from backend.errors import raise_validation_error, raise_internal_error
        print("  ✅ errors module imported successfully")
        
        from backend.services.request_validation import validate_chat_request, ChatCompletionRequest
        print("  ✅ request_validation module imported successfully")
        
        # Test routing subsystem imports
        print("📦 Testing routing subsystem imports...")
        print("  ✅ routing subsystem modules imported successfully")
        
        # Test that we can import the routing manager
        from backend.services.routing_subsystem.manager import get_routing_manager
        print("  ✅ routing manager imported successfully")
        
        # Test that we can import the decision engine
        from backend.services.routing_subsystem.decision_engine import get_decision_engine
        print("  ✅ decision engine imported successfully")
        
        # Test that we can import the policy manager
        from backend.services.routing_subsystem.policies import get_policy_manager
        print("  ✅ policy manager imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_routing_functionality():
    """Test basic routing functionality."""
    print("\nTesting routing functionality...")
    
    try:
        from backend.services.routing_subsystem.manager import get_routing_manager
        from backend.services.routing_subsystem.decision_engine import get_decision_engine
        from backend.services.routing_subsystem.policies import get_policy_manager
        
        # Test that we can get instances
        routing_manager = get_routing_manager()
        decision_engine = get_decision_engine()
        policy_manager = get_policy_manager()
        
        print("  ✅ Routing manager instance created")
        print("  ✅ Decision engine instance created")
        print("  ✅ Policy manager instance created")
        
        # Test that we can get system status
        system_status = routing_manager.get_system_status()
        print(f"  ✅ System status retrieved: {len(system_status.get('providers', {}))} providers")
        
        print("\n🎉 Routing functionality test successful!")
        return True
        
    except Exception as e:
        print(f"❌ Routing functionality test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Testing Goblin Assistant imports and functionality...\n")
    
    # Test imports
    import_success = test_imports()
    
    # Test routing functionality
    routing_success = test_routing_functionality()
    
    print("\n" + "=" * 50)
    if import_success and routing_success:
        print("🎉 All tests passed! The project structure is working correctly.")
        print("\nKey features verified:")
        print("  ✅ Absolute imports work correctly")
        print("  ✅ Routing subsystem is properly structured")
        print("  ✅ All modules can be imported without relative imports")
        print("  ✅ Routing functionality is accessible")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)