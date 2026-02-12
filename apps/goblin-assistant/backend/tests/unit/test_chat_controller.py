import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import importlib.util

# Add backend to path
sys.path.insert(0, "/Volumes/GOBLINOS 1/ForgeMonorepo/apps/goblin-assistant/backend")

# Load the ChatController module directly without going through services.__init__
spec = importlib.util.spec_from_file_location(
    "chat_controller",
    "/Volumes/GOBLINOS 1/ForgeMonorepo/apps/goblin-assistant/backend/services/chat_controller.py",
)
chat_controller_module = importlib.util.module_from_spec(spec)

# Mock the dependencies before executing the module
with patch.dict(
    "sys.modules",
    {
        "backend.config": MagicMock(),
        "backend.errors": MagicMock(),
        "backend.services": MagicMock(),
        "services.config_processor": MagicMock(),
        "services.scaling_processor": MagicMock(),
        "services.verification_processor": MagicMock(),
        "services.response_builder": MagicMock(),
        "services.utils": MagicMock(),
        "services.request_validation": MagicMock(),
    },
):
    spec.loader.exec_module(chat_controller_module)

# Get the classes from the loaded module
ChatController = chat_controller_module.ChatController

# Import request validation separately with direct loading
spec_req = importlib.util.spec_from_file_location(
    "request_validation",
    "/Volumes/GOBLINOS 1/ForgeMonorepo/apps/goblin-assistant/backend/services/request_validation.py",
)
req_validation_module = importlib.util.module_from_spec(spec_req)
spec_req.loader.exec_module(req_validation_module)

ChatCompletionRequest = req_validation_module.ChatCompletionRequest
ChatMessage = req_validation_module.ChatMessage


@pytest.mark.asyncio
async def test_orchestrate_completion_successful_routing():
    """Test successful orchestration with routing."""
    # Create controller
    controller = ChatController()

    # Mock request
    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Hello")]
    )

    # Mock services
    routing_service = AsyncMock()
    gateway_service = AsyncMock()
    req = MagicMock()

    # Mock gateway result
    gateway_result = MagicMock()
    gateway_result.intent.value = "chat"
    gateway_result.estimated_tokens = 10
    gateway_result.risk_score = 0.1
    gateway_result.allowed = True

    gateway_service.process_request = AsyncMock(return_value=gateway_result)

    # Mock routing result
    routing_result = {
        "success": True,
        "provider": {"model": "test-model"},
        "request_id": "test-123",
        "emergency_mode": False,
    }

    # Set up routing service mock
    routing_service.route_request = AsyncMock(return_value=routing_result)

    # Mock execution result
    execution_result = {
        "success": True,
        "tokens_used": 15,
        "response_text": "Hello back!",
        "routing_result": routing_result,
        "gateway_result": gateway_result,
    }

    # Mock the backend.services module to prevent import issues
    mock_backend_services = MagicMock()
    mock_backend_services.config_processor = MagicMock()
    mock_backend_services.config_processor.build_requirements = MagicMock(
        return_value={"test": "requirements"}
    )
    mock_backend_services.config_processor.get_client_context = MagicMock(
        return_value=("127.0.0.1", "/test", "user123")
    )

    # Setup mocks
    controller._check_gateway_and_prepare = AsyncMock(
        return_value=([{"role": "user", "content": "Hello"}], gateway_result)
    )
    controller._execute_provider_request = AsyncMock(return_value=execution_result)

    # Mock the backend.services module
    with patch.dict("sys.modules", {"backend.services": mock_backend_services}):
        # Call the method
        result = await controller.orchestrate_completion(
            request, req, routing_service, gateway_service
        )

        # Assertions
        assert result["success"] is True
        assert result["tokens_used"] == 15
        assert result["routing_result"] == routing_result
        assert result["gateway_result"] == gateway_result

        # Verify calls
        controller._check_gateway_and_prepare.assert_called_once_with(
            request, gateway_service
        )
        controller._execute_provider_request.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrate_completion_routing_failure():
    """Test orchestration when routing fails."""
    controller = ChatController()

    request = ChatCompletionRequest(
        messages=[ChatMessage(role="user", content="Hello")]
    )

    routing_service = AsyncMock()
    gateway_service = AsyncMock()
    req = MagicMock()

    # Mock gateway result
    gateway_result = MagicMock()
    gateway_result.allowed = True
    gateway_result.risk_score = 0.5
    gateway_result.intent.value = "chat"
    gateway_result.estimated_tokens = 10
    gateway_service.process_request = AsyncMock(return_value=gateway_result)

    # Mock routing failure
    routing_result = {"success": False, "error": "No provider available"}

    # Mock the backend.services module
    mock_backend_services = MagicMock()
    mock_backend_services.config_processor = MagicMock()
    mock_backend_services.config_processor.build_requirements = MagicMock(
        return_value={"test": "requirements"}
    )
    mock_backend_services.config_processor.get_client_context = MagicMock(
        return_value=("127.0.0.1", "/test", "user123")
    )

    # Setup mocks
    controller._check_gateway_and_prepare = AsyncMock(
        return_value=([{"role": "user", "content": "Hello"}], gateway_result)
    )

    # Mock routing service to return failure
    routing_service.route_request = AsyncMock(return_value=routing_result)

    # Mock the backend.services module and call the method
    with patch.dict("sys.modules", {"backend.services": mock_backend_services}):
        result = await controller.orchestrate_completion(
            request, req, routing_service, gateway_service
        )

        # Assertions
        assert result["success"] is False
        assert result["error"] == "No provider available"
        assert result["routing_result"] == routing_result
        assert result["gateway_result"] == gateway_result


