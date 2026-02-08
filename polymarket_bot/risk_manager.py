"""Risk management for the copy trading bot."""

import logging
from dataclasses import dataclass, field

from polymarket_bot.config import RiskConfig

logger = logging.getLogger(__name__)


@dataclass
class ActivePosition:
    """Tracks a position the bot has opened."""

    token_id: str
    condition_id: str
    asset: str
    market_title: str
    side: str
    size: float  # shares
    entry_price: float
    cost_usd: float  # total USD spent
    source_trader: str  # which leader triggered this


class RiskManager:
    """Enforces risk limits and position sizing for copy trades."""

    def __init__(self, config: RiskConfig):
        self.config = config
        self.positions: dict[str, ActivePosition] = {}  # token_id -> ActivePosition

    @property
    def total_exposure(self) -> float:
        """Total USD exposure across all open positions."""
        return sum(p.cost_usd for p in self.positions.values())

    @property
    def position_count(self) -> int:
        """Number of open positions."""
        return len(self.positions)

    def calculate_order_size(
        self,
        leader_size: float,
        current_price: float,
    ) -> float:
        """Calculate the size of a copy trade respecting risk limits.

        Args:
            leader_size: The leader's position size in shares.
            current_price: Current market price for the token.

        Returns:
            Number of shares to buy (0 if trade should be skipped).
        """
        # Scale down by allocation percentage
        raw_size = leader_size * self.config.allocation_pct
        raw_cost = raw_size * current_price

        # Cap by max position size
        if raw_cost > self.config.max_position_size_usd:
            raw_size = self.config.max_position_size_usd / current_price
            raw_cost = self.config.max_position_size_usd

        # Cap by remaining exposure budget
        remaining_budget = self.config.max_total_exposure_usd - self.total_exposure
        if remaining_budget <= 0:
            logger.warning(
                "Max total exposure reached ($%.2f). Skipping trade.",
                self.config.max_total_exposure_usd,
            )
            return 0.0

        if raw_cost > remaining_budget:
            raw_size = remaining_budget / current_price
            raw_cost = remaining_budget

        # Minimum viable trade (at least $1)
        if raw_cost < 1.0:
            logger.debug("Trade too small ($%.2f). Skipping.", raw_cost)
            return 0.0

        return round(raw_size, 2)

    def check_trade_allowed(
        self,
        token_id: str,
        price: float,
    ) -> tuple[bool, str]:
        """Check if a trade passes all risk checks.

        Args:
            token_id: The token to trade.
            price: The current price.

        Returns:
            (allowed, reason) tuple.
        """
        # Price bounds check
        if price < self.config.min_price:
            return False, f"Price {price:.4f} below min {self.config.min_price}"
        if price > self.config.max_price:
            return False, f"Price {price:.4f} above max {self.config.max_price}"

        # Position count check
        if token_id not in self.positions and self.position_count >= self.config.max_positions:
            return False, f"Max positions ({self.config.max_positions}) reached"

        # Exposure check
        if self.total_exposure >= self.config.max_total_exposure_usd:
            return False, f"Max exposure (${self.config.max_total_exposure_usd}) reached"

        # Already have this position?
        if token_id in self.positions:
            existing = self.positions[token_id]
            new_exposure = existing.cost_usd + self.config.max_position_size_usd
            if new_exposure > self.config.max_position_size_usd * 2:
                return False, f"Would exceed 2x max position size on {token_id[:16]}"

        return True, "OK"

    def register_position(
        self,
        token_id: str,
        condition_id: str,
        asset: str,
        market_title: str,
        side: str,
        size: float,
        price: float,
        source_trader: str,
    ):
        """Record a newly opened or increased position."""
        cost = size * price
        if token_id in self.positions:
            existing = self.positions[token_id]
            total_size = existing.size + size
            total_cost = existing.cost_usd + cost
            existing.size = total_size
            existing.entry_price = total_cost / total_size if total_size > 0 else 0
            existing.cost_usd = total_cost
            logger.info(
                "Position updated: %s now %.2f shares ($%.2f) on %s",
                asset,
                total_size,
                total_cost,
                market_title[:40],
            )
        else:
            self.positions[token_id] = ActivePosition(
                token_id=token_id,
                condition_id=condition_id,
                asset=asset,
                market_title=market_title,
                side=side,
                size=size,
                entry_price=price,
                cost_usd=cost,
                source_trader=source_trader,
            )
            logger.info(
                "Position opened: %s %.2f shares @ %.4f ($%.2f) on %s",
                asset,
                size,
                price,
                cost,
                market_title[:40],
            )

    def remove_position(self, token_id: str):
        """Remove a closed position from tracking."""
        if token_id in self.positions:
            pos = self.positions.pop(token_id)
            logger.info(
                "Position removed: %s on %s",
                pos.asset,
                pos.market_title[:40],
            )

    def check_stop_losses(self, price_getter) -> list[str]:
        """Check all positions against stop loss and return tokens to close.

        Args:
            price_getter: Callable(token_id) -> float that returns current price.

        Returns:
            List of token_ids that should be closed due to stop loss.
        """
        to_close = []
        for token_id, pos in self.positions.items():
            try:
                current_price = price_getter(token_id)
            except Exception:
                continue

            loss_pct = (pos.entry_price - current_price) / pos.entry_price
            if loss_pct >= self.config.stop_loss_pct:
                logger.warning(
                    "STOP LOSS triggered on %s: entry=%.4f current=%.4f loss=%.1f%%",
                    pos.asset,
                    pos.entry_price,
                    current_price,
                    loss_pct * 100,
                )
                to_close.append(token_id)

        return to_close

    def get_summary(self) -> dict:
        """Get a summary of current risk state."""
        return {
            "total_exposure_usd": round(self.total_exposure, 2),
            "max_exposure_usd": self.config.max_total_exposure_usd,
            "exposure_pct": round(
                self.total_exposure / self.config.max_total_exposure_usd * 100, 1
            )
            if self.config.max_total_exposure_usd > 0
            else 0,
            "position_count": self.position_count,
            "max_positions": self.config.max_positions,
            "positions": [
                {
                    "token": p.token_id[:16],
                    "asset": p.asset,
                    "size": p.size,
                    "entry_price": p.entry_price,
                    "cost_usd": round(p.cost_usd, 2),
                    "market": p.market_title[:60],
                    "source": p.source_trader[:10],
                }
                for p in self.positions.values()
            ],
        }
