import requests

url = 'https://thomasena-auxochromic-joziah.ngrok-free.dev/analyze'

# Test with basic content (should score ~50)
basic_content = "This is a test document for quality analysis. It has multiple sentences and some structure."

# Test with high-quality content (should score much higher)
quality_content = """# AI Development Best Practices

This comprehensive guide covers advanced AI development techniques with detailed explanations and practical examples that demonstrate real-world applications.

## Core Principles

1. Data quality is paramount for model performance and reliability
2. Model validation prevents overfitting and ensures generalization  
3. Continuous monitoring improves long-term results and catches issues early

## Implementation Example

```python
def train_model(data, epochs=100):
    model = create_neural_network()
    model.fit(data, epochs=epochs)
    return model
```

## Key Considerations

- Scalability requirements must be carefully planned from the start
- Performance metrics should be tracked throughout the development lifecycle
- Error handling strategies are essential for production deployments

This document provides excellent structure and depth for AI development practices with multiple sections, code examples, and detailed explanations."""

print("🧪 Testing Raptor Mini Analysis API")
print("=" * 50)

for test_name, content in [("Basic Content", basic_content), ("Quality Content", quality_content)]:
    print(f"\n📄 {test_name}:")
    payload = {'content': content, 'analysis_type': 'comprehensive'}
    response = requests.post(url, json=payload, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Score: {result['score']}/100")
        print(f"   Strength: {result['strength']}")
        print(f"   Weakness: {result['weakness']}")
    else:
        print(f"   ❌ Error: {response.status_code}")

