# Smart Market Watchlist

> **A normal watchlist tells you what your stocks are doing. Smart Watchlist tells you what you missed.**

Smart Market Watchlist is a context-aware market watchlist designed to reduce attention overload.

Instead of showing every price movement, it identifies **meaningful changes**, explains why they matter, remembers what the user has already seen, and surfaces only genuinely new developments.

## What makes it different?

Traditional watchlists answer:

> "How are my stocks doing?"

Smart Watchlist answers:

> **"What changed since I last checked, why did it change, and does it matter?"**

### Core capabilities

- **Meaningful-change detection** using a deterministic attention engine
- **Evidence-first explanations** for every important movement
- **Last-seen state** to distinguish new changes from already-seen changes
- **Market and sector context** for relative movement
- **Volume anomaly detection**
- **Corporate-event context**
- **Data-quality awareness** for fresh, delayed, stale and conflicting data
- **Persistent watchlists** with add, remove and reorder support
- **Deterministic demo scenarios** for reproducible evaluation
- **Provider abstraction** designed for integration with real market-data providers

## Example

A company moves +5.5%.

Instead of simply displaying:

`TCS +5.5%`

the system explains:

- Price moved +5.5%
- Volume is 3.2× average
- Moved 5.1% relative to sector
- Relevant company event detected

The attention engine combines these signals to determine whether the movement deserves the user's attention.

## "What did I miss?"

The system maintains a `last_market_check_at` timestamp.

This allows it to distinguish between:

- **Important but already seen**
- **Important and NEW**
- **No meaningful change**

For example:

```text
Company Move
    ↓
TCS +4.2%
    ↓
User checks the dashboard
    ↓
Marked as seen
    ↓
Refresh
    ↓
0 new meaningful changes
    ↓
NEW_UPDATE occurs
    ↓
TCS +5.5%
    ↓
1 NEW meaningful change


React + TypeScript + Vite
            |
        Typed API
            |
          FastAPI
            |
    +-------+-------+
    |       |       |
  Domain Services Providers
    |       |       |
    +-------+-------+
            |
       PostgreSQL
