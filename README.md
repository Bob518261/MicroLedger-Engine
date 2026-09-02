## Features

- Add income / expense transactions (stored in `transactions.csv`)
- View a summary of totals and spending by category
- ASCII bar charts printed right in the terminal (no dependencies needed)
- Set monthly budget caps per category, with automatic alerts at 80% and 100%+
- Export a summary to CSV
- Optional: save real PNG charts and generate a styled HTML monthly report
  (requires `matplotlib`)

## Setup

Requires Python 3.8+.

```bash
git clone <this-repo-url>
cd <this-repo>
pip install -r requirements.txt   # optional, only needed for PNG/HTML charts
python budget_tracker.py
```

If you skip the `pip install`, everything still works except the PNG export
and HTML report's embedded charts — those two features will just print a
message telling you to install matplotlib.

## Usage

Run the script and follow the on-screen menu:

```
=== Personal Finance Tracker ===
1.  Add transaction
2.  View summary
3.  Chart: Expenses by category (ASCII)
4.  Chart: Income vs Expenses by month (ASCII)
5.  Chart: Balance over time (ASCII)
6.  Set budget for a category
7.  View budget status & alerts
8.  Export summary to CSV
9.  Generate HTML monthly report (with charts)
10. Save charts as PNG files
11. Exit
```

## License

MIT — do whatever you want with it.