@pytest.mark.asyncio
async def test_execute_local_provider_with_scaling():
    """Test execution of local provider with scaling outcome."""
    controller = ChatController()

    # Mock parameters
    request = MagicMock()
    req = MagicMock()
    routing_result = {"request_id": "test-123", "provider": {"model": "test-model"}}
    messages = [{"role": "user", "content": "Hello"}]
    rag_context = None
    provider_info = {"model": "test-model"}
    selected_model = "test-model"
    temperature = 0.7
    max_tokens = 100
    top_p = 0.9
    adapter = MagicMock()
    provider_metrics_name = "test-provider"

    # Mock scaling outcome
    scaling_outcome = {
        "response_text": "Hello from scaling!",
        "scaling_result": {"scaled": True},
        "response_time_ms": 150,
    }

    # Mock the modules that get imported at runtime
    mock_scaling_processor = MagicMock()
    mock_response_builder = MagicMock()
    mock_utils = MagicMock()

    mock_scaling_processor.process_inference_scaling = AsyncMock(
        return_value=scaling_outcome
    )
    mock_response_builder.estimate_tokens = MagicMock(return_value=20)
    mock_response_builder.build_response_data = MagicMock(
        return_value={"response": "data"}
    )
    mock_utils._record_latency_metric = AsyncMock()

    # Create a mock backend.services module
    mock_backend_services = MagicMock()
    mock_backend_services.scaling_processor = mock_scaling_processor
    mock_backend_services.response_builder = mock_response_builder
    mock_backend_services.utils = mock_utils

    # Patch sys.modules to mock the entire backend.services module
    with patch.dict(
        "sys.modules",
        {
            "backend.services": mock_backend_services,
        },
    ):
        # Call the method
        result = await controller._execute_local_provider(
            request,
            req,
            routing_result,
            messages,
            rag_context,
            provider_info,
            selected_model,
            temperature,
            max_tokens,
            top_p,
            adapter,
            provider_metrics_name,
        )

        # Assertions
        assert result == {"response": "data"}
        mock_scaling_processor.process_inference_scaling.assert_called_once()
        mock_utils._record_latency_metric.assert_called_once_with(
            provider_metrics_name, selected_model, 150, 20, True
        )


@pytest.mark.asyncio
async def test_execute_cloud_provider():
    """Test execution of cloud provider."""
    controller = ChatController()

    # Mock parameters
    request = MagicMock()
    routing_result = {"request_id": "test-123", "provider": {"model": "test-model"}}
    messages = [{"role": "user", "content": "Hello"}]
    rag_context = None
    provider_info = {"model": "test-model"}
    selected_model = "test-model"
    temperature = 0.7
    max_tokens = 100
    top_p = 0.9
    adapter = MagicMock()
    provider_metrics_name = "test-provider"
    gateway_result = MagicMock()
    gateway_result.intent = MagicMock()

    # Mock simple generation
    generation_result = ("Hello from cloud!", 200, 25, True)

    # Mock the modules that get imported at runtime
    mock_verification_processor = MagicMock()
    mock_response_builder = MagicMock()

    mock_verification_processor.process_simple_generation = AsyncMock(
        return_value=generation_result
    )
    mock_response_builder.build_response_data = MagicMock(
        return_value={"response": "cloud_data"}
    )

    # Create a mock backend.services module
    mock_backend_services = MagicMock()
    mock_backend_services.verification_processor = mock_verification_processor
    mock_backend_services.response_builder = mock_response_builder

    # Patch sys.modules to mock the entire backend.services module
    with patch.dict(
        "sys.modules",
        {
            "backend.services": mock_backend_services,
        },
    ):
        # Call the method
        result = await controller._execute_cloud_provider(
            request,
            routing_result,
            messages,
            rag_context,
            provider_info,
            selected_model,
            temperature,
            max_tokens,
            top_p,
            adapter,
            provider_metrics_name,
            gateway_result,
        )

        # Assertions
        assert result == {"response": "cloud_data"}
        mock_verification_processor.process_simple_generation.assert_called_once()
        mock_response_builder.build_response_data.assert_called_once()
