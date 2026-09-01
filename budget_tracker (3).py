"""
Personal Finance / Budget Tracker
--------------------------------------------------------------
A simple, local, command-line budget tracker.

Core (no dependencies required):
- Stores transactions in a local CSV file (transactions.csv)
- Add income / expense entries
- View summary (totals, by category)
- Text-based ASCII charts in the terminal
- Set monthly budget caps per category, with 80%/100% alerts
- Export a summary to CSV (budget_summary.csv)

Optional (only if matplotlib is installed):
- Save real PNG charts to a charts/ folder
- Generate a styled HTML monthly report with embedded charts

Install the optional extra with:
    pip install matplotlib

Run:
    python budget_tracker.py
"""

import csv
import os
from datetime import datetime
from collections import defaultdict

DATA_FILE = "transactions.csv"
BUDGET_FILE = "budgets.csv"
CHARTS_DIR = "charts"
SUMMARY_EXPORT_FILE = "budget_summary.csv"
REPORT_FILE = "monthly_report.html"

TRANS_FIELDNAMES = ["date", "type", "category", "amount", "description"]
BUDGET_FIELDNAMES = ["category", "limit"]
BAR_WIDTH = 40  # max characters wide for ASCII bars

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


# ---------------------------------------------------------------------
# Transaction data handling
# ---------------------------------------------------------------------

def init_file():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=TRANS_FIELDNAMES)
            writer.writeheader()


