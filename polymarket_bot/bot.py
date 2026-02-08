"""Main bot orchestrator - ties all components together in a polling loop."""

import json
import logging
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

from polymarket_bot.config import BotConfig
from polymarket_bot.copy_engine import CopyEngine, CopyTradeResult
from polymarket_bot.leaderboard import LeaderboardScraper, LeaderboardTrader
from polymarket_bot.monitor import PositionMonitor
from polymarket_bot.polymarket_client import PolymarketClient
from polymarket_bot.risk_manager import RiskManager

logger = logging.getLogger(__name__)

STATE_FILE = Path("polymarket_bot_state.json")


class CopyTradingBot:
    """Orchestrates the copy trading loop.

    Flow:
    1. Fetch leaderboard -> identify top traders
    2. Snapshot their positions on first run
    3. Poll for position changes
    4. Mirror new/changed positions via the copy engine
    5. Check stop losses periodically
    """

    def __init__(self, config: BotConfig):
        self.config = config
        self.running = False

        # Components
        self.leaderboard = LeaderboardScraper(config.leaderboard)
        self.monitor = PositionMonitor(config.polymarket)
        self.risk_manager = RiskManager(config.risk)
        self.client = PolymarketClient(config.polymarket)
        self.engine = CopyEngine(config, self.client, self.risk_manager)

        # State
        self.tracked_traders: list[LeaderboardTrader] = []
        self.trade_log: list[dict] = []
        self._last_leaderboard_fetch: float = 0

    def start(self):
        """Initialize connections and start the main loop."""
        logger.info("=" * 60)
        logger.info("Polymarket Copy Trading Bot starting")
        logger.info("=" * 60)
        logger.info("Mode: %s", "DRY RUN" if self.config.dry_run else "LIVE TRADING")
        logger.info(
            "Leaderboard: top %d by %s (%s, %s)",
            self.config.leaderboard.top_n,
            self.config.leaderboard.order_by,
            self.config.leaderboard.category,
            self.config.leaderboard.time_period,
        )
        logger.info(
            "Risk: max $%.0f/trade, $%.0f total, %d positions, %.0f%% allocation",
            self.config.risk.max_position_size_usd,
            self.config.risk.max_total_exposure_usd,
            self.config.risk.max_positions,
            self.config.risk.allocation_pct * 100,
        )

        # Connect to Polymarket CLOB (only needed for live trading)
        if not self.config.dry_run:
            self.client.connect()
            logger.info("Connected to Polymarket CLOB")

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.running = True
        self._load_state()
        self._run_loop()

    def _signal_handler(self, signum, frame):
        logger.info("Shutdown signal received, stopping...")
        self.running = False

    def _run_loop(self):
        """Main polling loop."""
        iteration = 0

        while self.running:
            try:
                iteration += 1
                now = time.time()

                # Refresh leaderboard periodically
                if now - self._last_leaderboard_fetch > self.config.leaderboard_poll_interval:
                    self._refresh_leaderboard()
                    self._last_leaderboard_fetch = now

                if not self.tracked_traders:
                    logger.warning("No traders to track. Waiting...")
                    time.sleep(self.config.position_poll_interval)
                    continue

                # Get addresses of tracked traders
                addresses = [t.address for t in self.tracked_traders]

                # First scan: just snapshot positions without trading
                first_scan_addresses = [
                    a for a in addresses if self.monitor.is_first_scan(a)
                ]
                if first_scan_addresses:
                    logger.info(
                        "Initial scan for %d traders - snapshotting positions...",
                        len(first_scan_addresses),
                    )
                    for addr in first_scan_addresses:
                        self.monitor.detect_changes(addr)
                    # Remove first-scan addresses from this iteration
                    addresses = [a for a in addresses if a not in first_scan_addresses]

                if addresses:
                    # Detect position changes
                    deltas = self.monitor.scan_all_traders(addresses)

                    if deltas:
                        logger.info(
                            "Detected %d position changes across %d traders",
                            len(deltas),
                            len(set(d.trader_address for d in deltas)),
                        )
                        # Execute copy trades
                        results = self.engine.process_deltas(deltas)
                        self._log_results(results)
                    else:
                        if iteration % 10 == 0:  # Log every 10th quiet iteration
                            logger.debug("No position changes detected (iteration %d)", iteration)

                # Check stop losses every iteration
                if self.risk_manager.position_count > 0:
                    if not self.config.dry_run:
                        sl_results = self.engine.process_stop_losses()
                        if sl_results:
                            self._log_results(sl_results)

                # Periodic status
                if iteration % 20 == 0:
                    self._print_status()

                # Save state
                self._save_state()

                # Wait for next poll
                time.sleep(self.config.position_poll_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error("Error in main loop: %s", e, exc_info=True)
                time.sleep(self.config.position_poll_interval)

        self._shutdown()

    def _refresh_leaderboard(self):
        """Fetch fresh leaderboard data."""
        logger.info("Refreshing leaderboard...")
        try:
            self.tracked_traders = self.leaderboard.fetch_leaderboard()
            logger.info("Now tracking %d traders", len(self.tracked_traders))
        except Exception as e:
            logger.error("Failed to refresh leaderboard: %s", e)

    def _log_results(self, results: list[CopyTradeResult]):
        """Log trade results and add to trade history."""
        for r in results:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action": r.delta.action,
                "asset": r.delta.asset,
                "market": r.delta.market_title,
                "token_id": r.delta.token_id,
                "executed": r.executed,
                "size": r.size,
                "price": r.price,
                "cost_usd": round(r.size * r.price, 2) if r.size and r.price else 0,
                "source_trader": r.delta.trader_address[:16],
                "reason": r.reason,
            }
            self.trade_log.append(entry)

            status = "EXECUTED" if r.executed else "SKIPPED"
            logger.info(
                "[%s] %s %s %.2f @ %.4f ($%.2f) | %s | %s",
                status,
                r.delta.action,
                r.delta.asset,
                r.size,
                r.price,
                r.size * r.price if r.size and r.price else 0,
                r.delta.market_title[:40],
                r.reason,
            )

    def _print_status(self):
        """Print periodic status summary."""
        summary = self.risk_manager.get_summary()
        logger.info("─" * 50)
        logger.info("STATUS UPDATE")
        logger.info(
            "  Exposure: $%.2f / $%.2f (%.1f%%)",
            summary["total_exposure_usd"],
            summary["max_exposure_usd"],
            summary["exposure_pct"],
        )
        logger.info(
            "  Positions: %d / %d",
            summary["position_count"],
            summary["max_positions"],
        )
        logger.info("  Tracked traders: %d", len(self.tracked_traders))
        logger.info("  Total trades logged: %d", len(self.trade_log))
        logger.info("─" * 50)

    def _save_state(self):
        """Persist bot state to disk."""
        try:
            state = {
                "last_updated": datetime.now(timezone.utc).isoformat(),
                "tracked_traders": [
                    {"address": t.address, "username": t.username, "rank": t.rank}
                    for t in self.tracked_traders
                ],
                "risk_summary": self.risk_manager.get_summary(),
                "recent_trades": self.trade_log[-50:],  # Keep last 50
            }
            STATE_FILE.write_text(json.dumps(state, indent=2))
        except Exception as e:
            logger.debug("Failed to save state: %s", e)

    def _load_state(self):
        """Load previous state if available."""
        if STATE_FILE.exists():
            try:
                state = json.loads(STATE_FILE.read_text())
                self.trade_log = state.get("recent_trades", [])
                logger.info(
                    "Loaded previous state: %d trade log entries",
                    len(self.trade_log),
                )
            except Exception as e:
                logger.debug("Could not load state: %s", e)

    def _shutdown(self):
        """Clean up on shutdown."""
        logger.info("Shutting down...")
        self._save_state()
        self.leaderboard.close()
        self.monitor.close()
        logger.info("Bot stopped. Final status:")
        self._print_status()
