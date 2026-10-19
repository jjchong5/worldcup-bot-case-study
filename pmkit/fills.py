"""Fill-price estimation against a limit order book.

A midpoint backtest is optimistic: a real order pays the spread and walks the
book. These helpers turn a captured book (levels as ``[price, size]``, best
price first) into the volume-weighted price an order of a given size would get.
"""
from __future__ import annotations


def effective_buy_price(asks: list[list[float]], notional: float) -> float | None:
    """VWAP to spend ``notional`` USDC buying shares, walking asks best-first.

    Returns None for an empty book; if depth runs out, the VWAP of what filled.
    """
    if not asks:
        return None
    spent = shares = 0.0
    for price, size in asks:
        if price <= 0:
            continue
        level_cost = price * size
        if spent + level_cost >= notional:
            take = (notional - spent) / price
            shares += take
            spent += take * price
            break
        spent += level_cost
        shares += size
    return spent / shares if shares else None


def effective_sell_price(bids: list[list[float]], shares: float) -> float | None:
    """VWAP proceeds per share selling ``shares``, walking bids best-first."""
    if not bids:
        return None
    proceeds = filled = 0.0
    for price, size in bids:
        if price <= 0:
            continue
        if filled + size >= shares:
            take = shares - filled
            proceeds += take * price
            filled += take
            break
        proceeds += size * price
        filled += size
    return proceeds / filled if filled else None
