"""Run this model in Python

> pip install azure-ai-inference
"""

import os
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import (
    AssistantMessage,
    SystemMessage,
    UserMessage,
    ToolMessage,
)
from azure.ai.inference.models import ImageContentItem, ImageUrl, TextContentItem
from azure.core.credentials import AzureKeyCredential

# To authenticate with the model you will need to generate a personal access token (PAT) in your GitHub settings.
# Create your PAT token by following instructions here: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens
client = ChatCompletionsClient(
    endpoint="https://models.github.ai/inference",
    credential=AzureKeyCredential(os.environ["GITHUB_TOKEN"]),
)

messages = [
    SystemMessage(
        content="\nPurpose: Expertly migrate React tests from Enzyme to Testing Library with surgical precision\nPersonality: Pragmatic, detail-oriented, systematic, but fast-moving\nSuccess Metric: Tests migrated per hour while maintaining 100% test pass rate 🔧 Core Directives\n1. Primary Objective\ntext\nMigrate ALL React test files from Enzyme to Testing Library patterns\nwhile maintaining or improving test quality and coverage.\n2. Success Criteria\n✅ All tests pass after migration\n✅ No Enzyme imports remain\n✅ 80%+ line coverage maintained\n✅ Tests use Testing Library best practices\n✅ Migration completed within estimated timeframe\n3. Absolute Rules\ntext\n🛑 NEVER:\n- Modify production/runtime code\n- Break existing functionality\n- Skip test validation\n- Leave Enzyme patterns in place\n\n✅ ALWAYS:\n- Verify tests pass after each migration\n- Use screen.getByRole() as primary query\n- Add userEvent for interactions\n- Test behavior, not implementation"
    ),
]

tools = []

while True:
    response = client.complete(
        messages=messages,
        model="deepseek/DeepSeek-R1",
        tools=tools,
    )

    if response.choices[0].message.tool_calls:
        print(response.choices[0].message.tool_calls)
        messages.append(response.choices[0].message)
        for tool_call in response.choices[0].message.tool_calls:
            messages.append(
                ToolMessage(
                    content=locals()[tool_call.function.name](),
                    tool_call_id=tool_call.id,
                )
            )
    else:
        print(f"[Model Response] {response.choices[0].message.content}")
        break
