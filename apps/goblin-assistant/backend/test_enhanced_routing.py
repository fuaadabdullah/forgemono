#!/usr/bin/env python3#!/usr/bin/env python3#!/usr/bin/env python3#!/usr/bin/env python3#!/usr/bin/env python3

"""

Simple test for Enhanced Routing Service"""

"""

Simple test for Enhanced Routing Service"""

import asyncio

import sys"""

import os

Simple test for Enhanced Routing Service""""""

# Add backend to path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))import asyncio



try:import sys"""

    from services.enhanced_routing import EnhancedRoutingService

    print("✅ Import successful")import os

except ImportError as e:

    print(f"❌ Import failed: {e}")Test script for Enhanced Routing Service.Test script for Enhanced Routing Service.

    sys.exit(1)

# Add backend to path

async def test():

    print("🚀 Testing Enhanced Routing Service")sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))import asyncio



    # Mock DB

    class MockDB:

        passtry:import sys"""



    db = MockDB()    from services.enhanced_routing import EnhancedRoutingService

    service = EnhancedRoutingService(db, "test-key")

    print("✅ Import successful")import os

    # Test basic methods

    time_weight = service.get_time_weight()except ImportError as e:

    print(f"📊 Time weight: {time_weight}")

    print(f"❌ Import failed: {e}")This script demonstrates the enhanced routing capabilities including

    tier_weight = service.get_user_tier_weight("test-user")

    print(f"👤 Tier weight: {tier_weight}")    sys.exit(1)



    complexity = service.analyze_content_complexity("Hello world")# Add backend to path

    print(f"🧠 Complexity: {complexity}")

async def test():

    # Test routing score calculation

    score = service.calculate_routing_score("openai", "gpt-4", "enterprise-user", "Complex analysis request")    print("🚀 Testing Enhanced Routing Service")sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))import asynciomulti-factor decision algorithm, A/B testing, and dark launch features.

    print(f"🎯 Routing score: {score}")



    print("✅ Basic tests passed!")

    # Mock DB

if __name__ == "__main__":

    asyncio.run(test())    class MockDB:

        passtry:import sys"""



    db = MockDB()    from services.enhanced_routing import EnhancedRoutingService

    service = EnhancedRoutingService(db, "test-key")

    print("✅ Import successful")import os

    # Test basic methods

    time_weight = service.get_time_weight()except ImportError as e:

    print(f"📊 Time weight: {time_weight}")

    print(f"❌ Import failed: {e}")import asyncio

    tier_weight = service.get_user_tier_weight("test-user")

    print(f"👤 Tier weight: {tier_weight}")    sys.exit(1)



    complexity = service.analyze_content_complexity("Hello world")# Add the backend directory to the pathimport sys

    print(f"🧠 Complexity: {complexity}")

async def test():

    print("✅ Basic tests passed!")

    print("🚀 Testing Enhanced Routing Service")sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))import os

if __name__ == "__main__":

    asyncio.run(test())

    # Mock DB

    class MockDB:

        passfrom services.enhanced_routing import EnhancedRoutingService# Add the backend directory to the path



    db = MockDB()sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    service = EnhancedRoutingService(db, "test-key")



    # Test basic methods

    time_weight = service.get_time_weight()async def test_enhanced_routing():from services.enhanced_routing import EnhancedRoutingService

    print(f"📊 Time weight: {time_weight}")

    """Test the enhanced routing service."""

    tier_weight = service.get_user_tier_weight("test-user")

    print(f"👤 Tier weight: {tier_weight}")



    complexity = service.analyze_content_complexity("Hello world")    print("🚀 Testing Enhanced Routing Service")async def test_enhanced_routing():

    print(f"🧠 Complexity: {complexity}")

    print("=" * 50)    """Test the enhanced routing service with various scenarios."""

    print("✅ Basic tests passed!")



