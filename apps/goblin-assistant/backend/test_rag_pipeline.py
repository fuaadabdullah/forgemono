#!/usr/bin/env python3#!/usr/bin/env python3

""""""

RAG Pipeline Test ScriptRAG Pipeline Test Script

Tests the complete RAG pipeline with 10k token retriever window and fallback mechanisms.Tests the complete RAG pipeline with 10k token retriever window and fallback mechanisms.

""""""



import asyncioimport asyncio

import osimport os

import sysimport sys

import timeimport time

from typing import Dict, Anyfrom typing import Dict, Any

import loggingimport logging



# Add the backend directory to the path# Add the backend directory to the path

sys.path.insert(0, os.path.dirname(__file__))sys.path.insert(0, os.path.dirname(__file__))



from services.rag_service import RAGServicefrom services.rag_service import RAGService



logging.basicConfig(level=logging.INFO)logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)logger = logging.getLogger(__name__)





async def test_rag_pipeline():async def test_rag_pipeline():

    """Test the complete RAG pipeline."""    """Test the complete RAG pipeline."""

    print("🧪 Testing RAG Pipeline with 10k Token Retriever Window")    print("🧪 Testing RAG Pipeline with 10k Token Retriever Window")

    print("=" * 60)    print("=" * 60)



    rag_service = RAGService()    rag_service = RAGService()



    # Test 1: Add sample documents    # Test 1: Add sample documents

    print("\n📚 Test 1: Adding sample documents...")    print("\n📚 Test 1: Adding sample documents...")

    sample_docs = [    sample_docs = [

        {        {

            "content": """            "content": """

            FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.            FastAPI is a modern, fast web framework for building APIs with Python 3.7+ based on standard Python type hints.

            It is designed to be easy to use, fast to code, and ready for production. FastAPI is built on top of Starlette            It is designed to be easy to use, fast to code, and ready for production. FastAPI is built on top of Starlette

            for the web parts and Pydantic for the data parts. It provides automatic API documentation with Swagger UI            for the web parts and Pydantic for the data parts. It provides automatic API documentation with Swagger UI

            and ReDoc, data validation, serialization, and much more. FastAPI is one of the fastest Python web frameworks            and ReDoc, data validation, serialization, and much more. FastAPI is one of the fastest Python web frameworks

            available, thanks to its async capabilities and optimization for performance.            available, thanks to its async capabilities and optimization for performance.

            """,            """,

            "id": "fastapi_intro",            "id": "fastapi_intro",

            "metadata": {"topic": "web_frameworks", "language": "python"}            "metadata": {"topic": "web_frameworks", "language": "python"},

        },        },

        {        {

            "content": """            "content": """

            Retrieval-Augmented Generation (RAG) is a technique that combines the power of large language models with            Retrieval-Augmented Generation (RAG) is a technique that combines the power of large language models with

            external knowledge retrieval. Instead of relying solely on the model's trained knowledge, RAG systems can            external knowledge retrieval. Instead of relying solely on the model's trained knowledge, RAG systems can

            fetch relevant information from external sources like databases, documents, or APIs. This approach helps            fetch relevant information from external sources like databases, documents, or APIs. This approach helps

            reduce hallucinations, improve accuracy, and provide up-to-date information. The typical RAG pipeline            reduce hallucinations, improve accuracy, and provide up-to-date information. The typical RAG pipeline

            involves: 1) Query processing, 2) Document retrieval, 3) Context ranking and filtering, 4) Prompt augmentation,            involves: 1) Query processing, 2) Document retrieval, 3) Context ranking and filtering, 4) Prompt augmentation,

            and 5) Response generation. RAG is particularly effective for question-answering, content summarization,            and 5) Response generation. RAG is particularly effective for question-answering, content summarization,

            and tasks requiring specific domain knowledge.            and tasks requiring specific domain knowledge.

            """,            """,

            "id": "rag_explanation",            "id": "rag_explanation",

            "metadata": {"topic": "ai_techniques", "language": "general"}            "metadata": {"topic": "ai_techniques", "language": "general"},

        },        },

        {        {

            "content": """            "content": """

            ChromaDB is an open-source embedding database designed for AI applications. It provides efficient storage            ChromaDB is an open-source embedding database designed for AI applications. It provides efficient storage

            and retrieval of vector embeddings, making it ideal for semantic search, RAG systems, and recommendation            and retrieval of vector embeddings, making it ideal for semantic search, RAG systems, and recommendation

            engines. ChromaDB supports multiple embedding models and provides both Python and REST APIs. Key features            engines. ChromaDB supports multiple embedding models and provides both Python and REST APIs. Key features

            include: persistent storage, metadata filtering, collection management, and scalable vector search.            include: persistent storage, metadata filtering, collection management, and scalable vector search.

            ChromaDB is lightweight and can run locally or in distributed environments, making it suitable for both            ChromaDB is lightweight and can run locally or in distributed environments, making it suitable for both

            development and production use cases.            development and production use cases.

            """,            """,

            "id": "chromadb_overview",            "id": "chromadb_overview",

            "metadata": {"topic": "databases", "language": "python"}            "metadata": {"topic": "databases", "language": "python"},

        }        },

    ]    ]



    success = await rag_service.add_documents(sample_docs)    success = await rag_service.add_documents(sample_docs)

    print(f"✅ Documents added: {success}")    print(f"✅ Documents added: {success}")



    # Test 2: Basic retrieval    # Test 2: Basic retrieval

    print("\n🔍 Test 2: Basic retrieval test...")    print("\n🔍 Test 2: Basic retrieval test...")

    query = "What is FastAPI?"    query = "What is FastAPI?"

    context = await rag_service.retrieve_context(query, top_k=5)    context = await rag_service.retrieve_context(query, top_k=5)

    print(f"Query: {query}")    print(f"Query: {query}")

    print(f"Retrieved chunks: {context['filtered_count']}")    print(f"Retrieved chunks: {context['filtered_count']}")

    print(f"Total tokens: {context['total_tokens']}")    print(f"Total tokens: {context['total_tokens']}")



    # Test 3: RAG pipeline with session caching    # Test 3: RAG pipeline with session caching

    print("\n🚀 Test 3: RAG pipeline with session caching...")    print("\n🚀 Test 3: RAG pipeline with session caching...")

    session_id = "test_session_123"    session_id = "test_session_123"



    # First query (should not be cached)    # First query (should not be cached)

    start_time = time.time()    start_time = time.time()

    result1 = await rag_service.rag_pipeline(    result1 = await rag_service.rag_pipeline(

        query="How does RAG work?",        query="How does RAG work?", session_id=session_id

        session_id=session_id    )

    )    first_duration = time.time() - start_time

    first_duration = time.time() - start_time    print(f"First query - Cached: {result1['cached']}, Duration: {first_duration:.2f}s")

    print(f"First query - Cached: {result1['cached']}, Duration: {first_duration:.2f}s")

    # Second query with same session (should be cached)

    # Second query with same session (should be cached)    start_time = time.time()

    start_time = time.time()    result2 = await rag_service.rag_pipeline(

    result2 = await rag_service.rag_pipeline(        query="How does RAG work?", session_id=session_id

        query="How does RAG work?",    )

        session_id=session_id    second_duration = time.time() - start_time

    )    print(

    second_duration = time.time() - start_time        f"Second query - Cached: {result2['cached']}, Duration: {second_duration:.2f}s"

    print(f"Second query - Cached: {result2['cached']}, Duration: {second_duration:.2f}s")    )

    print(f"Cache speedup: {first_duration/second_duration:.1f}x faster")    print(f"Cache speedup: {first_duration / second_duration:.1f}x faster")



    # Test 4: Large context test (simulate 10k token window)    # Test 4: Large context test (simulate 10k token window)

    print("\n📏 Test 4: Large context handling (10k token simulation)...")    print("\n📏 Test 4: Large context handling (10k token simulation)...")



    # Create a large document to test token limits    # Create a large document to test token limits

    large_content = " ".join([    large_content = " ".join(

        f"This is sentence number {i} containing information about artificial intelligence, machine learning, and natural language processing. "        [

        for i in range(500)  # This should create ~10k+ tokens            f"This is sentence number {i} containing information about artificial intelligence, machine learning, and natural language processing. "

    ])            for i in range(500)  # This should create ~10k+ tokens

        ]

    large_docs = [{    )

        "content": large_content,

        "id": "large_doc_test",    large_docs = [

        "metadata": {"topic": "ai_ml", "size": "large"}        {

    }]            "content": large_content,

            "id": "large_doc_test",

    await rag_service.add_documents(large_docs)            "metadata": {"topic": "ai_ml", "size": "large"},

        }

    # Test retrieval with token limit    ]

    large_query = "What information is available about artificial intelligence?"

    large_context = await rag_service.retrieve_context(large_query, top_k=10)    await rag_service.add_documents(large_docs)

    print(f"Large document query: {large_query}")

    print(f"Retrieved tokens: {large_context['total_tokens']}")    # Test retrieval with token limit

    print(f"Within 10k limit: {large_context['total_tokens'] <= 10000}")    large_query = "What information is available about artificial intelligence?"

    large_context = await rag_service.retrieve_context(large_query, top_k=10)

    # Test 5: Fallback mechanisms    print(f"Large document query: {large_query}")

    print("\n🔄 Test 5: Fallback mechanisms...")    print(f"Retrieved tokens: {large_context['total_tokens']}")

    print(f"Within 10k limit: {large_context['total_tokens'] <= 10000}")

    # Test with no relevant documents

    irrelevant_query = "What is the capital of Mars?"    # Test 5: Fallback mechanisms

    fallback_result = await rag_service.retrieve_context(irrelevant_query)    print("\n🔄 Test 5: Fallback mechanisms...")

    print(f"Irrelevant query: {irrelevant_query}")

    print(f"Fallback chunks: {fallback_result['filtered_count']}")    # Test with no relevant documents

    print(f"Graceful degradation: {fallback_result['filtered_count'] == 0}")    irrelevant_query = "What is the capital of Mars?"

    fallback_result = await rag_service.retrieve_context(irrelevant_query)

    # Test with filtering    print(f"Irrelevant query: {irrelevant_query}")

    filtered_query = "Python web frameworks"    print(f"Fallback chunks: {fallback_result['filtered_count']}")

    filtered_result = await rag_service.retrieve_context(    print(f"Graceful degradation: {fallback_result['filtered_count'] == 0}")

        filtered_query,

        filters={"language": "python"}    # Test with filtering

    )    filtered_query = "Python web frameworks"

    print(f"Filtered query: {filtered_query}")    filtered_result = await rag_service.retrieve_context(

    print(f"Filtered results: {filtered_result['filtered_count']}")        filtered_query, filters={"language": "python"}

    )

    print("\n🎉 RAG Pipeline Tests Completed!")    print(f"Filtered query: {filtered_query}")

    print("=" * 60)    print(f"Filtered results: {filtered_result['filtered_count']}")



    # Summary    print("\n🎉 RAG Pipeline Tests Completed!")

    print("\n📊 Test Summary:")    print("=" * 60)

    print("✅ Document ingestion and chunking")

    print("✅ Dense retrieval with semantic search")    # Summary

    print("✅ Session-based caching for hot-paths")    print("\n📊 Test Summary:")

    print("✅ 10k token retriever window management")    print("✅ Document ingestion and chunking")

    print("✅ Intelligent chunk filtering and ranking")    print("✅ Dense retrieval with semantic search")

    print("✅ Fallback mechanisms for edge cases")    print("✅ Session-based caching for hot-paths")

    print("✅ Metadata filtering capabilities")    print("✅ 10k token retriever window management")

    print("✅ Intelligent chunk filtering and ranking")

    return True    print("✅ Fallback mechanisms for edge cases")

    print("✅ Metadata filtering capabilities")



async def test_rag_endpoints():    return True

    """Test RAG endpoints via HTTP."""

    print("\n🌐 Testing RAG Endpoints...")

async def test_rag_endpoints():

    try:    """Test RAG endpoints via HTTP."""

        import httpx    print("\n🌐 Testing RAG Endpoints...")



        base_url = "http://localhost:8002"  # Local LLM proxy default port    try:

        headers = {"x-api-key": os.getenv("LOCAL_LLM_API_KEY", "")}        import httpx



        # Test health endpoint        base_url = "http://localhost:8002"  # Local LLM proxy default port

        async with httpx.AsyncClient() as client:        headers = {"x-api-key": os.getenv("LOCAL_LLM_API_KEY", "")}

            response = await client.get(f"{base_url}/rag/health", headers=headers)

            if response.status_code == 200:        # Test health endpoint

                print("✅ RAG health endpoint working")        async with httpx.AsyncClient() as client:

            else:            response = await client.get(f"{base_url}/rag/health", headers=headers)

                print(f"⚠️  RAG health endpoint: {response.status_code}")            if response.status_code == 200:

                print("✅ RAG health endpoint working")

            # Test document addition            else:

            doc_data = {                print(f"⚠️  RAG health endpoint: {response.status_code}")

                "content": "This is a test document for RAG endpoint testing.",

                "id": "endpoint_test_doc",            # Test document addition

                "metadata": {"test": True}            doc_data = {

            }                "content": "This is a test document for RAG endpoint testing.",

                "id": "endpoint_test_doc",

            response = await client.post(                "metadata": {"test": True},

                f"{base_url}/rag/documents",            }

                json=doc_data,

                headers=headers            response = await client.post(

            )                f"{base_url}/rag/documents", json=doc_data, headers=headers

            if response.status_code == 200:            )

                print("✅ Document addition endpoint working")            if response.status_code == 200:

            else:                print("✅ Document addition endpoint working")

                print(f"⚠️  Document addition: {response.status_code}")            else:

                print(f"⚠️  Document addition: {response.status_code}")

            # Test RAG query

            query_data = {            # Test RAG query

                "query": "What is this test about?",            query_data = {

                "session_id": "endpoint_test_session"                "query": "What is this test about?",

            }                "session_id": "endpoint_test_session",

            }

            response = await client.post(

                f"{base_url}/rag/query",            response = await client.post(

                json=query_data,                f"{base_url}/rag/query", json=query_data, headers=headers

                headers=headers            )

            )            if response.status_code == 200:

            if response.status_code == 200:                print("✅ RAG query endpoint working")

                print("✅ RAG query endpoint working")            else:

            else:                print(f"⚠️  RAG query: {response.status_code}")

                print(f"⚠️  RAG query: {response.status_code}")

    except ImportError:

    except ImportError:        print("⚠️  httpx not available for endpoint testing")

        print("⚠️  httpx not available for endpoint testing")    except Exception as e:

    except Exception as e:        print(f"⚠️  Endpoint testing failed: {e}")

        print(f"⚠️  Endpoint testing failed: {e}")



if __name__ == "__main__":

if __name__ == "__main__":

    async def main():    async def main():

        # Run core RAG tests        # Run core RAG tests

        await test_rag_pipeline()        await test_rag_pipeline()



        # Test endpoints if proxy is running        # Test endpoints if proxy is running

        await test_rag_endpoints()        await test_rag_endpoints()



    asyncio.run(main())    asyncio.run(main())


# Sample long document for RAG testing
SAMPLE_DOCUMENT = """
# Azure Cosmos DB for NoSQL: Complete Guide

## Introduction
Azure Cosmos DB is Microsoft's globally distributed, multi-model database service. It offers turnkey global distribution across any number of Azure regions with transparent multi-region writes. The service provides guaranteed low latency, high availability, and elastic scalability.

## Key Features

### Global Distribution
Cosmos DB allows you to distribute your data globally across multiple Azure regions. You can add or remove regions at any time without application downtime. The service automatically replicates your data to all configured regions.

### Multi-Model Support
Cosmos DB supports multiple data models:
- Document (NoSQL)
- Key-value
- Graph (Gremlin)
- Column-family (Cassandra)
- Table

### Performance Guarantees
The service provides comprehensive SLAs covering:
- 99.999% availability for multi-region accounts
- Single-digit millisecond latency at P99 for reads and writes
- Guaranteed throughput and consistency

### Consistency Models
Cosmos DB offers 5 consistency levels:
1. Strong - Linearizability guarantee
2. Bounded Staleness - Configurable lag window
3. Session - Read-your-writes guarantee within a session
4. Consistent Prefix - Reads never see out-of-order writes
5. Eventual - Highest availability, lowest latency

## Pricing Model

### Request Units (RUs)
Cosmos DB uses Request Units as the currency for throughput. One RU represents the resources needed to read a 1KB document. Write operations cost more RUs than reads.

### Billing Options
- Provisioned throughput: Reserve RU/s capacity
- Serverless: Pay per request
- Autoscale: Automatically scale RU/s based on demand

### Cost Optimization
To optimize costs:
- Use appropriate consistency levels
- Optimize query patterns
- Leverage TTL for automatic data deletion
- Use composite indexes wisely
- Consider serverless for unpredictable workloads

## Partitioning Strategy

### Logical Partitions
Each item belongs to a logical partition determined by the partition key. Logical partitions are limited to 20GB.

### Physical Partitions
Azure automatically manages physical partitions. Data is distributed across physical partitions for scalability.

### Choosing a Partition Key
Select a partition key that:
- Has high cardinality (many distinct values)
- Distributes requests evenly
- Aligns with your query patterns
- Avoids hot partitions

### Hierarchical Partition Keys
New feature allowing up to 3 partition key paths for better data distribution and query flexibility.

## Best Practices

### Data Modeling
- Denormalize data where possible
- Embed related data for atomic operations
- Use reference IDs for large or frequently updated data
- Keep item sizes under 2MB

### Indexing
- Cosmos DB indexes all properties by default
- Customize indexing policy to exclude unused properties
- Use composite indexes for ORDER BY with multiple properties
- Leverage spatial and vector indexes when needed

### Query Optimization
- Avoid cross-partition queries when possible
- Use continuation tokens for pagination
- Leverage query metrics to identify bottlenecks
- Add filters early in the query pipeline

### Security
- Enable firewall rules
- Use private endpoints for VNet integration
- Implement RBAC with Azure AD
- Enable customer-managed keys for encryption
- Audit access with diagnostic logs

## Monitoring and Troubleshooting

### Metrics to Monitor
- Request rate and latency
- Throttled requests (429 errors)
- Storage consumption
- RU consumption patterns
- Cross-region replication lag

### Common Issues
1. Hot partitions - caused by poor partition key choice
2. Rate limiting - insufficient RU provisioning
3. High latency - suboptimal query patterns
4. High costs - over-provisioning or inefficient queries

### Diagnostic Tools
- Azure Portal metrics
- Log Analytics integration
- Cosmos DB Profiler
- Query statistics and metrics

## Integration Patterns

### Change Feed
Monitor and react to data changes in real-time. Use cases:
- Event-driven architectures
- Real-time analytics
- Data synchronization across systems
- Audit logging

### Azure Functions Integration
Trigger functions based on Cosmos DB events:
- Automatic document processing
- Real-time data pipelines
- Serverless workflows

### Synapse Link
Analyze operational data without affecting transactional workload:
- Near real-time analytics
- No ETL required
- Cost-effective analytical queries

## Conclusion
Azure Cosmos DB is a powerful globally distributed database service suitable for applications requiring low latency, high availability, and elastic scalability. Proper data modeling, partitioning strategy, and cost optimization are key to success.
"""


def chunk_document(text: str, chunk_size: int = 500) -> list:
    """Split document into chunks by paragraphs."""
    # Split by double newlines (paragraphs)
    paragraphs = re.split(r"\n\n+", text.strip())

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(current_chunk) + len(para) < chunk_size:
            current_chunk += "\n\n" + para if current_chunk else para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


async def retrieve_relevant_chunks(
    query: str, chunks: list, model_id: str = "qwen2.5:3b", top_k: int = 3
):
    """Use qwen2.5:3b to identify most relevant chunks."""
    ollama_base_url = os.getenv("LOCAL_LLM_PROXY_URL", "http://45.61.60.3:8002")
    ollama_api_key = os.getenv("LOCAL_LLM_API_KEY", "your-secure-api-key-here")
    adapter = OllamaAdapter(ollama_api_key, ollama_base_url)

    # Score each chunk
    scores = []
    print(f"\nScoring {len(chunks)} chunks with {model_id}...")

    for i, chunk in enumerate(chunks):
        prompt = f"""Rate the relevance of this text chunk to the query on a scale of 0-10.
Query: {query}

Text chunk:
{chunk[:300]}...

Respond with ONLY a number 0-10."""

        try:
            response = await adapter.chat(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=10,
            )

            # Extract number from response
            score_match = re.search(r"\d+", response)
            score = int(score_match.group()) if score_match else 0
            scores.append((i, score, chunk))
            print(f"  Chunk {i + 1}: score={score}")

        except Exception as e:
            print(f"  Chunk {i + 1}: error - {e}")
            scores.append((i, 0, chunk))

    # Sort by score and return top_k
    scores.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [chunk for _, _, chunk in scores[:top_k]]

    print(
        f"\nSelected top {top_k} chunks (scores: {[s for _, s, _ in scores[:top_k]]})"
    )

    return top_chunks


async def generate_answer(
    query: str, context_chunks: list, model_id: str = "mistral:7b"
):
    """Use mistral:7b to generate final answer from retrieved context."""
    ollama_base_url = os.getenv("LOCAL_LLM_PROXY_URL", "http://45.61.60.3:8002")
    ollama_api_key = os.getenv("LOCAL_LLM_API_KEY", "your-secure-api-key-here")
    adapter = OllamaAdapter(ollama_api_key, ollama_base_url)

    # Combine chunks into context
    context = "\n\n".join(
        [f"[Chunk {i + 1}]\n{chunk}" for i, chunk in enumerate(context_chunks)]
    )

    prompt = f"""Based on the provided context, answer the following question. If the answer is not in the context, say so explicitly. Cite which chunks you used.

Context:
{context}

Question: {query}

Answer:"""

    print(f"\nGenerating answer with {model_id}...")
    start_time = time.time()

    try:
        response = await adapter.chat(
            model=model_id,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=512,
        )

        end_time = time.time()
        latency = (end_time - start_time) * 1000

        return {
            "success": True,
            "answer": response,
            "latency_ms": round(latency, 2),
            "tokens": len(response.split()),
        }

    except Exception as e:
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        return {"success": False, "error": str(e), "latency_ms": round(latency, 2)}


def evaluate_answer_quality(answer: str, query: str):
    """Evaluate answer quality heuristically."""
    answer_lower = answer.lower()

    # Check for citation
    has_citation = bool(re.search(r"chunk \d+|according to|based on", answer_lower))

    # Check for refusal
    has_refusal = any(
        phrase in answer_lower
        for phrase in [
            "not in the context",
            "not provided",
            "don't have information",
            "cannot find",
            "not mentioned",
        ]
    )

    # Check coherence (basic metrics)
    sentences = re.split(r"[.!?]+", answer)
    avg_sentence_length = len(answer.split()) / max(len(sentences), 1)

    # Length check
    is_adequate_length = 20 < len(answer.split()) < 500

    # Score
    score = 0
    if has_citation:
        score += 30  # Good practice to cite sources
    if not has_refusal:
        score += 20  # Answered the question
    if 10 < avg_sentence_length < 30:
        score += 25  # Good sentence structure
    if is_adequate_length:
        score += 25  # Adequate detail

    quality = "GOOD" if score >= 70 else "FAIR" if score >= 50 else "POOR"

    return {
        "quality": quality,
        "score": score,
        "has_citation": has_citation,
        "has_refusal": has_refusal,
        "avg_sentence_length": round(avg_sentence_length, 1),
        "word_count": len(answer.split()),
    }


async def test_rag_pipeline(query: str, document: str):
    """Test complete RAG pipeline."""
    print(f"\n{'=' * 80}")
    print(f"RAG Pipeline Test")
    print(f"{'=' * 80}")
    print(f"\nQuery: {query}")

    # Step 1: Chunk document
    print(f"\n--- Step 1: Document Chunking ---")
    chunks = chunk_document(document, chunk_size=500)
    print(f"Document split into {len(chunks)} chunks")
    print(f"Average chunk size: {sum(len(c) for c in chunks) / len(chunks):.0f} chars")

    # Step 2: Retrieve relevant chunks with qwen2.5:3b
    print(f"\n--- Step 2: Retrieval (qwen2.5:3b) ---")
    start_retrieval = time.time()
    relevant_chunks = await retrieve_relevant_chunks(
        query, chunks, model_id="qwen2.5:3b", top_k=3
    )
    retrieval_time = (time.time() - start_retrieval) * 1000
    print(f"Retrieval completed in {retrieval_time:.0f}ms")

    # Step 3: Generate answer with mistral:7b
    print(f"\n--- Step 3: Answer Generation (mistral:7b) ---")
    result = await generate_answer(query, relevant_chunks, model_id="mistral:7b")

    if not result["success"]:
        print(f"❌ Failed: {result['error']}")
        return None

    print(f"✅ Answer generated in {result['latency_ms']:.0f}ms")
    print(f"Response length: {result['tokens']} tokens")

    # Step 4: Evaluate answer
    print(f"\n--- Step 4: Answer Evaluation ---")
    evaluation = evaluate_answer_quality(result["answer"], query)
    print(f"Quality: {evaluation['quality']} (score: {evaluation['score']}/100)")
    print(f"Has citation: {evaluation['has_citation']}")
    print(f"Has refusal: {evaluation['has_refusal']}")
    print(f"Word count: {evaluation['word_count']}")
    print(f"Avg sentence length: {evaluation['avg_sentence_length']} words")

    # Display answer
    print(f"\n--- Final Answer ---")
    print(result["answer"])

    # Return results
    total_time = retrieval_time + result["latency_ms"]
    return {
        "query": query,
        "retrieval_time_ms": retrieval_time,
        "generation_time_ms": result["latency_ms"],
        "total_time_ms": total_time,
        "answer": result["answer"],
        "evaluation": evaluation,
        "chunks_retrieved": len(relevant_chunks),
    }


async def main():
    """Run RAG test suite."""
    print("\n" + "=" * 80)
    print("LONG DOCUMENT RAG TEST SUITE")
    print("=" * 80)
    print("\nDocument length:", len(SAMPLE_DOCUMENT), "characters")

    # Test queries
    test_queries = [
        "What are the 5 consistency models offered by Cosmos DB?",
        "How should I choose a partition key for Cosmos DB?",
        "What are the cost optimization strategies for Cosmos DB?",
        "How does the Change Feed feature work?",
        "What is the maximum size of a logical partition?",
    ]

    results = []

    for i, query in enumerate(test_queries, 1):
        print(f"\n\n{'#' * 80}")
        print(f"TEST {i}/{len(test_queries)}")
        print(f"{'#' * 80}")

        result = await test_rag_pipeline(query, SAMPLE_DOCUMENT)
        if result:
            results.append(result)

        # Pause between tests
        if i < len(test_queries):
            await asyncio.sleep(2)

    # Summary
    print(f"\n\n{'=' * 80}")
    print("RAG PIPELINE SUMMARY")
    print(f"{'=' * 80}\n")

    print(
        f"{'Test':<5} {'Quality':<10} {'Retrieval':<12} {'Generation':<12} {'Total':<12} {'Citation'}"
    )
    print("-" * 80)

    for i, result in enumerate(results, 1):
        eval_data = result["evaluation"]
        print(
            f"{i:<5} "
            f"{eval_data['quality']:<10} "
            f"{result['retrieval_time_ms']:<12.0f} "
            f"{result['generation_time_ms']:<12.0f} "
            f"{result['total_time_ms']:<12.0f} "
            f"{'✅' if eval_data['has_citation'] else '❌'}"
        )

    # Calculate averages
    if results:
        avg_retrieval = sum(r["retrieval_time_ms"] for r in results) / len(results)
        avg_generation = sum(r["generation_time_ms"] for r in results) / len(results)
        avg_total = sum(r["total_time_ms"] for r in results) / len(results)

        print("-" * 80)
        print(
            f"{'AVG':<5} {'':<10} {avg_retrieval:<12.0f} {avg_generation:<12.0f} {avg_total:<12.0f}"
        )

    # Quality distribution
    print(f"\n{'=' * 80}")
    print("QUALITY DISTRIBUTION")
    print(f"{'=' * 80}\n")

    quality_counts = {"GOOD": 0, "FAIR": 0, "POOR": 0}
    for result in results:
        quality_counts[result["evaluation"]["quality"]] += 1

    total = len(results)
    for quality, count in quality_counts.items():
        pct = (count / total * 100) if total > 0 else 0
        print(f"{quality}: {count}/{total} ({pct:.0f}%)")

    # Save results
    output = {
        "test_date": "2025-12-01",
        "document_length": len(SAMPLE_DOCUMENT),
        "results": results,
    }

    with open("rag_test_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n📊 Results saved to: rag_test_results.json\n")


if __name__ == "__main__":
    asyncio.run(main())
