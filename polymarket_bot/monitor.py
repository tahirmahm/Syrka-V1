"""Monitor top traders' positions and detect new trades to copy."""

import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

from polymarket_bot.config import PolymarketConfig

logger = logging.getLogger(__name__)

DATA_API = "https://data-api.polymarket.com"


@dataclass
class TraderPosition:
    """A single position held by a tracked trader."""

    trader_address: str
    market_slug: str
    token_id: str
    condition_id: str
    asset: str  # The outcome name (e.g., "Yes", "No")
    size: float  # Number of shares
    avg_price: float
    current_value: float
    pnl: float
    side: str  # "BUY" direction
    market_title: str = ""


@dataclass
class PositionDelta:
    """Represents a change in a trader's position (new, increased, decreased, closed)."""

    trader_address: str
    token_id: str
    condition_id: str
    asset: str
    market_title: str
    action: str  # "OPEN", "INCREASE", "DECREASE", "CLOSE"
    old_size: float
    new_size: float
    size_delta: float  # positive = bought more, negative = sold
    current_price: float

    @property
    def is_buy(self) -> bool:
        return self.size_delta > 0

    @property
    def is_sell(self) -> bool:
        return self.size_delta < 0


class PositionMonitor:
    """Tracks positions of top traders and detects changes."""

    def __init__(self, config: PolymarketConfig):
        self.config = config
        self._http = httpx.Client(timeout=30)
        # State: address -> {token_id -> TraderPosition}
        self._snapshots: dict[str, dict[str, TraderPosition]] = {}

    def fetch_positions(self, trader_address: str) -> list[TraderPosition]:
        """Fetch current positions for a trader from the Data API.

        Args:
            trader_address: The proxy wallet address of the trader.

        Returns:
            List of the trader's current positions.
        """
        url = f"{DATA_API}/positions"
        params = {"user": trader_address}

        try:
            resp = self._http.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            logger.error("Failed to fetch positions for %s: %s", trader_address[:10], e)
            return []

        positions = []
        if not isinstance(data, list):
            data = data.get("positions", []) if isinstance(data, dict) else []

        for entry in data:
            try:
                size = float(entry.get("size", 0))
                if size == 0:
                    continue

                position = TraderPosition(
                    trader_address=trader_address,
                    market_slug=entry.get("marketSlug", entry.get("slug", "")),
                    token_id=entry.get("tokenId", entry.get("token_id", "")),
                    condition_id=entry.get("conditionId", entry.get("condition_id", "")),
                    asset=entry.get("asset", entry.get("outcome", "")),
                    size=size,
                    avg_price=float(entry.get("avgPrice", entry.get("avg_price", 0))),
                    current_value=float(entry.get("currentValue", entry.get("value", 0))),
                    pnl=float(entry.get("pnl", 0)),
                    side="BUY",
                    market_title=entry.get("title", entry.get("question", "")),
                )
                positions.append(position)
            except (ValueError, TypeError) as e:
                logger.warning("Skipping malformed position entry: %s", e)
                continue

        return positions

    def fetch_activity(self, trader_address: str) -> list[dict]:
        """Fetch recent activity/trades for a trader.

        Args:
            trader_address: The proxy wallet address of the trader.

        Returns:
            List of recent activity entries.
        """
        url = f"{DATA_API}/activity"
        params = {"user": trader_address}

        try:
            resp = self._http.get(url, params=params)
            resp.raise_for_status()
            return resp.json() if isinstance(resp.json(), list) else []
        except httpx.HTTPError as e:
            logger.error("Failed to fetch activity for %s: %s", trader_address[:10], e)
            return []

    def detect_changes(self, trader_address: str) -> list[PositionDelta]:
        """Compare current positions against last snapshot to detect changes.

        Args:
            trader_address: The proxy wallet address to check.

        Returns:
            List of position changes (new positions, size changes, closures).
        """
        current_positions = self.fetch_positions(trader_address)
        current_map = {p.token_id: p for p in current_positions}

        old_map = self._snapshots.get(trader_address, {})
        deltas = []

        # Detect new or increased positions
        for token_id, pos in current_map.items():
            old_pos = old_map.get(token_id)
            if old_pos is None:
                # New position opened
                delta = PositionDelta(
                    trader_address=trader_address,
                    token_id=token_id,
                    condition_id=pos.condition_id,
                    asset=pos.asset,
                    market_title=pos.market_title,
                    action="OPEN",
                    old_size=0,
                    new_size=pos.size,
                    size_delta=pos.size,
                    current_price=pos.avg_price,
                )
                deltas.append(delta)
                logger.info(
                    "NEW position: %s opened %.2f shares of %s (%s)",
                    trader_address[:10],
                    pos.size,
                    pos.asset,
                    pos.market_title[:50],
                )
            elif pos.size != old_pos.size:
                size_diff = pos.size - old_pos.size
                action = "INCREASE" if size_diff > 0 else "DECREASE"
                delta = PositionDelta(
                    trader_address=trader_address,
                    token_id=token_id,
                    condition_id=pos.condition_id,
                    asset=pos.asset,
                    market_title=pos.market_title,
                    action=action,
                    old_size=old_pos.size,
                    new_size=pos.size,
                    size_delta=size_diff,
                    current_price=pos.avg_price,
                )
                deltas.append(delta)
                logger.info(
                    "%s position: %s %+.2f shares of %s (%s)",
                    action,
                    trader_address[:10],
                    size_diff,
                    pos.asset,
                    pos.market_title[:50],
                )

        # Detect closed positions
        for token_id, old_pos in old_map.items():
            if token_id not in current_map:
                delta = PositionDelta(
                    trader_address=trader_address,
                    token_id=token_id,
                    condition_id=old_pos.condition_id,
                    asset=old_pos.asset,
                    market_title=old_pos.market_title,
                    action="CLOSE",
                    old_size=old_pos.size,
                    new_size=0,
                    size_delta=-old_pos.size,
                    current_price=0,
                )
                deltas.append(delta)
                logger.info(
                    "CLOSED position: %s sold all %s (%s)",
                    trader_address[:10],
                    old_pos.asset,
                    old_pos.market_title[:50],
                )

        # Update snapshot
        self._snapshots[trader_address] = current_map
        return deltas

    def scan_all_traders(self, addresses: list[str]) -> list[PositionDelta]:
        """Scan all tracked traders for position changes.

        Args:
            addresses: List of trader proxy wallet addresses.

        Returns:
            Combined list of all detected position deltas.
        """
        all_deltas = []
        for addr in addresses:
            deltas = self.detect_changes(addr)
            all_deltas.extend(deltas)
        return all_deltas

    def is_first_scan(self, trader_address: str) -> bool:
        """Check if this trader has been scanned before."""
        return trader_address not in self._snapshots

    def close(self):
        self._http.close()
