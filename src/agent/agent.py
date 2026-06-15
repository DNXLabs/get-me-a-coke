"""Agent definition — Strands SDK agent with AgentCore Runtime (no Payments plugin)."""

from __future__ import annotations

import logging
import os

from strands import Agent
from strands.models.bedrock import BedrockModel

from agent.config import AgentConfig  # noqa: TCH001
from agent.tools.approval import execute_purchase
from agent.tools.vending_machine import get_purchase_quote, list_products
from agent.tools.wallet import wallet_get_balance, wallet_pay
from observability.telemetry import get_sigil_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a vending machine purchasing agent with a crypto wallet.

You have these tools:
- list_products: See what's available in the vending machine
- get_purchase_quote: Get price/terms for a product
- execute_purchase: Complete the purchase (triggers a human approval gate)
- wallet_get_balance: Check your USDC balance
- wallet_pay: Make a USDC payment

PURCHASE FLOW (mandatory):
1. Use list_products to show what's available
2. Use get_purchase_quote to get the price
3. Show the quote to the user
4. Call execute_purchase — this triggers a Step Functions approval workflow that prompts the human for explicit approval. You do NOT need to ask for approval yourself; the system enforces it.
5. Report the result (approved and purchased, or rejected)

IMPORTANT:
- The approval gate is a hard system-level control. The human will be prompted automatically.
- You should still show the quote details before calling execute_purchase so the user knows what they are approving.
- Every purchase is audited with user identity, timestamp, and Step Functions execution ID.
- If the user declines, acknowledge it gracefully and offer alternatives.
"""


def get_system_prompt(config: AgentConfig) -> str:
    """Load system prompt from Bedrock Prompt Management, fallback to hardcoded."""
    import boto3

    prompt_id = os.environ.get("BEDROCK_PROMPT_ID", "")
    prompt_version = os.environ.get("BEDROCK_PROMPT_VERSION", "DRAFT")

    if not prompt_id:
        logger.info("No BEDROCK_PROMPT_ID set, using default prompt")
        return SYSTEM_PROMPT

    try:
        client = boto3.client("bedrock-agent", region_name=config.aws_region)
        resp = client.get_prompt(promptIdentifier=prompt_id, promptVersion=prompt_version)
        # Extract text from the first variant's template
        variants = resp.get("variants", [])
        if variants:
            template_config = variants[0].get("templateConfiguration", {})
            text_config = template_config.get("text", {})
            prompt_text = text_config.get("text", "")
            if prompt_text:
                logger.info("Loaded system prompt from Bedrock Prompt Management: %s (v%s)", prompt_id, prompt_version)
                return prompt_text
        logger.warning("Bedrock prompt %s has no text content, using default", prompt_id)
        return SYSTEM_PROMPT
    except Exception as e:
        logger.info("Bedrock Prompt Management unavailable (%s), using default", e)
        return SYSTEM_PROMPT


def create_agent(config: AgentConfig) -> Agent:
    """Create a Strands agent with tools.

    Args:
        config: Agent configuration loaded from .env

    Returns:
        Configured Strands Agent instance
    """
    model = BedrockModel(
        model_id=config.bedrock_model_id,
        region_name=config.aws_region,
    )

    # Configure Sigil Strands adapter for AI observability
    sigil_hooks = []
    sigil_client = get_sigil_client()
    if sigil_client is not None:
        try:
            from sigil_sdk_strands import SigilStrandsHandler, SigilStrandsHookProvider

            handler = SigilStrandsHandler(
                client=sigil_client,
                agent_name="nova",
                agent_version="0.1.0",
            )
            sigil_hooks.append(SigilStrandsHookProvider(sigil_handler=handler))
        except ImportError:
            logger.warning("sigil-sdk-strands not installed. Continuing without Sigil adapter.")
        except Exception as e:
            logger.warning("Failed to create Sigil Strands adapter: %s", e)

    return Agent(
        model=model,
        system_prompt=get_system_prompt(config),
        tools=[list_products, get_purchase_quote, execute_purchase, wallet_get_balance, wallet_pay],
        hooks=sigil_hooks or None,
    )
