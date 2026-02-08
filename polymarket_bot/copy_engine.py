"""Core copy trading engine - decides when and how to mirror leader trades."""

import logging
from dataclasses import dataclass

from polymarket_bot.config import BotConfig
from polymarket_bot.monitor import PositionDelta
from polymarket_bot.polymarket_client import PolymarketClient
from polymarket_bot.risk_manager import RiskManager

logger = logging.getLogger(__name__)


@dataclass
class CopyTradeResult:
    """Result of a copy trade attempt."""

    delta: PositionDelta
    executed: bool
    size: float
    price: float
    order_response: dict | None
    reason: str  # "OK", or reason for skipping


class CopyEngine:
    """Processes position deltas from leaders and executes copy trades."""

    def __init__(
        self,
        config: BotConfig,
        client: PolymarketClient,
        risk_manager: RiskManager,
    ):
        self.config = config
        self.client = client
        self.risk = risk_manager

    def process_delta(self, delta: PositionDelta) -> CopyTradeResult:
        """Process a single position delta and decide whether to copy it.

        Args:
            delta: The detected position change from a leader.

        Returns:
            CopyTradeResult with execution details.
        """
        if delta.action == "OPEN" or delta.action == "INCREASE":
            return self._handle_buy(delta)
        elif delta.action == "CLOSE" or delta.action == "DECREASE":
            return self._handle_sell(delta)
        else:
            return CopyTradeResult(
                delta=delta,
                executed=False,
                size=0,
                price=0,
                order_response=None,
                reason=f"Unknown action: {delta.action}",
            )

    def _handle_buy(self, delta: PositionDelta) -> CopyTradeResult:
        """Handle a leader opening or increasing a position."""
        token_id = delta.token_id

        # Get current price
        try:
            current_price = self.client.get_price(token_id, "BUY")
        except Exception as e:
            return CopyTradeResult(
                delta=delta,
                executed=False,
                size=0,
                price=0,
                order_response=None,
                reason=f"Failed to get price: {e}",
            )

        # Risk checks
        allowed, reason = self.risk.check_trade_allowed(token_id, current_price)
        if not allowed:
            logger.info("Trade blocked by risk manager: %s", reason)
            return CopyTradeResult(
                delta=delta,
                executed=False,
                size=0,
                price=current_price,
                order_response=None,
                reason=reason,
            )

        # Calculate position size
        size = self.risk.calculate_order_size(delta.size_delta, current_price)
        if size <= 0:
            return CopyTradeResult(
                delta=delta,
                executed=False,
                size=0,
                price=current_price,
                order_response=None,
                reason="Calculated size too small",
            )

        # Execute or simulate
        if self.config.dry_run:
            logger.info(
                "[DRY RUN] Would BUY %.2f shares of %s @ %.4f ($%.2f) - copying %s",
                size,
                delta.asset,
                current_price,
                size * current_price,
                delta.trader_address[:10],
            )
            self.risk.register_position(
                token_id=token_id,
                condition_id=delta.condition_id,
                asset=delta.asset,
                market_title=delta.market_title,
                side="BUY",
                size=size,
                price=current_price,
                source_trader=delta.trader_address,
            )
            return CopyTradeResult(
                delta=delta,
                executed=True,
                size=size,
                price=current_price,
                order_response={"status": "DRY_RUN"},
                reason="OK (dry run)",
            )

        # Place real order
        try:
            amount_usd = size * current_price
            resp = self.client.place_market_order(
                token_id=token_id,
                amount_usd=amount_usd,
                side="BUY",
            )
            self.risk.register_position(
                token_id=token_id,
                condition_id=delta.condition_id,
                asset=delta.asset,
                market_title=delta.market_title,
                side="BUY",
                size=size,
                price=current_price,
                source_trader=delta.trader_address,
            )
            return CopyTradeResult(
                delta=delta,
                executed=True,
                size=size,
                price=current_price,
                order_response=resp,
                reason="OK",
            )
        except Exception as e:
            logger.error("Order execution failed: %s", e)
            return CopyTradeResult(
                delta=delta,
                executed=False,
                size=size,
                price=current_price,
                order_response=None,
                reason=f"Order failed: {e}",
            )

    def _handle_sell(self, delta: PositionDelta) -> CopyTradeResult:
        """Handle a leader closing or decreasing a position."""
        token_id = delta.token_id

        # Only sell if we hold this position
        if token_id not in self.risk.positions:
            return CopyTradeResult(
                delta=delta,
                executed=False,
                size=0,
                price=0,
                order_response=None,
                reason="We don't hold this position",
            )

        our_position = self.risk.positions[token_id]

        # Get current price
        try:
            current_price = self.client.get_price(token_id, "SELL")
        except Exception as e:
            return CopyTradeResult(
                delta=delta,
                executed=False,
                size=0,
                price=0,
                order_response=None,
                reason=f"Failed to get sell price: {e}",
            )

        # Determine sell size
        if delta.action == "CLOSE":
            sell_size = our_position.size
        else:
            # Proportional decrease
            if delta.old_size > 0:
                decrease_ratio = abs(delta.size_delta) / delta.old_size
            else:
                decrease_ratio = 1.0
            sell_size = round(our_position.size * decrease_ratio, 2)
            sell_size = min(sell_size, our_position.size)

        if sell_size <= 0:
            return CopyTradeResult(
                delta=delta,
                executed=False,
                size=0,
                price=current_price,
                order_response=None,
                reason="Nothing to sell",
            )

        if self.config.dry_run:
            logger.info(
                "[DRY RUN] Would SELL %.2f shares of %s @ %.4f ($%.2f) - copying %s",
                sell_size,
                delta.asset,
                current_price,
                sell_size * current_price,
                delta.trader_address[:10],
            )
            if sell_size >= our_position.size:
                self.risk.remove_position(token_id)
            else:
                our_position.size -= sell_size
                our_position.cost_usd = our_position.size * our_position.entry_price
            return CopyTradeResult(
                delta=delta,
                executed=True,
                size=sell_size,
                price=current_price,
                order_response={"status": "DRY_RUN"},
                reason="OK (dry run)",
            )

        # Place real sell order
        try:
            amount_usd = sell_size * current_price
            resp = self.client.place_market_order(
                token_id=token_id,
                amount_usd=amount_usd,
                side="SELL",
            )
            if sell_size >= our_position.size:
                self.risk.remove_position(token_id)
            else:
                our_position.size -= sell_size
                our_position.cost_usd = our_position.size * our_position.entry_price
            return CopyTradeResult(
                delta=delta,
                executed=True,
                size=sell_size,
                price=current_price,
                order_response=resp,
                reason="OK",
            )
        except Exception as e:
            logger.error("Sell order failed: %s", e)
            return CopyTradeResult(
                delta=delta,
                executed=False,
                size=sell_size,
                price=current_price,
                order_response=None,
                reason=f"Sell order failed: {e}",
            )

    def process_stop_losses(self) -> list[CopyTradeResult]:
        """Check and execute stop losses for all positions.

        Returns:
            List of results for any stop loss trades executed.
        """
        results = []

        def price_getter(token_id: str) -> float:
            return self.client.get_price(token_id, "SELL")

        tokens_to_close = self.risk.check_stop_losses(price_getter)

        for token_id in tokens_to_close:
            pos = self.risk.positions.get(token_id)
            if not pos:
                continue

            fake_delta = PositionDelta(
                trader_address="STOP_LOSS",
                token_id=token_id,
                condition_id=pos.condition_id,
                asset=pos.asset,
                market_title=pos.market_title,
                action="CLOSE",
                old_size=pos.size,
                new_size=0,
                size_delta=-pos.size,
                current_price=0,
            )
            result = self._handle_sell(fake_delta)
            results.append(result)

        return results

    def process_deltas(self, deltas: list[PositionDelta]) -> list[CopyTradeResult]:
        """Process a batch of position deltas.

        Args:
            deltas: List of detected position changes.

        Returns:
            List of copy trade results.
        """
        results = []
        for delta in deltas:
            result = self.process_delta(delta)
            results.append(result)
            if result.executed:
                logger.info(
                    "Copied trade: %s %s %.2f @ %.4f (%s) -> %s",
                    "BUY" if delta.is_buy else "SELL",
                    delta.asset,
                    result.size,
                    result.price,
                    delta.market_title[:40],
                    result.reason,
                )
            else:
                logger.debug(
                    "Skipped trade: %s %s (%s) -> %s",
                    "BUY" if delta.is_buy else "SELL",
                    delta.asset,
                    delta.market_title[:40],
                    result.reason,
                )
        return results
