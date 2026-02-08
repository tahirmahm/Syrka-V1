# Polymarket Copy Trading Bot

A Python bot that monitors the Polymarket leaderboard, tracks top-performing traders' positions, and automatically mirrors their trades on your account.

## How It Works

1. **Leaderboard Fetch** - Queries the Polymarket Data API to identify top traders by PnL or volume
2. **Position Monitoring** - Polls each trader's positions via the Data API to detect new entries, increases, decreases, and closures
3. **Copy Execution** - When a leader opens or changes a position, the bot mirrors the trade at a configurable allocation percentage through the CLOB API
4. **Risk Management** - Enforces per-trade limits, total exposure caps, price bounds, max position count, and stop losses

## Architecture

```
polymarket_bot/
├── config.py              # All configuration (env vars + defaults)
├── leaderboard.py         # Fetches top traders from leaderboard API
├── monitor.py             # Tracks trader positions, detects changes
├── polymarket_client.py   # Wrapper around py-clob-client for trading
├── copy_engine.py         # Decides when/how to mirror trades
├── risk_manager.py        # Position sizing and risk enforcement
├── bot.py                 # Main orchestrator loop
└── main.py                # CLI entry point
```

## Setup

### 1. Install Dependencies

```bash
pip install -r polymarket_bot/requirements.txt
```

### 2. Configure Environment

```bash
cp polymarket_bot/.env.example .env
```

Edit `.env` with your credentials:

- **POLYMARKET_PRIVATE_KEY** - Export from https://reveal.polymarket.com or your wallet
- **POLYMARKET_FUNDER_ADDRESS** - The address you deposit USDC to on Polymarket
- **POLYMARKET_SIGNATURE_TYPE** - `0` for MetaMask/EOA, `1` for email/Magic wallet, `2` for browser proxy

### 3. Fund Your Account

Make sure your Polymarket account has USDC.e (contract `0x2791bca1f2de4661ed88a30c99a7a9449aa84174`) on Polygon.

## Usage

### View the Leaderboard

```bash
python -m polymarket_bot.main leaderboard --top-n 10 --period WEEK
```

### Run in Dry-Run Mode (Recommended First)

```bash
python -m polymarket_bot.main run --dry-run --top-n 5
```

This simulates all trades without placing real orders - use this to verify the bot tracks the right traders and makes sensible decisions.

### Run Live

```bash
python -m polymarket_bot.main run --no-dry-run --top-n 5 --max-exposure 500 --max-position 50 --allocation 10
```

### Check Bot Status

```bash
python -m polymarket_bot.main status
```

## CLI Options

| Flag | Description | Default |
|------|-------------|---------|
| `--dry-run` | Simulate without trading | On |
| `--no-dry-run` | Enable live trading | Off |
| `--top-n N` | Number of leaders to follow | 5 |
| `--category CAT` | Leaderboard category (OVERALL, CRYPTO, etc.) | OVERALL |
| `--period P` | Time period (DAY, WEEK, MONTH, ALL) | WEEK |
| `--max-exposure USD` | Max total portfolio exposure | $500 |
| `--max-position USD` | Max per-trade size | $50 |
| `--allocation PCT` | % of leader's position to mirror (1-100) | 10 |

## Risk Controls

- **Position sizing**: Copies only a configurable % of leader's position (default 10%)
- **Per-trade cap**: No single trade exceeds `max_position_size_usd` (default $50)
- **Total exposure cap**: Total portfolio limited to `max_total_exposure_usd` (default $500)
- **Position count limit**: Max 20 concurrent positions
- **Price bounds**: Skips trades below $0.05 or above $0.95
- **Stop loss**: Closes positions that lose more than 50% of entry value

## Environment Variables

See `.env.example` for all available settings. Key variables:

| Variable | Description |
|----------|-------------|
| `POLYMARKET_PRIVATE_KEY` | Wallet private key for signing |
| `POLYMARKET_FUNDER_ADDRESS` | Proxy/funder wallet address |
| `POLYMARKET_SIGNATURE_TYPE` | Wallet type (0/1/2) |
| `DRY_RUN` | Enable dry-run mode |
| `LEADERBOARD_TOP_N` | Leaders to follow |
| `RISK_MAX_TOTAL_EXPOSURE_USD` | Portfolio exposure limit |
| `RISK_ALLOCATION_PCT` | Copy allocation ratio |

## Important Notes

- **Start with dry-run mode** to understand how the bot operates before risking real funds
- Polymarket's Terms of Service prohibit US persons from trading
- The CLOB API has a rate limit of 60 orders per minute
- The bot persists state to `polymarket_bot_state.json` for crash recovery
- Logs are written to `polymarket_bot.log`
