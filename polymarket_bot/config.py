"""Configuration for the Polymarket copy trading bot."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class PolymarketConfig:
    """Core Polymarket API configuration."""

    clob_host: str = "https://clob.polymarket.com"
    gamma_host: str = "https://gamma-api.polymarket.com"
    data_host: str = "https://data-api.polymarket.com"
    chain_id: int = 137  # Polygon mainnet

    # Wallet credentials (loaded from env)
    private_key: str = ""
    funder_address: str = ""
    signature_type: int = 1  # 0=EOA, 1=Email/Magic, 2=Browser proxy

    def __post_init__(self):
        self.private_key = os.getenv("POLYMARKET_PRIVATE_KEY", self.private_key)
        self.funder_address = os.getenv("POLYMARKET_FUNDER_ADDRESS", self.funder_address)
        sig_type = os.getenv("POLYMARKET_SIGNATURE_TYPE")
        if sig_type is not None:
            self.signature_type = int(sig_type)


@dataclass
class LeaderboardConfig:
    """Settings for which leaderboard traders to follow."""

    # Leaderboard query parameters
    category: str = "OVERALL"  # OVERALL, POLITICS, SPORTS, CRYPTO, etc.
    time_period: str = "WEEK"  # DAY, WEEK, MONTH, ALL
    order_by: str = "PNL"  # PNL or VOL
    top_n: int = 5  # Number of top traders to follow
    min_pnl: float = 0.0  # Minimum PnL to qualify

    def __post_init__(self):
        self.category = os.getenv("LEADERBOARD_CATEGORY", self.category)
        self.time_period = os.getenv("LEADERBOARD_TIME_PERIOD", self.time_period)
        self.order_by = os.getenv("LEADERBOARD_ORDER_BY", self.order_by)
        top_n = os.getenv("LEADERBOARD_TOP_N")
        if top_n is not None:
            self.top_n = int(top_n)
        min_pnl = os.getenv("LEADERBOARD_MIN_PNL")
        if min_pnl is not None:
            self.min_pnl = float(min_pnl)


@dataclass
class RiskConfig:
    """Risk management settings."""

    max_position_size_usd: float = 50.0  # Max per-trade size in USDC
    max_total_exposure_usd: float = 500.0  # Max total portfolio exposure
    max_positions: int = 20  # Max concurrent open positions
    min_price: float = 0.05  # Don't buy below this price
    max_price: float = 0.95  # Don't buy above this price
    allocation_pct: float = 0.1  # % of leader's position to mirror (0.0-1.0)
    stop_loss_pct: float = 0.5  # Close if position loses >50% of value

    def __post_init__(self):
        for attr in [
            "max_position_size_usd",
            "max_total_exposure_usd",
            "min_price",
            "max_price",
            "allocation_pct",
            "stop_loss_pct",
        ]:
            env_key = f"RISK_{attr.upper()}"
            val = os.getenv(env_key)
            if val is not None:
                setattr(self, attr, float(val))
        max_pos = os.getenv("RISK_MAX_POSITIONS")
        if max_pos is not None:
            self.max_positions = int(max_pos)


@dataclass
class BotConfig:
    """Top-level bot configuration."""

    polymarket: PolymarketConfig = field(default_factory=PolymarketConfig)
    leaderboard: LeaderboardConfig = field(default_factory=LeaderboardConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)

    # Polling intervals (seconds)
    leaderboard_poll_interval: int = 300  # Re-fetch leaderboard every 5 min
    position_poll_interval: int = 30  # Check leader positions every 30s
    log_level: str = "INFO"
    dry_run: bool = True  # If True, don't place real orders

    def __post_init__(self):
        poll = os.getenv("LEADERBOARD_POLL_INTERVAL")
        if poll is not None:
            self.leaderboard_poll_interval = int(poll)
        pos_poll = os.getenv("POSITION_POLL_INTERVAL")
        if pos_poll is not None:
            self.position_poll_interval = int(pos_poll)
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)
        dry = os.getenv("DRY_RUN")
        if dry is not None:
            self.dry_run = dry.lower() in ("true", "1", "yes")
