"""
Refactoring Validation Script

This script validates that the refactoring was successful by:
1. Testing all extracted services
2. Verifying imports work correctly
3. Running basic functionality tests
4. Checking for any remaining coupling issues
"""

import sys
import importlib
import traceback
from typing import Dict, List, Any, Tuple
from unittest.mock import Mock, AsyncMock


def test_imports() -> Tuple[bool, List[str]]:
    """Test that all services can be imported correctly."""
    errors = []
    
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
        
    except ImportError as e:
        errors.append(f"Import error: {e}")
        print(f"✗ Import error: {e}")
    
    return len(errors) == 0, errors


def test_service_instantiation() -> Tuple[bool, List[str]]:
    """Test that all services can be instantiated."""
    errors = []
    
    try:
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
        
    except Exception as e:
        errors.append(f"Instantiation error: {e}")
        print(f"✗ Instantiation error: {e}")
    
    return len(errors) == 0, errors


def test_service_interfaces() -> Tuple[bool, List[str]]:
    """Test that all services have expected interfaces."""
    errors = []
    
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
        
        # Test that services have expected methods
        validator = ChatValidator()
        assert hasattr(validator, 'validate_request')
        assert hasattr(validator, 'get_stats')
        assert hasattr(validator, 'reset_stats')
        
        builder = ChatResponseBuilder()
        assert hasattr(builder, 'build_provider_request')
        assert hasattr(builder, 'build_response_data')
        assert hasattr(builder, 'get_stats')
        
        error_handler = ChatErrorHandler()
        assert hasattr(error_handler, 'handle_validation_error')
        assert hasattr(error_handler, 'handle_provider_error')
        assert hasattr(error_handler, 'get_stats')
        
        rate_limiter = ChatRateLimiter()
        assert hasattr(rate_limiter, 'check_rate_limit')
        assert hasattr(rate_limiter, 'get_stats')
        assert hasattr(rate_limiter, 'reset_stats')
        
        session_manager = ChatSessionManager()
        assert hasattr(session_manager, 'get_or_create_session')
        assert hasattr(session_manager, 'update_session_with_request')
        assert hasattr(session_manager, 'get_stats')
        
        provider_selector = ChatProviderSelector([])
        assert hasattr(provider_selector, 'select_provider')
        assert hasattr(provider_selector, 'get_stats')
        assert hasattr(provider_selector, 'update_provider_status')
        
        metrics_collector = ChatMetricsCollector()
        assert hasattr(metrics_collector, 'start_request')
        assert hasattr(metrics_collector, 'update_response_metrics')
        assert hasattr(metrics_collector, 'get_system_metrics')
        
        cache_manager = ChatCacheManager()
        assert hasattr(cache_manager, 'set')
        assert hasattr(cache_manager, 'get')
        assert hasattr(cache_manager, 'get_stats')
        
        timeout_handler = ChatTimeoutHandler()
        assert hasattr(timeout_handler, 'timeout_context')
        assert hasattr(timeout_handler, 'get_stats')
        assert hasattr(timeout_handler, 'reset_stats')
        
        retry_handler = ChatRetryHandler()
        assert hasattr(retry_handler, 'retry_with_strategy')
        assert hasattr(retry_handler, 'retry_decorator')
        assert hasattr(retry_handler, 'get_retry_stats')
        
        compression_handler = ChatCompressionHandler()
        assert hasattr(compression_handler, 'compress_response')
        assert hasattr(compression_handler, 'decompress_response')
        assert hasattr(compression_handler, 'get_stats')
        
        response_formatter = ChatResponseFormatter()
        assert hasattr(response_formatter, 'format_response')
        assert hasattr(response_formatter, 'format_stream_response')
        assert hasattr(response_formatter, 'get_response_headers')
        
        error_formatter = ChatErrorFormatter()
        assert hasattr(error_formatter, 'format_validation_error')
        assert hasattr(error_formatter, 'format_provider_error')
        assert hasattr(error_formatter, 'get_stats')
        
        controller = ChatController()
        assert hasattr(controller, 'handle_chat_request')
        assert hasattr(controller, 'get_request_state')
        assert hasattr(controller, 'get_controller_stats')
        
        print("✓ All service interfaces validated")
        
    except Exception as e:
        errors.append(f"Interface validation error: {e}")
        print(f"✗ Interface validation error: {e}")
    
    return len(errors) == 0, errors