def load_data():
    init_file()
    rows = []
    with open(DATA_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row["amount"] = float(row["amount"])
                row["date_obj"] = datetime.strptime(row["date"], "%Y-%m-%d")
                rows.append(row)
            except (ValueError, KeyError):
                continue
    rows.sort(key=lambda r: r["date_obj"])
    return rows


def add_transaction():
    print("\n--- Add Transaction ---")
    t_type = ""
    while t_type not in ("income", "expense"):
        t_type = input("Type (income/expense): ").strip().lower()

    category = input("Category (e.g. Food, Rent, Salary): ").strip() or "Uncategorized"

    amount = None
    while amount is None:
        try:
            amount = abs(float(input("Amount: ").strip()))
        except ValueError:
            print("Please enter a valid number.")

    description = input("Description (optional): ").strip()

    date_str = input("Date (YYYY-MM-DD, leave blank for today): ").strip()
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    else:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format, using today's date instead.")
            date_str = datetime.now().strftime("%Y-%m-%d")

    init_file()
    with open(DATA_FILE, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=TRANS_FIELDNAMES)
        writer.writerow({
            "date": date_str,
            "type": t_type,
            "category": category,
            "amount": amount,
            "description": description,
        })
    print("Transaction added.")

    if t_type == "expense":
        check_budget_alert(category, date_str)
    print()


# ---------------------------------------------------------------------
# Budget handling
# ---------------------------------------------------------------------

def init_budget_file():
    if not os.path.exists(BUDGET_FILE):
        with open(BUDGET_FILE, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=BUDGET_FIELDNAMES)
            writer.writeheader()


def load_budgets():
    """Returns dict: {category: limit}"""
    init_budget_file()
    budgets = {}
    with open(BUDGET_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                budgets[row["category"]] = float(row["limit"])
            except (ValueError, KeyError):
                continue
    return budgets


def save_budgets(budgets):
    with open(BUDGET_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=BUDGET_FIELDNAMES)
        writer.writeheader()
        for category, limit in budgets.items():
            writer.writerow({"category": category, "limit": limit})


def set_budget():
    print("\n--- Set Budget ---")
    category = input("Category (e.g. Food): ").strip()
    if not category:
        print("Category cannot be empty.\n")
        return

    limit = None
    while limit is None:
        try:
            limit = abs(float(input(f"Monthly limit for '{category}': $").strip()))
        except ValueError:
            print("Please enter a valid number.")

    budgets = load_budgets()
    budgets[category] = limit
    save_budgets(budgets)
    print(f"Budget set: {category} -> ${limit:,.2f} / month\n")


def _month_expense_for_category(rows, category, month_str):
    return sum(
        r["amount"] for r in rows
        if r["type"] == "expense"
        and r["category"] == category
        and r["date_obj"].strftime("%Y-%m") == month_str
    )


def check_budget_alert(category, date_str):
    """Called right after logging an expense. Warns at 80% / 100%+."""
    budgets = load_budgets()
    if category not in budgets:
        return  # no budget set for this category

    limit = budgets[category]
    month_str = date_str[:7]  # YYYY-MM
    rows = load_data()
    spent = _month_expense_for_category(rows, category, month_str)
    pct = (spent / limit * 100) if limit > 0 else 0

    if pct >= 100:
        print(f"ALERT: You've EXCEEDED your '{category}' budget! "
              f"${spent:,.2f} / ${limit:,.2f} ({pct:.0f}%)")
    elif pct >= 80:
        print(f"WARNING: You've used {pct:.0f}% of your '{category}' budget "
              f"(${spent:,.2f} / ${limit:,.2f})")


def view_budget_status():
    """Shows all budgets vs. current month's spending, with visual bars."""
    budgets = load_budgets()
    if not budgets:
        print("\nNo budgets set yet. Use 'Set budget' to add one.\n")
        return

    rows = load_data()
    current_month = datetime.now().strftime("%Y-%m")

    print(f"\n--- Budget Status ({current_month}) ---")
    for category, limit in budgets.items():
        spent = _month_expense_for_category(rows, category, current_month)
        pct = (spent / limit * 100) if limit > 0 else 0
        bar_len = int(min(pct, 100) / 100 * BAR_WIDTH)
        bar = "#" * bar_len + "-" * (BAR_WIDTH - bar_len)
        flag = ""
        if pct >= 100:
            flag = "  <<< OVER BUDGET"
        elif pct >= 80:
            flag = "  <<< NEAR LIMIT"
        print(f"  {category:<15} [{bar}] {pct:5.1f}%  (${spent:,.2f} / ${limit:,.2f}){flag}")
    print()


# ---------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------

def _compute_summary(rows):
    income = sum(r["amount"] for r in rows if r["type"] == "income")
    expenses = sum(r["amount"] for r in rows if r["type"] == "expense")

    cat_totals = defaultdict(float)
    for r in rows:
        if r["type"] == "expense":
            cat_totals[r["category"]] += r["amount"]

    monthly = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for r in rows:
        month = r["date_obj"].strftime("%Y-%m")
        monthly[month][r["type"]] += r["amount"]

    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
        "by_category": dict(sorted(cat_totals.items(), key=lambda x: -x[1])),
        "by_month": dict(sorted(monthly.items())),
    }


def view_summary():
    rows = load_data()
    if not rows:
        print("\nNo transactions yet.\n")
        return

    s = _compute_summary(rows)
    print("\n--- Summary ---")
    print(f"Total Income:   ${s['income']:,.2f}")
    print(f"Total Expenses: ${s['expenses']:,.2f}")
    print(f"Balance:        ${s['balance']:,.2f}")

    print("\nExpenses by category:")
    if not s["by_category"]:
        print("  (none)")
    else:
        for c, amt in s["by_category"].items():
            print(f"  {c:<20} ${amt:,.2f}")
    print()


# ---------------------------------------------------------------------
# ASCII charts (always available)
# ---------------------------------------------------------------------

def _print_bar_chart(labels_and_values, title, unit="$"):
    print(f"\n--- {title} ---")
    if not labels_and_values:
        print("  (no data)\n")
        return
    max_val = max(abs(v) for _, v in labels_and_values) or 1
    max_label_len = max(len(str(label)) for label, _ in labels_and_values)
    for label, value in labels_and_values:
        bar_len = int((abs(value) / max_val) * BAR_WIDTH)
        bar = "#" * bar_len
        print(f"  {str(label):<{max_label_len}} | {bar} {unit}{value:,.2f}")
    print()


def plot_expenses_by_category():
    rows = load_data()
    s = _compute_summary(rows)
    _print_bar_chart(list(s["by_category"].items()), "Expenses by Category")


def plot_income_vs_expenses():
    rows = load_data()
    s = _compute_summary(rows)
    if not s["by_month"]:
        print("\nNo data to plot.\n")
        return
    print("\n--- Income vs Expenses by Month ---")
    max_val = max(max(v["income"], v["expense"]) for v in s["by_month"].values()) or 1
    for month, v in s["by_month"].items():
        inc_bar = "#" * int((v["income"] / max_val) * BAR_WIDTH)
        exp_bar = "*" * int((v["expense"] / max_val) * BAR_WIDTH)
        print(f"  {month}  Income  | {inc_bar} ${v['income']:,.2f}")
        print(f"  {month}  Expense | {exp_bar} ${v['expense']:,.2f}")
    print()


def plot_balance_over_time():
    rows = load_data()
    if not rows:
        print("\nNo data to plot.\n")
        return
    print("\n--- Balance Over Time ---")
    running = 0.0
    data = []
    for r in rows:
        running += r["amount"] if r["type"] == "income" else -r["amount"]
        data.append((r["date"], running))
    if len(data) > 20:
        data = data[-20:]
        print("  (showing most recent 20 entries)")
    max_val = max(abs(v) for _, v in data) or 1
    for date, value in data:
        bar_len = int((abs(value) / max_val) * BAR_WIDTH)
        bar = ("+" if value >= 0 else "-") * bar_len
        print(f"  {date} | {bar} ${value:,.2f}")
    print()


# ---------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------

def export_summary_csv():
    rows = load_data()
    if not rows:
        print("\nNo transactions yet, nothing to export.\n")
        return

    s = _compute_summary(rows)
    budgets = load_budgets()
    current_month = datetime.now().strftime("%Y-%m")

    with open(SUMMARY_EXPORT_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Personal Finance Summary"])
        writer.writerow(["Generated on", datetime.now().strftime("%Y-%m-%d %H:%M")])
        writer.writerow([])

        writer.writerow(["Overall Totals"])
        writer.writerow(["Total Income", f"{s['income']:.2f}"])
        writer.writerow(["Total Expenses", f"{s['expenses']:.2f}"])
        writer.writerow(["Balance", f"{s['balance']:.2f}"])
        writer.writerow([])

        writer.writerow(["Expenses by Category"])
        writer.writerow(["Category", "Total Spent", "Budget Limit", "% Used"])
        for cat, amt in s["by_category"].items():
            limit = budgets.get(cat)
            if limit:
                month_spent = _month_expense_for_category(rows, cat, current_month)
                pct = f"{(month_spent / limit * 100):.0f}%"
                writer.writerow([cat, f"{amt:.2f}", f"{limit:.2f}", pct])
            else:
                writer.writerow([cat, f"{amt:.2f}", "", ""])
        writer.writerow([])

        writer.writerow(["Income vs Expenses by Month"])
        writer.writerow(["Month", "Income", "Expenses", "Net"])
        for month, v in s["by_month"].items():
            writer.writerow([month, f"{v['income']:.2f}", f"{v['expense']:.2f}",
                              f"{v['income'] - v['expense']:.2f}"])

    print(f"\nSummary exported to '{SUMMARY_EXPORT_FILE}'. "
          f"You can open it in Excel or attach it to an email.\n")


# ---------------------------------------------------------------------
# Matplotlib PNG charts (optional)
# ---------------------------------------------------------------------

def save_charts_png(silent=False):
    """Generates and saves PNG charts to the charts/ folder. Returns list of paths saved."""
    if not MATPLOTLIB_AVAILABLE:
        if not silent:
            print("\nmatplotlib is not installed, so PNG charts can't be generated.")
            print("Install it with:  pip install matplotlib\n")
        return []

    rows = load_data()
    if not rows:
        if not silent:
            print("\nNo transactions yet, nothing to chart.\n")
        return []

    os.makedirs(CHARTS_DIR, exist_ok=True)
    s = _compute_summary(rows)
    saved = []

    # Pie chart: expenses by category
    if s["by_category"]:
        plt.figure(figsize=(7, 7))
        plt.pie(s["by_category"].values(), labels=s["by_category"].keys(),
                autopct="%1.1f%%", startangle=90)
        plt.title("Expenses by Category")
        plt.tight_layout()
        path = os.path.join(CHARTS_DIR, "expenses_by_category.png")
        plt.savefig(path)
        plt.close()
        saved.append(path)

    # Bar chart: income vs expenses by month
    if s["by_month"]:
        months = list(s["by_month"].keys())
        income_vals = [s["by_month"][m]["income"] for m in months]
        expense_vals = [s["by_month"][m]["expense"] for m in months]
        x = range(len(months))
        width = 0.35
        plt.figure(figsize=(9, 5))
        plt.bar([i - width / 2 for i in x], income_vals, width, label="Income")
        plt.bar([i + width / 2 for i in x], expense_vals, width, label="Expense")
        plt.xticks(list(x), months, rotation=45)
        plt.ylabel("Amount ($)")
        plt.title("Income vs Expenses by Month")
        plt.legend()
        plt.tight_layout()
        path = os.path.join(CHARTS_DIR, "income_vs_expenses.png")
        plt.savefig(path)
        plt.close()
        saved.append(path)

    # Line chart: balance over time
    dates = [r["date"] for r in rows]
    running_vals = []
    running = 0.0
    for r in rows:
        running += r["amount"] if r["type"] == "income" else -r["amount"]
        running_vals.append(running)
    plt.figure(figsize=(9, 5))
    plt.plot(dates, running_vals, marker="o")
    plt.axhline(0, color="gray", linewidth=0.8, linestyle="--")
    plt.xticks(rotation=45)
    plt.ylabel("Balance ($)")
    plt.title("Balance Over Time")
    plt.tight_layout()
    path = os.path.join(CHARTS_DIR, "balance_over_time.png")
    plt.savefig(path)
    plt.close()
    saved.append(path)

    if not silent:
        print(f"\nSaved {len(saved)} chart(s) to the '{CHARTS_DIR}/' folder:")
        for p in saved:
            print(f"  {p}")
        print()

    return saved


# ---------------------------------------------------------------------
# HTML monthly report
# ---------------------------------------------------------------------

def generate_html_report():
    rows = load_data()
    if not rows:
        print("\nNo transactions yet, nothing to report.\n")
        return

    s = _compute_summary(rows)
    budgets = load_budgets()
    current_month = datetime.now().strftime("%Y-%m")
    chart_paths = save_charts_png(silent=True)  # empty list if matplotlib missing

    def rel(p):
        return p.replace(os.sep, "/") if p else ""

    charts_html = ""
    if chart_paths:
        for p in chart_paths:
            charts_html += f'<img src="{rel(p)}" alt="chart" class="chart-img">\n'
    else:
        charts_html = "<p><em>Install matplotlib (pip install matplotlib) to include charts here.</em></p>"

    category_rows = ""
    for cat, amt in s["by_category"].items():
        limit = budgets.get(cat)
        if limit:
            month_spent = _month_expense_for_category(rows, cat, current_month)
            pct = month_spent / limit * 100
            status = "over" if pct >= 100 else ("near" if pct >= 80 else "ok")
            limit_html = f"${limit:,.2f}"
            pct_html = f'<span class="badge {status}">{pct:.0f}%</span>'
        else:
            limit_html = "—"
            pct_html = "—"
        category_rows += (
            f"<tr><td>{cat}</td><td>${amt:,.2f}</td>"
            f"<td>{limit_html}</td><td>{pct_html}</td></tr>\n"
        )

    month_rows = ""
    for month, v in s["by_month"].items():
        net = v["income"] - v["expense"]
        net_class = "positive" if net >= 0 else "negative"
        month_rows += (
            f"<tr><td>{month}</td><td>${v['income']:,.2f}</td>"
            f"<td>${v['expense']:,.2f}</td>"
            f"<td class='{net_class}'>${net:,.2f}</td></tr>\n"
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Monthly Finance Report</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Arial, sans-serif; max-width: 900px;
          margin: 40px auto; padding: 0 20px; color: #222; background: #fafafa; }}
  h1 {{ margin-bottom: 0; }}
  .generated {{ color: #888; font-size: 0.9em; margin-top: 4px; }}
  .totals {{ display: flex; gap: 20px; margin: 24px 0; }}
  .card {{ background: white; border-radius: 10px; padding: 16px 20px;
           box-shadow: 0 1px 3px rgba(0,0,0,0.1); flex: 1; }}
  .card h3 {{ margin: 0 0 6px 0; font-size: 0.85em; text-transform: uppercase;
              color: #888; }}
  .card .value {{ font-size: 1.5em; font-weight: 600; }}
  table {{ width: 100%; border-collapse: collapse; background: white;
           border-radius: 10px; overflow: hidden; margin-bottom: 30px;
           box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
  th, td {{ text-align: left; padding: 10px 14px; border-bottom: 1px solid #eee; }}
  th {{ background: #f0f0f0; font-size: 0.85em; text-transform: uppercase; color: #666; }}
  .positive {{ color: #1a7f37; font-weight: 600; }}
  .negative {{ color: #cf222e; font-weight: 600; }}
  .badge {{ padding: 2px 8px; border-radius: 12px; font-size: 0.85em; font-weight: 600; }}
  .badge.ok {{ background: #dafbe1; color: #1a7f37; }}
  .badge.near {{ background: #fff8c5; color: #9a6700; }}
  .badge.over {{ background: #ffebe9; color: #cf222e; }}
  .chart-img {{ width: 100%; max-width: 700px; display: block; margin: 20px auto;
                border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
</style>
</head>
<body>
  <h1>Personal Finance Report</h1>
  <div class="generated">Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>

  <div class="totals">
    <div class="card"><h3>Total Income</h3><div class="value">${s['income']:,.2f}</div></div>
    <div class="card"><h3>Total Expenses</h3><div class="value">${s['expenses']:,.2f}</div></div>
    <div class="card"><h3>Balance</h3><div class="value">${s['balance']:,.2f}</div></div>
  </div>

  <h2>Charts</h2>
  {charts_html}

  <h2>Expenses by Category</h2>
  <table>
    <tr><th>Category</th><th>Total Spent</th><th>Budget</th><th>Used This Month</th></tr>
    {category_rows if category_rows else "<tr><td colspan='4'>No expenses yet.</td></tr>"}
  </table>

  <h2>Income vs Expenses by Month</h2>
  <table>
    <tr><th>Month</th><th>Income</th><th>Expenses</th><th>Net</th></tr>
    {month_rows if month_rows else "<tr><td colspan='4'>No monthly data yet.</td></tr>"}
  </table>
</body>
</html>
"""

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nHTML report generated: '{REPORT_FILE}'. Open it in any web browser to view.\n")


# ---------------------------------------------------------------------
# Menu
# ---------------------------------------------------------------------

def main():
    init_file()
    init_budget_file()
    menu = """
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
"""
    while True:
        print(menu)
        choice = input("Choose an option (1-11): ").strip()

        if choice == "1":
            add_transaction()
        elif choice == "2":
            view_summary()
        elif choice == "3":
            plot_expenses_by_category()
        elif choice == "4":
            plot_income_vs_expenses()
        elif choice == "5":
            plot_balance_over_time()
        elif choice == "6":
            set_budget()
        elif choice == "7":
            view_budget_status()
        elif choice == "8":
            export_summary_csv()
        elif choice == "9":
            generate_html_report()
        elif choice == "10":
            save_charts_png()
        elif choice == "11":
            print("Goodbye!")
            break
        else:
            print("Invalid choice, try again.")


if __name__ == "__main__":
    main()