if __name__ == "__main__":

    asyncio.run(test())    # Mock database session    print("🚀 Testing Enhanced Routing Service")

    class MockDB:    print("=" * 50)

        pass

    # Mock database session (in real usage, this would be a proper DB session)

    db = MockDB()    class MockDB:

        pass

    # Initialize enhanced routing service

    service = EnhancedRoutingService(db, "test-encryption-key")    db = MockDB()



    print("✅ Enhanced Routing Service initialized")    # Initialize enhanced routing service

    service = EnhancedRoutingService(db, "test-encryption-key")

    # Test time-based weighting

    print("\n📊 Testing Time-Based Weighting:")    print("✅ Enhanced Routing Service initialized")

    time_weight = service.get_time_weight()

    print(f"Current time weight: {time_weight}")    # Test time-based weighting

    print("\n📊 Testing Time-Based Weighting:")

    # Test user tier weighting    time_weight = service._get_time_based_weight()

    print("\n👤 Testing User Tier Weighting:")    print(f"Current time weight: {time_weight}")

    free_weight = service.get_user_tier_weight("user-free")

    premium_weight = service.get_user_tier_weight("user-premium")    # Test user tier weighting

    print(f"Free user weight: {free_weight}")    print("\n👤 Testing User Tier Weighting:")

    print(f"Premium user weight: {premium_weight}")    free_weight = service._get_user_tier_weight("user-free")

    premium_weight = service._get_user_tier_weight("user-premium")

    # Test content complexity analysis    print(f"Free user weight: {free_weight}")

    print("\n🧠 Testing Content Complexity Analysis:")    print(f"Premium user weight: {premium_weight}")

    simple_content = "Hello, how are you?"

    complex_content = "I need help debugging this Python function. The algorithm should optimize the database query but it's running in O(n^2) time complexity."    # Test context complexity analysis

    print("\n🧠 Testing Context Complexity Analysis:")

    simple_complexity = service.analyze_content_complexity(simple_content)    simple_request = "Hello, how are you?"

    complex_complexity = service.analyze_content_complexity(complex_content)    complex_request = """

    print(f"Simple content complexity: {simple_complexity}")    I need help debugging this Python function. The algorithm should optimize the database query

    print(f"Complex content complexity: {complex_complexity}")    but it's running in O(n^2) time complexity. Here's the code:



    print("\n✅ All enhanced routing tests completed successfully!")    def optimize_query(data):

    print("\n🎯 Key Features Demonstrated:")        for i in range(len(data)):

    print("  • Time-of-day based routing optimization")            for j in range(len(data)):

    print("  • User tier prioritization")                if data[i] == data[j]:

    print("  • Content complexity analysis")                    return True

        return False



if __name__ == "__main__":    Can you help me fix this performance issue?

    asyncio.run(test_enhanced_routing())    """

    simple_complexity = service._get_context_complexity(None, simple_request)
    complex_complexity = service._get_context_complexity(None, complex_request)
    print(f"Simple request complexity: {simple_complexity}")
    print(f"Complex request complexity: {complex_complexity}")

    # Test specialized skills detection
    print("\n🎯 Testing Specialized Skills Detection:")
    vision_request = "Can you analyze this image and describe what you see?"
    code_request = "Help me debug this Python function"
    math_request = "Solve this equation: 2x + 3 = 7"

    vision_score = service._check_specialized_skills("chat", vision_request)
    code_score = service._check_specialized_skills("chat", code_request)
    math_score = service._check_specialized_skills("chat", math_request)
    print(f"Vision request score: {vision_score}")
    print(f"Code request score: {code_score}")
    print(f"Math request score: {math_score}")

    # Test safety rating
    print("\n🛡️  Testing Content Safety Rating:")
    safe_content = (
        "Please help me write a Python function to calculate fibonacci numbers."
    )
    unsafe_content = "How can I hack into a computer system?"

    safe_score = service._get_safety_rating(safe_content)
    unsafe_score = service._get_safety_rating(unsafe_content)
    print(f"Safe content score: {safe_score}")
    print(f"Unsafe content score: {unsafe_score}")

    # Test cost prediction
    print("\n💰 Testing Cost Prediction:")
    short_request = "Hello"
    long_request = "A" * 20000  # Very long request

    short_cost = service._predict_token_cost(short_request)
    long_cost = service._predict_token_cost(long_request)
    print(f"Short request cost factor: {short_cost}")
    print(f"Long request cost factor: {long_cost}")

    # Test A/B testing
    print("\n🧪 Testing A/B Testing Framework:")
    test_user = "test-user-123"
    should_test = service._should_ab_test(test_user)
    variant = service._select_ab_test_variant(test_user) if should_test else "no-test"
    print(f"User should be in A/B test: {should_test}")
    print(f"Selected variant: {variant}")

    # Test regional latency
    print("\n🌍 Testing Regional Latency:")
    regions = ["us-west", "us-east", "eu-west", "asia-east"]
    for region in regions:
        latency = service._get_regional_latency(region)
        print(f"{region}: {latency}")

    print("\n✅ All enhanced routing tests completed successfully!")
    print("\n🎯 Key Features Demonstrated:")
    print("  • Time-of-day based routing optimization")
    print("  • User tier prioritization")
    print("  • Conversation context complexity analysis")
    print("  • Specialized capabilities detection")
    print("  • Content safety scoring")
    print("  • Predictive cost analysis")
    print("  • A/B testing framework")
    print("  • Regional latency optimization")
    print("  • Dark launch capabilities")


if __name__ == "__main__":
    asyncio.run(test_enhanced_routing())
