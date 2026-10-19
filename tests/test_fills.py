import pytest
from pmkit.fills import effective_buy_price, effective_sell_price

ASKS = [[0.40, 100], [0.50, 100], [0.60, 100]]
BIDS = [[0.38, 100], [0.30, 100]]


def test_buy_within_top_level_pays_best_ask():
    assert effective_buy_price(ASKS, 20) == pytest.approx(0.40)


def test_buy_walks_into_second_level():
    # 40 USDC clears level 1 (100 sh); 20 more buys 40 sh at 0.50 -> 140 sh for 60
    assert effective_buy_price(ASKS, 60) == pytest.approx(60 / 140)


def test_buy_beyond_depth_returns_vwap_of_what_filled():
    assert effective_buy_price(ASKS, 1_000) == pytest.approx(150 / 300)


def test_empty_book_is_none():
    assert effective_buy_price([], 10) is None
    assert effective_sell_price([], 10) is None


def test_sell_walks_bids():
    # 100 sh at 0.38 + 50 sh at 0.30 = 53 / 150
    assert effective_sell_price(BIDS, 150) == pytest.approx(53 / 150)


def test_sell_small_order_gets_best_bid():
    assert effective_sell_price(BIDS, 10) == pytest.approx(0.38)
