# Claude API - Quick Start Documentation

## Official Anthropic Claude API Setup

### 1. Set Your API Key
Get your API key from the [Claude Console](https://console.anthropic.com/) and set it as an environment variable:

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

### 2. Install the SDK
Install the Anthropic Python SDK:

```bash

pip install anthropic
```

### 3. Create Your Code
Save this as `quickstart.py`:

```python
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-5",
    max_tokens=1000,
    messages=[
        {
            "role": "user",
            "content": "What should I search for to find the latest developments in renewable energy?"
        }
    ]
)
print(message.content)
```

### 4. Run Your Code
```bash

python quickstart.py
```

### Example Output:

```python
[TextBlock(text='Here are some effective search strategies for finding the latest renewable energy developments:\n\n**Search Terms to Use:**\n- "renewable energy news 2024"\n- "clean energy breakthroughs"\n- "solar/wind/battery technology advances"\n- "energy storage innovations"\n- "green hydrogen developments"\n- "renewable energy policy updates"\n\n**Reliable Sources to Check:**\n- **News & Analysis:** Reuters Energy, Bloomberg New Energy Finance, Greentech Media, Energy Storage News\n- **Industry Publications:** Renewable Energy World, PV Magazine, Wind Power Engineering\n- **Research Organizations:** International Energy Agency (IEA), National Renewable Energy Laboratory (NREL)\n- **Government Sources:** Department of Energy websites, EPA clean energy updates\n\n**Specific Topics to Explore:**\n- Perovskite and next-gen solar cells\n- Offshore wind expansion\n- Grid-scale battery storage\n- Green hydrogen production\n- Carbon capture technologies\n- Smart grid innovations\n- Energy policy changes and incentives...', type='text')]
```

## Key Points for Goblin-Assistant Integration

1. **Client Initialization**: Use `anthropic.Anthropic()` - it automatically reads from `ANTHROPIC_API_KEY` env var
2. **Model**: Latest model is `claude-sonnet-4-5` (or use `claude-3-haiku-20240307` for faster/cheaper)
3. **Messages Format**: Must use `messages` array with `role` and `content`
4. **Response**: Returns `TextBlock` objects in `message.content`

## Troubleshooting

### Common Issues:
- **401 Unauthorized**: API key is invalid or revoked
- **403 Forbidden**: Billing not set up or API access not enabled
- **429 Rate Limit**: Too many requests (check rate limits)
- **500 Server Error**: Anthropic service issue

### Billing Requirements:
- Claude API requires **credits/billing setup** even for testing
- Visit https://console.anthropic.com/settings/billing
- Add payment method or use free credits if available

### Testing Your Key:
```python

import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

try:
    client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    message = client.messages.create(
        model='claude-3-haiku-20240307',
        max_tokens=10,
        messages=[{'role': 'user', 'content': 'Hi'}]
    )
    print('✅ Claude API key is VALID')
    print(f'Response: {message.content}')
except anthropic.AuthenticationError:
    print('❌ Invalid API key - check your key at <https://console.anthropic.com/')>
except anthropic.PermissionDeniedError:
    print('❌ Permission denied - check billing setup')
except Exception as e:
    print(f'⚠️ Error: {e}')
```

---

**Source**: Anthropic Claude API Documentation
**Saved**: December 1, 2025
