"""Setup and settings endpoints for GeoStorm API."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Response

from src.config import get_settings
from src.database import get_db_connection
from src.llm.base import LLMProviderError, PromptRequest, ProviderType
from src.llm.factory import get_api_key
from src.llm.openrouter import OpenRouterProvider
from src.schemas import (
    ApiKeyStatusResponse,
    AutofillRequest,
    AutofillResponse,
    SetupStatusResponse,
    StoreApiKeyRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/setup/status")
async def get_setup_status() -> SetupStatusResponse:
    has_api_key = False

    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = 'openrouter_api_key'",
        )
        row = await cursor.fetchone()
        if row and row["value"]:
            has_api_key = True

    if not has_api_key:
        settings = get_settings()
        if settings.openrouter_api_key:
            has_api_key = True

    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT COUNT(*) as count FROM projects WHERE is_demo = 0",
        )
        count_row = await cursor.fetchone()
        project_count: int = count_row["count"] if count_row else 0

    return SetupStatusResponse(
        has_api_key=has_api_key,
        has_projects=project_count > 0,
        project_count=project_count,
    )


@router.get("/settings/api-key-status")
async def get_api_key_status() -> ApiKeyStatusResponse:
    async with get_db_connection() as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = 'openrouter_api_key'",
        )
        row = await cursor.fetchone()
        if row and row["value"]:
            return ApiKeyStatusResponse(configured=True, source="database")

    settings = get_settings()
    if settings.openrouter_api_key:
        return ApiKeyStatusResponse(configured=True, source="environment")

    return ApiKeyStatusResponse(configured=False, source=None)


@router.post("/settings/api-key")
async def store_api_key(req: StoreApiKeyRequest) -> dict[str, Any]:
    now = datetime.now(tz=UTC).isoformat()

    async with get_db_connection() as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES ('openrouter_api_key', ?, ?)",
            (req.key, now),
        )
        await db.commit()

    return {"status": "stored"}


@router.delete("/settings/api-key")
async def delete_api_key() -> Response:
    async with get_db_connection() as db:
        await db.execute("DELETE FROM settings WHERE key = 'openrouter_api_key'")
        await db.commit()

    return Response(status_code=204)


_AUTOFILL_SYSTEM_PROMPT = """\
You are a helpful assistant that generates project monitoring configuration.
Given a company name, URL, GitHub repo, or package name, return a JSON object with:
- brand_name: the official brand/product name
- brand_aliases: list of common alternative names, abbreviations, or misspellings
- description: a one-sentence description of what this brand/product does
- competitors: list of 3-5 direct competitor names
- monitoring_terms: list of 5-8 natural-language queries someone might ask an AI assistant when looking for this type of product/service

Return ONLY valid JSON, no markdown fences, no explanation.\
"""


@router.post("/setup/autofill")
async def autofill_project(req: AutofillRequest) -> AutofillResponse:
    api_key = await get_api_key(ProviderType.OPENROUTER)
    if not api_key:
        raise HTTPException(status_code=400, detail="No OpenRouter API key configured")

    provider = OpenRouterProvider(api_key)
    try:
        response = await provider.send_prompt(
            PromptRequest(
                prompt=req.input,
                model_id="google/gemini-2.0-flash-001",
                system_prompt=_AUTOFILL_SYSTEM_PROMPT,
                temperature=0.3,
            ),
        )
    except LLMProviderError as e:
        logger.warning("Autofill LLM error: %s", e)
        raise HTTPException(status_code=502, detail="AI service error") from e
    finally:
        await provider.close()

    text = response.text.strip()
    # Strip markdown code block wrappers if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [l for l in lines[1:] if l.strip() != "```"]
        text = "\n".join(lines)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logger.warning("Autofill returned invalid JSON: %s", text[:200])
        raise HTTPException(status_code=502, detail="AI returned invalid response") from e

    return AutofillResponse(
        brand_name=data.get("brand_name", req.input),
        brand_aliases=data.get("brand_aliases", []),
        description=data.get("description", ""),
        competitors=data.get("competitors", []),
        monitoring_terms=data.get("monitoring_terms", []),
    )
