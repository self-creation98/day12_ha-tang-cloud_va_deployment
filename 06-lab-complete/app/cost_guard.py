"""
Cost Guard — Bảo Vệ Budget LLM

Track chi phí hàng ngày và block khi vượt budget.
Trong production: nên lưu trong Redis/DB thay vì in-memory.
"""
import time
import logging
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

# Giá token (GPT-4o-mini)
PRICE_PER_1K_INPUT_TOKENS = 0.00015   # $0.15/1M input
PRICE_PER_1K_OUTPUT_TOKENS = 0.0006   # $0.60/1M output

_daily_cost = 0.0
_cost_reset_day = time.strftime("%Y-%m-%d")


def check_and_record_cost(input_tokens: int, output_tokens: int):
    """
    Kiểm tra và ghi nhận chi phí.
    Raise 503 nếu vượt daily budget.
    """
    global _daily_cost, _cost_reset_day

    today = time.strftime("%Y-%m-%d")
    if today != _cost_reset_day:
        _daily_cost = 0.0
        _cost_reset_day = today

    if _daily_cost >= settings.daily_budget_usd:
        raise HTTPException(503, "Daily budget exhausted. Try tomorrow.")

    cost = (input_tokens / 1000) * PRICE_PER_1K_INPUT_TOKENS + \
           (output_tokens / 1000) * PRICE_PER_1K_OUTPUT_TOKENS
    _daily_cost += cost


def get_daily_cost() -> float:
    """Return current daily cost."""
    return _daily_cost
