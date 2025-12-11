# apps/goblin-assistant/backend/seed.py
import os
import uuid
from datetime import datetime, timedelta, timezone
import random
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Load environment variables from .env file
load_dotenv()

# Import models
from .models import Provider, Model, SearchCollection, SearchDocument, Task


def seed_database(db: Session):
    """Seed the database with initial data."""

    # Seed initial data if tables are empty
    if db.query(Provider).count() == 0:
        print("Seeding initial providers...")
        # Seed providers with API keys from environment variables
        providers_data = [
            {
                "name": "openai",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
                "base_url": "",
                "models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"],
                "enabled": True,
            },
            {
                "name": "anthropic",
                "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
                "base_url": "",
                "models": ["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                "enabled": True,
            },
            {
                "name": "gemini",
                "api_key": os.getenv("GEMINI_API_KEY", ""),
                "base_url": "",
                "models": ["gemini-pro", "gemini-pro-vision"],
                "enabled": True,
            },
            {
                "name": "groq",
                "api_key": os.getenv("GROQ_API_KEY", ""),
                "base_url": "",
                "models": ["llama2-70b-4096", "mixtral-8x7b-32768"],
                "enabled": True,
            },
            {
                "name": "deepseek",
                "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                "base_url": "",
                "models": ["deepseek-chat", "deepseek-coder"],
                "enabled": True,
            },
            {
                "name": "siliconflow",
                "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
                "base_url": "",
                "models": ["Qwen2-72B-Instruct"],
                "enabled": True,
            },
            {
                "name": "moonshot",
                "api_key": os.getenv("MOONSHOT_API_KEY", ""),
                "base_url": "",
                "models": ["moonshot-v1-8k", "moonshot-v1-32k"],
                "enabled": True,
            },
            {
                "name": "fireworks",
                "api_key": os.getenv("FIREWORKS_API_KEY", ""),
                "base_url": "",
                "models": ["accounts/fireworks/models/llama-v2-7b-chat"],
                "enabled": True,
            },
            {
                "name": "elevenlabs",
                "api_key": os.getenv("ELEVENLABS_API_KEY", ""),
                "base_url": "",
                "models": ["eleven_monolingual_v1"],
                "enabled": True,
            },
            {
                "name": "datadog",
                "api_key": os.getenv("DATADOG_API_KEY", ""),
                "base_url": "",
                "models": [],
                "enabled": True,
            },
            {
                "name": "netlify",
                "api_key": os.getenv("NETLIFY_API_KEY", ""),
                "base_url": "",
                "models": [],
                "enabled": True,
            },
        ]

        for provider_data in providers_data:
            provider = Provider(
                name=provider_data["name"],
                api_key=provider_data["api_key"],
                base_url=provider_data["base_url"],
                models=provider_data["models"],
                enabled=provider_data["enabled"],
                display_name=provider_data["name"].capitalize(), # Added display_name
                is_active=provider_data["enabled"], # Map enabled to is_active
            )
            db.add(provider)
        db.commit()
        print("Providers seeded successfully.")
    else:
        print("Updating existing providers...")
        # Update existing providers with API keys from environment variables
        providers_to_update = {
            "openai": os.getenv("OPENAI_API_KEY", ""),
            "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
            "gemini": os.getenv("GEMINI_API_KEY", ""),
            "groq": os.getenv("GROQ_API_KEY", ""),
            "deepseek": os.getenv("DEEPSEEK_API_KEY", ""),
            "siliconflow": os.getenv("SILICONFLOW_API_KEY", ""),
            "moonshot": os.getenv("MOONSHOT_API_KEY", ""),
            "fireworks": os.getenv("FIREWORKS_API_KEY", ""),
            "elevenlabs": os.getenv("ELEVENLABS_API_KEY", ""),
            "datadog": os.getenv("DATADOG_API_KEY", ""),
            "netlify": os.getenv("NETLIFY_API_KEY", ""),
        }

        for provider_name, api_key in providers_to_update.items():
            provider = db.query(Provider).filter_by(name=provider_name).first()
            if provider and api_key:
                provider.api_key = api_key
                print(f"Updated API key for {provider_name}")
            elif not provider:
                # Create missing providers
                provider_data = {
                    "name": provider_name,
                    "api_key": api_key,
                    "base_url": "",
                    "models": [],
                    "enabled": True,
                }
                if provider_name == "openai":
                    provider_data["models"] = [
                        "gpt-4",
                        "gpt-4-turbo",
                        "gpt-3.5-turbo",
                    ]
                elif provider_name == "anthropic":
                    provider_data["models"] = [
                        "claude-3-opus",
                        "claude-3-sonnet",
                        "claude-3-haiku",
                    ]
                elif provider_name == "gemini":
                    provider_data["models"] = ["gemini-pro", "gemini-pro-vision"]
                elif provider_name == "groq":
                    provider_data["models"] = [
                        "llama2-70b-4096",
                        "mixtral-8x7b-32768",
                    ]
                elif provider_name == "deepseek":
                    provider_data["models"] = ["deepseek-chat", "deepseek-coder"]
                elif provider_name == "siliconflow":
                    provider_data["models"] = ["Qwen2-72B-Instruct"]
                elif provider_name == "moonshot":
                    provider_data["models"] = ["moonshot-v1-8k", "moonshot-v1-32k"]
                elif provider_name == "fireworks":
                    provider_data["models"] = [
                        "accounts/fireworks/models/llama-v2-7b-chat"
                    ]
                elif provider_name == "elevenlabs":
                    provider_data["models"] = ["eleven_monolingual_v1"]

                # Ensure display_name and is_active are set for new providers
                provider_data["display_name"] = provider_data["name"].capitalize()
                provider_data["is_active"] = provider_data["enabled"]

                provider = Provider(**provider_data)
                db.add(provider)
                print(f"Created provider {provider_name}")
        db.commit()
        print("Providers updated successfully.")


    if db.query(Model).count() == 0:
        print("Seeding initial models...")
        # Seed models
        models_data = [
            # OpenAI models
            {
                "name": "gpt-4",
                "provider": "openai",
                "model_id": "gpt-4",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            {
                "name": "gpt-4-turbo",
                "provider": "openai",
                "model_id": "gpt-4-turbo-preview",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            {
                "name": "gpt-3.5-turbo",
                "provider": "openai",
                "model_id": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            # Anthropic models
            {
                "name": "claude-3-opus",
                "provider": "anthropic",
                "model_id": "claude-3-opus-20240229",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            {
                "name": "claude-3-sonnet",
                "provider": "anthropic",
                "model_id": "claude-3-sonnet-20240229",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            {
                "name": "claude-3-haiku",
                "provider": "anthropic",
                "model_id": "claude-3-haiku-20240307",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            # Gemini models
            {
                "name": "gemini-pro",
                "provider": "gemini",
                "model_id": "gemini-pro",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            {
                "name": "gemini-pro-vision",
                "provider": "gemini",
                "model_id": "gemini-pro-vision",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            # Groq models
            {
                "name": "llama2-70b",
                "provider": "groq",
                "model_id": "llama2-70b-4096",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            {
                "name": "mixtral-8x7b",
                "provider": "groq",
                "model_id": "mixtral-8x7b-32768",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            # DeepSeek models
            {
                "name": "deepseek-chat",
                "provider": "deepseek",
                "model_id": "deepseek-chat",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            {
                "name": "deepseek-coder",
                "provider": "deepseek",
                "model_id": "deepseek-coder",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            # SiliconFlow models
            {
                "name": "qwen2-72b",
                "provider": "siliconflow",
                "model_id": "Qwen2-72B-Instruct",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
            # Moonshot models
            {
                "name": "moonshot-v1-8k",
                "provider": "moonshot",
                "model_id": "moonshot-v1-8k",
                "temperature": 0.7,
                "max_tokens": 8192,
                "enabled": True,
            },
            {
                "name": "moonshot-v1-32k",
                "provider": "moonshot",
                "model_id": "moonshot-v1-32k",
                "temperature": 0.7,
                "max_tokens": 32768,
                "enabled": True,
            },
            # Fireworks models
            {
                "name": "llama-v2-7b",
                "provider": "fireworks",
                "model_id": "accounts/fireworks/models/llama-v2-7b-chat",
                "temperature": 0.7,
                "max_tokens": 4096,
                "enabled": True,
            },
        ]

        for model_data in models_data:
            model = Model(
                name=model_data["name"],
                provider=model_data["provider"],
                model_id=model_data["model_id"],
                temperature=model_data["temperature"],
                max_tokens=model_data["max_tokens"],
                enabled=model_data["enabled"],
            )
            db.add(model)
        db.commit()
        print("Models seeded successfully.")


    if db.query(SearchDocument).count() == 0:
        print("Seeding initial search documents...")
        # Seed search documents
        search_docs = [
            {
                "id": "doc_1",
                "collection": "documents",
                "document": "This is a comprehensive guide to building modern web applications using React and TypeScript. It covers component architecture, state management, and best practices for scalable applications.",
                "metadata": {
                    "source": "docs",
                    "type": "guide",
                    "tags": ["react", "typescript", "web-development"],
                },
            },
            {
                "id": "doc_2",
                "collection": "documents",
                "document": "API design principles for microservices architecture. Learn about RESTful APIs, GraphQL, and how to design scalable backend services.",
                "metadata": {
                    "source": "docs",
                    "type": "tutorial",
                    "tags": ["api", "microservices", "backend"],
                },
            },
            {
                "id": "doc_3",
                "collection": "documents",
                "document": "Machine learning fundamentals including neural networks, deep learning, and practical applications in computer vision and natural language processing.",
                "metadata": {
                    "source": "docs",
                    "type": "reference",
                    "tags": ["ml", "ai", "neural-networks"],
                },
            },
            {
                "id": "code_1",
                "collection": "code",
                "document": "function calculateTotal(items) { return items.reduce((sum, item) => sum + item.price * item.quantity, 0); }",
                "metadata": {
                    "source": "code",
                    "language": "javascript",
                    "tags": ["javascript", "array-methods"],
                },
            },
            {
                "id": "code_2",
                "collection": "code",
                "document": "class UserService { constructor(db) { this.db = db; } async findById(id) { return this.db.users.find(u => u.id === id); } }",
                "metadata": {
                    "source": "code",
                    "language": "javascript",
                    "tags": ["javascript", "class", "service"],
                },
            },
            {
                "id": "kb_1",
                "collection": "knowledge",
                "document": "DevOps best practices include continuous integration, automated testing, infrastructure as code, and monitoring. These practices help teams deliver software faster and more reliably.",
                "metadata": {
                    "source": "knowledge",
                    "category": "devops",
                    "tags": ["devops", "ci-cd", "automation"],
                },
            },
            {
                "id": "kb_2",
                "collection": "knowledge",
                "document": "Security principles: defense in depth, least privilege, fail-safe defaults, and regular security audits are essential for protecting applications and data.",
                "metadata": {
                    "source": "knowledge",
                    "category": "security",
                    "tags": ["security", "best-practices", "auditing"],
                },
            },
        ]

        for doc_data in search_docs:
            collection_name = doc_data["collection"]
            collection_obj = db.query(SearchCollection).filter_by(name=collection_name).first()
            if not collection_obj:
                collection_obj = SearchCollection(name=collection_name)
                db.add(collection_obj)
                db.flush() # Flush to get the ID for the new collection

            doc = SearchDocument(
                document_id=doc_data["id"],
                collection_id=collection_obj.id,
                document=doc_data["document"],
                metadata=doc_data["metadata"],
            )
            db.add(doc)
        db.commit()
        print("Search documents seeded successfully.")


    if db.query(Task).count() == 0:
        print("Seeding initial tasks...")
        # Seed some mock tasks
        mock_tasks = [
            {
                "id": "task_001",
                "user_id": "demo_user",
                "goblin": "docs-writer",
                "task": "Write documentation for the new API endpoints",
                "status": "completed",
                "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
                "updated_at": datetime.now(timezone.utc)
                - timedelta(hours=1, minutes=45),
                "result": "Successfully generated comprehensive API documentation with examples and usage patterns.",
                "cost": 0.0345,
                "tokens": 456,
                "duration_ms": 2340,
            },
            {
                "id": "task_002",
                "user_id": "demo_user",
                "goblin": "code-writer",
                "task": "Implement user authentication middleware",
                "status": "completed",
                "created_at": datetime.now(timezone.utc) - timedelta(hours=4),
                "updated_at": datetime.now(timezone.utc)
                - timedelta(hours=3, minutes=30),
                "result": "Created JWT-based authentication middleware with role-based access control and secure token handling.",
                "cost": 0.0678,
                "tokens": 789,
                "duration_ms": 4120,
            },
            {
                "id": "task_003",
                "user_id": "demo_user",
                "goblin": "docs-writer",
                "task": "Create deployment guide for the application",
                "status": "completed",
                "created_at": datetime.now(timezone.utc) - timedelta(hours=6),
                "updated_at": datetime.now(timezone.utc)
                - timedelta(hours=5, minutes=15),
                "result": "Compiled detailed deployment guide covering Docker, Kubernetes, and cloud platform configurations.",
                "cost": 0.0234,
                "tokens": 345,
                "duration_ms": 1890,
            },
        ]

        for task_data in mock_tasks:
            task = Task(
                id=task_data["id"],
                user_id=task_data["user_id"],
                goblin=task_data["goblin"],
                task=task_data["task"],
                status=task_data["status"],
                created_at=task_data["created_at"],
                updated_at=task_data["updated_at"],
                result=task_data["result"],
                cost=task_data["cost"],
                tokens=task_data["tokens"],
                duration_ms=task_data["duration_ms"],
            )
            db.add(task)
        db.commit()
        print("Tasks seeded successfully.")
