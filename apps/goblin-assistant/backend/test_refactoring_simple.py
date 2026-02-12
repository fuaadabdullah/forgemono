#!/usr/bin/env python3
"""
Simple refactoring validation script
"""

import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that all services can be imported."""
    print("Testing imports...")
    
    try:
        # Test core services
        from services.chat_validator import ChatValidator
        from services.chat_response_builder import ChatResponseBuilder
        from services.chat_error_handler import ChatErrorHandler
        from services.chat_rate_limiter import ChatRateLimiter
        from services.chat_session_manager import ChatSessionManager
        from services.chat_provider_selector import ChatProviderSelector
        from services.chat_metrics_collector import ChatMetricsCollector
        from services.chat_cache_manager import ChatCacheManager
        from services.chat_timeout_handler import ChatTimeoutHandler
        from services.chat_retry_handler import ChatRetryHandler
        from services.chat_compression_handler import ChatCompressionHandler
        from services.chat_response_formatter import ChatResponseFormatter
        from services.chat_error_formatter import ChatErrorFormatter
        from services.chat_controller_refactored import ChatController
        
        print("✓ All service imports successful")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_instantiation():
    """Test that all services can be instantiated."""
    print("Testing instantiation...")
    
    try:
        from services.chat_validator import ChatValidator
        from services.chat_response_builder import ChatResponseBuilder
        from services.chat_error_handler import ChatErrorHandler
        from services.chat_rate_limiter import ChatRateLimiter
        from services.chat_session_manager import ChatSessionManager
        from services.chat_provider_selector import ChatProviderSelector
        from services.chat_metrics_collector import ChatMetricsCollector
        from services.chat_cache_manager import ChatCacheManager
        from services.chat_timeout_handler import ChatTimeoutHandler
        from services.chat_retry_handler import ChatRetryHandler
        from services.chat_compression_handler import ChatCompressionHandler
        from services.chat_response_formatter import ChatResponseFormatter
        from services.chat_error_formatter import ChatErrorFormatter
        from services.chat_controller_refactored import ChatController
        
        # Test service instantiation
        validator = ChatValidator()
        builder = ChatResponseBuilder()
        error_handler = ChatErrorHandler()
        rate_limiter = ChatRateLimiter()
        session_manager = ChatSessionManager()
        provider_selector = ChatProviderSelector([])
        metrics_collector = ChatMetricsCollector()
        cache_manager = ChatCacheManager()
        timeout_handler = ChatTimeoutHandler()
        retry_handler = ChatRetryHandler()
        compression_handler = ChatCompressionHandler()
        response_formatter = ChatResponseFormatter()
        error_formatter = ChatErrorFormatter()
        controller = ChatController()
        
        print("✓ All services instantiated successfully")
        return True
        
    except Exception as e:
        print(f"✗ Instantiation error: {e}")
        return False

def test_controller():
    """Test that the controller has all expected services."""
    print("Testing controller integration...")
    
    try:
        from services.chat_controller_refactored import ChatController
        
        # Create controller
        controller = ChatController()
        
        # Verify controller has all expected services
        services = [
            'validator', 'rate_limiter', 'session_manager', 'provider_selector',
            'response_builder', 'error_handler', 'metrics_collector', 'cache_manager',
            'timeout_handler', 'retry_handler', 'compression_handler', 
            'response_formatter', 'error_formatter'
        ]
        
        for service in services:
            if not hasattr(controller, service):
                print(f"✗ Controller missing service: {service}")
                return False
        
        print("✓ Controller has all expected services")
        return True
        
    except Exception as e:
        print(f"✗ Controller test error: {e}")
        return False

def test_cache_functionality():
    """Test basic cache functionality."""
    print("Testing cache functionality...")
    
    try:
        from services.chat_cache_manager import ChatCacheManager
        
        # Test cache manager
        cache_manager = ChatCacheManager()
        cache_manager.set("test_key", {"test": "data"}, cache_manager.CacheType.RESPONSE)
        retrieved = cache_manager.get("test_key", cache_manager.CacheType.RESPONSE)
        
        if retrieved == {"test": "data"}:
            print("✓ Cache functionality works")
            return True
        else:
            print("✗ Cache functionality failed")
            return False
            
    except Exception as e:
        print(f"✗ Cache test error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🧪 Running Simple Refactoring Validation Tests")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_instantiation,
        test_controller,
        test_cache_functionality
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ ALL TESTS PASSED - REFACTORING SUCCESSFUL!")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())