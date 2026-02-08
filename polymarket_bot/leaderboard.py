"""Fetch and parse the Polymarket leaderboard to identify top traders."""

import logging
from dataclasses import dataclass

import httpx

from polymarket_bot.config import LeaderboardConfig

logger = logging.getLogger(__name__)

DATA_API = "https://data-api.polymarket.com"
LEADERBOARD_ENDPOINT = f"{DATA_API}/v1/leaderboard"


@dataclass
class LeaderboardTrader:
    """A trader from the Polymarket leaderboard."""

    rank: int
    address: str  # proxy wallet address
    username: str
    pnl: float
    volume: float
    profile_image: str = ""
    x_username: str = ""
    verified: bool = False


class LeaderboardScraper:
    """Fetches top traders from the Polymarket leaderboard API."""

    def __init__(self, config: LeaderboardConfig):
        self.config = config
        self._http = httpx.Client(timeout=30)

    def fetch_leaderboard(self) -> list[LeaderboardTrader]:
        """Fetch the leaderboard and return top traders matching filters.

        Returns:
            List of LeaderboardTrader objects sorted by rank.
        """
        params = {
            "category": self.config.category,
            "timePeriod": self.config.time_period,
            "orderBy": self.config.order_by,
            "limit": min(self.config.top_n, 50),  # API max is 50
            "offset": 0,
        }

        logger.info(
            "Fetching leaderboard: category=%s period=%s orderBy=%s top_n=%d",
            self.config.category,
            self.config.time_period,
            self.config.order_by,
            self.config.top_n,
        )

        resp = self._http.get(LEADERBOARD_ENDPOINT, params=params)
        resp.raise_for_status()
        data = resp.json()

        traders = []
        for entry in data:
            pnl = float(entry.get("pnl", 0))
            if pnl < self.config.min_pnl:
                continue

            trader = LeaderboardTrader(
                rank=int(entry.get("rank", 0)),
                address=entry.get("proxyWallet", ""),
                username=entry.get("userName", ""),
                pnl=pnl,
                volume=float(entry.get("vol", 0)),
                profile_image=entry.get("profileImage", ""),
                x_username=entry.get("xUsername", ""),
                verified=entry.get("verifiedBadge", False),
            )
            traders.append(trader)

        traders.sort(key=lambda t: t.rank)
        logger.info("Found %d traders matching criteria", len(traders))
        for t in traders:
            logger.info(
                "  #%d %s (PnL: $%.2f, Vol: $%.2f)",
                t.rank,
                t.username or t.address[:10],
                t.pnl,
                t.volume,
            )

        return traders

    def get_trader_addresses(self) -> list[str]:
        """Convenience method to get just the wallet addresses of top traders."""
        traders = self.fetch_leaderboard()
        return [t.address for t in traders if t.address]

    def close(self):
        self._http.close()
