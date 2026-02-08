"""Wrapper around the Polymarket CLOB client for order execution and market data."""

import logging
from typing import Optional

from py_clob_client.client import ClobClient
from py_clob_client.clob_types import (
    BookParams,
    MarketOrderArgs,
    OpenOrderParams,
    OrderArgs,
    OrderType,
)
from py_clob_client.constants import BUY, SELL

from polymarket_bot.config import PolymarketConfig

logger = logging.getLogger(__name__)


class PolymarketClient:
    """High-level wrapper for Polymarket CLOB trading operations."""

    def __init__(self, config: PolymarketConfig):
        self.config = config
        self._client: Optional[ClobClient] = None

    def connect(self):
        """Initialize and authenticate the CLOB client."""
        self._client = ClobClient(
            host=self.config.clob_host,
            key=self.config.private_key,
            chain_id=self.config.chain_id,
            signature_type=self.config.signature_type,
            funder=self.config.funder_address,
        )
        # Derive or load API credentials
        self._client.set_api_creds(self._client.create_or_derive_api_creds())
        logger.info("Connected to Polymarket CLOB API")

    @property
    def client(self) -> ClobClient:
        if self._client is None:
            raise RuntimeError("Client not connected. Call connect() first.")
        return self._client

    # ── Market Data ──────────────────────────────────────────────

    def get_markets(self):
        """Fetch all simplified markets."""
        return self.client.get_simplified_markets()

    def get_market(self, condition_id: str):
        """Fetch a single market by condition ID."""
        return self.client.get_market(condition_id)

    def get_orderbook(self, token_id: str) -> dict:
        """Get orderbook for a token."""
        return self.client.get_order_book(token_id)

    def get_orderbooks(self, token_ids: list[str]) -> list[dict]:
        """Get orderbooks for multiple tokens."""
        params = [BookParams(token_id=tid) for tid in token_ids]
        return self.client.get_order_books(params)

    def get_midpoint(self, token_id: str) -> float:
        """Get the midpoint price for a token."""
        mid = self.client.get_midpoint(token_id)
        return float(mid)

    def get_price(self, token_id: str, side: str = "BUY") -> float:
        """Get the current price for a token on a given side."""
        price = self.client.get_price(token_id, side)
        return float(price)

    def get_last_trade_price(self, token_id: str) -> float:
        """Get the last trade price for a token."""
        price = self.client.get_last_trade_price(token_id)
        return float(price)

    # ── Order Management ─────────────────────────────────────────

    def place_limit_order(
        self,
        token_id: str,
        price: float,
        size: float,
        side: str = "BUY",
    ) -> dict:
        """Place a GTC limit order.

        Args:
            token_id: The market token to trade.
            price: Limit price (0.01 - 0.99).
            size: Number of shares.
            side: BUY or SELL.

        Returns:
            Order response from the CLOB.
        """
        order_side = BUY if side.upper() == "BUY" else SELL
        order_args = OrderArgs(
            token_id=token_id,
            price=price,
            size=size,
            side=order_side,
        )
        signed_order = self.client.create_order(order_args)
        resp = self.client.post_order(signed_order, OrderType.GTC)
        logger.info(
            "Limit order placed: %s %.2f @ %.4f on %s -> %s",
            side,
            size,
            price,
            token_id[:16],
            resp,
        )
        return resp

    def place_market_order(
        self,
        token_id: str,
        amount_usd: float,
        side: str = "BUY",
    ) -> dict:
        """Place a Fill-or-Kill market order.

        Args:
            token_id: The market token to trade.
            amount_usd: Dollar amount to spend.
            side: BUY or SELL.

        Returns:
            Order response from the CLOB.
        """
        order_side = BUY if side.upper() == "BUY" else SELL
        mo = MarketOrderArgs(
            token_id=token_id,
            amount=amount_usd,
            side=order_side,
        )
        signed_order = self.client.create_market_order(mo)
        resp = self.client.post_order(signed_order, OrderType.FOK)
        logger.info(
            "Market order placed: %s $%.2f on %s -> %s",
            side,
            amount_usd,
            token_id[:16],
            resp,
        )
        return resp

    def cancel_order(self, order_id: str) -> dict:
        """Cancel a specific order."""
        resp = self.client.cancel(order_id)
        logger.info("Order cancelled: %s -> %s", order_id, resp)
        return resp

    def cancel_all_orders(self) -> dict:
        """Cancel all open orders."""
        resp = self.client.cancel_all()
        logger.info("All orders cancelled: %s", resp)
        return resp

    def get_open_orders(self) -> list[dict]:
        """Get all open orders."""
        return self.client.get_orders(OpenOrderParams())

    def get_trades(self) -> list[dict]:
        """Get trade history."""
        return self.client.get_trades()
