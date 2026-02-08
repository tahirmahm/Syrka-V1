"""Entry point for the Polymarket Copy Trading Bot."""

import argparse
import logging
import sys

from polymarket_bot.config import BotConfig
from polymarket_bot.bot import CopyTradingBot
from polymarket_bot.leaderboard import LeaderboardScraper


def setup_logging(level: str = "INFO"):
    """Configure structured logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("polymarket_bot.log"),
        ],
    )


def cmd_run(args):
    """Run the copy trading bot."""
    config = BotConfig()

    # CLI overrides
    if args.dry_run is not None:
        config.dry_run = args.dry_run
    if args.top_n is not None:
        config.leaderboard.top_n = args.top_n
    if args.category:
        config.leaderboard.category = args.category
    if args.period:
        config.leaderboard.time_period = args.period
    if args.max_exposure:
        config.risk.max_total_exposure_usd = args.max_exposure
    if args.max_position:
        config.risk.max_position_size_usd = args.max_position
    if args.allocation:
        config.risk.allocation_pct = args.allocation / 100.0

    setup_logging(config.log_level)

    bot = CopyTradingBot(config)
    bot.start()


def cmd_leaderboard(args):
    """Show current leaderboard."""
    config = BotConfig()
    if args.category:
        config.leaderboard.category = args.category
    if args.period:
        config.leaderboard.time_period = args.period
    if args.top_n:
        config.leaderboard.top_n = args.top_n

    setup_logging("INFO")

    scraper = LeaderboardScraper(config.leaderboard)
    traders = scraper.fetch_leaderboard()

    print(f"\n{'Rank':<6}{'Username':<20}{'PnL':>12}{'Volume':>14}{'Address':<16}")
    print("─" * 70)
    for t in traders:
        print(
            f"{t.rank:<6}{(t.username or 'anon'):<20}${t.pnl:>10,.2f}  ${t.volume:>11,.2f}  {t.address[:14]}"
        )
    print()
    scraper.close()


def cmd_status(args):
    """Show bot state from the state file."""
    import json
    from pathlib import Path

    state_file = Path("polymarket_bot_state.json")
    if not state_file.exists():
        print("No state file found. Has the bot been run yet?")
        return

    state = json.loads(state_file.read_text())
    print(f"\nLast updated: {state.get('last_updated', 'unknown')}")

    risk = state.get("risk_summary", {})
    print(f"\nExposure: ${risk.get('total_exposure_usd', 0):.2f} / ${risk.get('max_exposure_usd', 0):.2f}")
    print(f"Positions: {risk.get('position_count', 0)} / {risk.get('max_positions', 0)}")

    traders = state.get("tracked_traders", [])
    if traders:
        print(f"\nTracked traders ({len(traders)}):")
        for t in traders:
            print(f"  #{t.get('rank', '?')} {t.get('username', t.get('address', '')[:14])}")

    trades = state.get("recent_trades", [])
    if trades:
        print(f"\nRecent trades ({len(trades)}):")
        for t in trades[-10:]:
            status = "OK" if t.get("executed") else "SKIP"
            print(
                f"  [{status}] {t.get('action', '?')} {t.get('asset', '?')} "
                f"${t.get('cost_usd', 0):.2f} | {t.get('market', '')[:40]} | {t.get('reason', '')}"
            )
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Polymarket Copy Trading Bot - Mirror trades from top performers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # View the current leaderboard
  python -m polymarket_bot.main leaderboard --top-n 10

  # Run bot in dry-run mode (no real trades)
  python -m polymarket_bot.main run --dry-run --top-n 5

  # Run bot live with custom risk settings
  python -m polymarket_bot.main run --no-dry-run --max-exposure 1000 --max-position 100 --allocation 5

  # Check bot status
  python -m polymarket_bot.main status
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Start the copy trading bot")
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        dest="dry_run",
        help="Simulate trades without executing (default)",
    )
    run_parser.add_argument(
        "--no-dry-run",
        action="store_false",
        dest="dry_run",
        help="Execute real trades (requires wallet config)",
    )
    run_parser.add_argument("--top-n", type=int, help="Number of top traders to follow")
    run_parser.add_argument(
        "--category",
        choices=["OVERALL", "POLITICS", "SPORTS", "CRYPTO", "CULTURE", "WEATHER", "ECONOMICS", "TECH", "FINANCE"],
        help="Leaderboard category",
    )
    run_parser.add_argument(
        "--period",
        choices=["DAY", "WEEK", "MONTH", "ALL"],
        help="Leaderboard time period",
    )
    run_parser.add_argument("--max-exposure", type=float, help="Max total exposure in USD")
    run_parser.add_argument("--max-position", type=float, help="Max per-trade size in USD")
    run_parser.add_argument(
        "--allocation",
        type=float,
        help="Percentage of leader's position to mirror (1-100)",
    )

    # Leaderboard command
    lb_parser = subparsers.add_parser("leaderboard", help="Show the current leaderboard")
    lb_parser.add_argument("--top-n", type=int, default=10, help="Number of traders to show")
    lb_parser.add_argument("--category", default="OVERALL", help="Leaderboard category")
    lb_parser.add_argument("--period", default="WEEK", help="Time period")

    # Status command
    subparsers.add_parser("status", help="Show current bot status")

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "leaderboard":
        cmd_leaderboard(args)
    elif args.command == "status":
        cmd_status(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