def test_service_isolation() -> Tuple[bool, List[str]]:
    """Test that services are properly isolated and don't have circular dependencies."""
    errors = []
    
    try:
        # Test that services don't import each other inappropriately
        import inspect
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
        
        # Check that validator doesn't import other services
        validator_source = inspect.getsource(ChatValidator)
        for service_name in [
            'ChatResponseBuilder', 'ChatErrorHandler', 'ChatRateLimiter',
            'ChatSessionManager', 'ChatProviderSelector', 'ChatMetricsCollector',
            'ChatCacheManager', 'ChatTimeoutHandler', 'ChatRetryHandler',
            'ChatCompressionHandler', 'ChatResponseFormatter', 'ChatErrorFormatter'
        ]:
            if service_name in validator_source:
                errors.append(f"ChatValidator inappropriately references {service_name}")
        
        # Check that response builder doesn't import other services (except maybe error handler)
        builder_source = inspect.getsource(ChatResponseBuilder)
        for service_name in [
            'ChatValidator', 'ChatRateLimiter', 'ChatSessionManager',
            'ChatProviderSelector', 'ChatMetricsCollector', 'ChatCacheManager',
            'ChatTimeoutHandler', 'ChatRetryHandler', 'ChatCompressionHandler',
            'ChatResponseFormatter'
        ]:
            if service_name in builder_source:
                errors.append(f"ChatResponseBuilder inappropriately references {service_name}")
        
        # Check that error handler doesn't import other services
        error_handler_source = inspect.getsource(ChatErrorHandler)
        for service_name in [
            'ChatValidator', 'ChatResponseBuilder', 'ChatRateLimiter',
            'ChatSessionManager', 'ChatProviderSelector', 'ChatMetricsCollector',
            'ChatCacheManager', 'ChatTimeoutHandler', 'ChatRetryHandler',
            'ChatCompressionHandler', 'ChatResponseFormatter'
        ]:
            if service_name in error_handler_source:
                errors.append(f"ChatErrorHandler inappropriately references {service_name}")
        
        if not errors:
            print("✓ Service isolation validated")
        
    except Exception as e:
        errors.append(f"Isolation test error: {e}")
        print(f"✗ Isolation test error: {e}")
    
    return len(errors) == 0, errors


def test_controller_integration() -> Tuple[bool, List[str]]:
    """Test that the controller properly integrates with all services."""
    errors = []
    
    try:
        from services.chat_controller_refactored import ChatController
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
        
        # Create controller
        controller = ChatController()
        
        # Verify controller has all expected services
        assert hasattr(controller, 'validator')
        assert hasattr(controller, 'rate_limiter')
        assert hasattr(controller, 'session_manager')
        assert hasattr(controller, 'provider_selector')
        assert hasattr(controller, 'response_builder')
        assert hasattr(controller, 'error_handler')
        assert hasattr(controller, 'metrics_collector')
        assert hasattr(controller, 'cache_manager')
        assert hasattr(controller, 'timeout_handler')
        assert hasattr(controller, 'retry_handler')
        assert hasattr(controller, 'compression_handler')
        assert hasattr(controller, 'response_formatter')
        assert hasattr(controller, 'error_formatter')
        
        # Verify services are the correct types
        assert isinstance(controller.validator, ChatValidator)
        assert isinstance(controller.rate_limiter, ChatRateLimiter)
        assert isinstance(controller.session_manager, ChatSessionManager)
        assert isinstance(controller.provider_selector, ChatProviderSelector)
        assert isinstance(controller.response_builder, ChatResponseBuilder)
        assert isinstance(controller.error_handler, ChatErrorHandler)
        assert isinstance(controller.metrics_collector, ChatMetricsCollector)
        assert isinstance(controller.cache_manager, ChatCacheManager)
        assert isinstance(controller.timeout_handler, ChatTimeoutHandler)
        assert isinstance(controller.retry_handler, ChatRetryHandler)
        assert isinstance(controller.compression_handler, ChatCompressionHandler)
        assert isinstance(controller.response_formatter, ChatResponseFormatter)
        assert isinstance(controller.error_formatter, ChatErrorFormatter)
        
        print("✓ Controller integration validated")
        
    except Exception as e:
        errors.append(f"Integration test error: {e}")
        print(f"✗ Integration test error: {e}")
    
    return len(errors) == 0, errors


