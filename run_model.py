import os
from openai import OpenAI

# Authenticate with GitHub Models using PAT
client = OpenAI(
    base_url="https://models.github.ai/inference",
    api_key=os.environ["GITHUB_TOKEN"],
)

messages = [
    {
        "role": "system",
        "content": """
Purpose: Expertly migrate React tests from Enzyme to Testing Library with surgical precision
Personality: Pragmatic, detail-oriented, systematic, but fast-moving
Success Metric: Tests migrated per hour while maintaining 100% test pass rate 🔧 
Core Directives
1. Primary Objective
Migrate ALL React test files from Enzyme to Testing Library patterns
while maintaining or improving test quality and coverage.
2. Success Criteria
✅ All tests pass after migration
✅ No Enzyme imports remain
✅ 80%+ line coverage maintained
✅ Tests use Testing Library best practices
✅ Migration completed within estimated timeframe
3. Absolute Rules
🛑 NEVER:
- Modify production/runtime code
- Break existing functionality
- Skip test validation
- Leave Enzyme patterns in place

✅ ALWAYS:
- Verify tests pass after each migration
- Use screen.getByRole() as primary query
- Add userEvent for interactions
- Test behavior, not implementation
""",
    }
]

tools = []

while True:
    response = client.chat.completions.create(
        model="deepseek/DeepSeek-R1",
        messages=messages,
        tools=tools,
    )

    if response.choices[0].message.tool_calls:
        print(response.choices[0].message.tool_calls)
        messages.append(response.choices[0].message)
        for tool_call in response.choices[0].message.tool_calls:
            # Note: No tools defined, so this won't execute
            # In a real scenario, you'd call the function here
            messages.append(
                {
                    "role": "tool",
                    "content": "Tool executed",  # Placeholder
                    "tool_call_id": tool_call.id,
                }
            )
    else:
        print(f"[Model Response] {response.choices[0].message.content}")
        break
