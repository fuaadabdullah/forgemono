"""
Chat Controller Helpers.

Utility functions for chat controller operations.
Reduces cognitive complexity by extracting common logic.
"""

from typing import Any, Tuple, List, Dict
import logging

logger = logging.getLogger(__name__)


async def gateway_check_and_prepare(
    request: Any,
    gateway_service: Any,
) -> Tuple[List[Dict], Any]:
    """
    Validate request, prepare messages, and run gateway checks.

    Args:
        request: The chat completion request
        gateway_service: The gateway service instance

    Returns:
        Tuple of (prepared_messages, gateway_result)

    Raises:
        HTTPException: If request is flagged as high-risk
    """
    from backend.services import request_validation, config_processor
    from fastapi import HTTPException

    # Validate request using the validation service
    request_validation.validate_chat_request(request)
    messages = config_processor.prepare_messages(request)

    # Run gateway checks
    gateway_result = await gateway_service.process_request(
        messages=messages,
        max_tokens=request.max_tokens,
        context=request.context,
    )

    logger.info(
        f"Gateway analysis: intent={gateway_result.intent.value}, "
        f"estimated_tokens={gateway_result.estimated_tokens}, "
        f"risk_score={gateway_result.risk_score:.2f}, "
        f"allowed={gateway_result.allowed}"
    )

    if not gateway_result.allowed:
        raise HTTPException(
            status_code=400,
            detail="Request flagged as high-risk. Please reduce token limits or simplify request.",
        )

    return messages, gateway_result