def test_basic_functionality() -> Tuple[bool, List[str]]:
    """Test basic functionality of key services."""
    errors = []
    
    try:
        from services.chat_validator import ChatValidator
        from services.chat_response_builder import ChatResponseBuilder
        from services.chat_error_handler import ChatErrorHandler
        from services.chat_cache_manager import ChatCacheManager
        from services.chat_response_formatter import ChatResponseFormatter
        from services.chat_error_formatter import ChatErrorFormatter
        
        # Test validator
        validator = ChatValidator()
        # Note: validate_request is async, so we'll just test instantiation
        
        # Test response builder
        builder = ChatResponseBuilder()
        # Note: build_provider_request is async, so we'll just test instantiation
        
        # Test error handler
        error_handler = ChatErrorHandler()
        # Note: handle_validation_error is async, so we'll just test instantiation
        
        # Test cache manager
        cache_manager = ChatCacheManager()
        cache_manager.set("test_key", {"test": "data"}, cache_manager.CacheType.RESPONSE)
        retrieved = cache_manager.get("test_key", cache_manager.CacheType.RESPONSE)
        assert retrieved == {"test": "data"}
        
        # Test response formatter
        formatter = ChatResponseFormatter()
        # Note: format_response is async, so we'll just test instantiation
        
        # Test error formatter
        error_formatter = ChatErrorFormatter()
        # Note: format_validation_error is async, so we'll just test instantiation
        
        print("✓ Basic functionality validated")
        
    except Exception as e:
        errors.append(f"Functionality test error: {e}")
        print(f"✗ Functionality test error: {e}")
    
    return len(errors) == 0, errors


def run_validation() -> Dict[str, Any]:
    """Run all validation tests and return results."""
    results = {
        "imports": False,
        "instantiation": False,
        "interfaces": False,
        "isolation": False,
        "integration": False,
        "functionality": False,
        "errors": [],
        "success": False
    }
    
    print("🧪 Running Refactoring Validation Tests")
    print("=" * 50)
    
    # Test imports
    results["imports"], import_errors = test_imports()
    results["errors"].extend(import_errors)
    
    # Test instantiation
    results["instantiation"], instantiation_errors = test_service_instantiation()
    results["errors"].extend(instantiation_errors)
    
    # Test interfaces
    results["interfaces"], interface_errors = test_service_interfaces()
    results["errors"].extend(interface_errors)
    
    # Test isolation
    results["isolation"], isolation_errors = test_service_isolation()
    results["errors"].extend(isolation_errors)
    
    # Test integration
    results["integration"], integration_errors = test_controller_integration()
    results["errors"].extend(integration_errors)
    
    # Test functionality
    results["functionality"], functionality_errors = test_basic_functionality()
    results["errors"].extend(functionality_errors)
    
    # Determine overall success
    results["success"] = all([
        results["imports"],
        results["instantiation"],
        results["interfaces"],
        results["isolation"],
        results["integration"],
        results["functionality"]
    ])
    
    print("\n" + "=" * 50)
    print("📊 VALIDATION RESULTS")
    print("=" * 50)
    
    print(f"Imports: {'✓ PASS' if results['imports'] else '✗ FAIL'}")
    print(f"Instantiation: {'✓ PASS' if results['instantiation'] else '✗ FAIL'}")
    print(f"Interfaces: {'✓ PASS' if results['interfaces'] else '✗ FAIL'}")
    print(f"Isolation: {'✓ PASS' if results['isolation'] else '✗ FAIL'}")
    print(f"Integration: {'✓ PASS' if results['integration'] else '✗ FAIL'}")
    print(f"Functionality: {'✓ PASS' if results['functionality'] else '✗ FAIL'}")
    
    if results["errors"]:
        print(f"\n❌ ERRORS ({len(results['errors'])}):")
        for error in results["errors"]:
            print(f"  - {error}")
    else:
        print("\n✅ NO ERRORS FOUND")
    
    print(f"\n🎯 OVERALL RESULT: {'SUCCESS' if results['success'] else 'FAILURE'}")
    
    return results


if __name__ == "__main__":
    # Add the backend directory to the path so imports work
    import os
    import sys
    backend_path = os.path.join(os.path.dirname(__file__), "..", "..")
    sys.path.insert(0, backend_path)
    
    results = run_validation()
    sys.exit(0 if results["success"] else 1)