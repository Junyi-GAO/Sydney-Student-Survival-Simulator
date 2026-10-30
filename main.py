# Entry point: run python3 main.py (Python 3.8+, standard library only).
"""English terminal interface for Sydney Student Survival Simulator."""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from budget import Budget, CATEGORIES, Simulation, money, parse_money
from display import dashboard, ending, event_card, event_start, event_end, section, welcome


DEFAULT_HISTORY = Path(__file__).resolve().parent / "survival_history.jsonl"


def choose(prompt, options):
    while True:
        answer = input(prompt).strip().lower()
        if answer in options:
            return answer
        print("Choose one of: " + ", ".join(options))


def ask_money(prompt):
    while True:
        try:
            return parse_money(input(prompt))
        except ValueError as error:
            print(error)


def read_budget():
    print("\nAll values are AUD for ONE MONTH. Convert weekly costs first.")
    print("Monthly funds = money available this month, excluding emergency savings.")
    funds = ask_money("Monthly funds: $")
    savings = ask_money("Separate emergency savings: $")
    days = int(choose("Days in this month [28/29/30/31]: ", ("28", "29", "30", "31")))
    expenses = {name: ask_money(f"Monthly {name}: $") for name in CATEGORIES}
    return Budget(funds, savings, expenses, days)


def percent(value):
    return "N/A (zero monthly funds)" if value is None else f"{value:.1f}%"


def show_budget(budget):
    print("\n--- MONTHLY PLAN ---")
    print(f"Monthly funds:          {money(budget.funds)}")
    print(f"Planned expenses:       {money(budget.total)}")
    print(f"Unallocated funds:      {money(budget.remaining)}")
    print(f"Separate savings:       {money(budget.savings)}")
    daily = max(0, budget.remaining) // budget.days
    print(f"Extra spending per day: {money(daily)} (beyond planned expenses)")
    print(f"Rent / monthly funds:   {percent(budget.percentage(budget.expenses['rent']))}")
    print(f"Expenses / funds:       {percent(budget.percentage(budget.total))}")
    print(f"Unallocated / funds:    {percent(budget.percentage(budget.remaining))}")
    if budget.remaining < 0:
        print(f"Your base plan already has a {money(-budget.remaining)} shortfall.")


def play_event(simulation, event, number):
    event_card(event)
    print(f"  Event amount: {money(event.amount)}")
    before = simulation.available
    if event.amount >= 0:
        simulation.apply(event)
        print("\n  >>> RESULT: Payment received. [+]")
    else:
        print("\n  ---- YOUR MOVE " + "-" * 49)
        print("[p] Pay from unallocated funds (a negative balance records a shortfall)")
        options = {"p": "pay"}
        if event.optional:
            print("[k] Skip this optional expense")
            options["k"] = "skip"
        if event.alternative:
            print(f"[a] {event.alternative} ({money(event.alternative_cost)})")
            print(f"    Trade-off: {event.consequence}")
            options["a"] = "alternative"
        if simulation.savings > 0:
            print(f"[s] Transfer savings, then pay (up to {money(simulation.savings)})")
            options["s"] = "savings"
        if simulation.entertainment > 0:
            print(f"[r] Reduce planned entertainment, then pay (up to {money(simulation.entertainment)})")
            options["r"] = "reduce"
        while True:
            action = options[choose(f"\n  >>> EVENT {number}/4 | Your choice: ", options)]
            amount = ask_money("  >>> Amount to transfer/release: $") if action in ("savings", "reduce") else 0
            try:
                simulation.apply(event, action, amount)
                break
            except ValueError as error:
                print(error)
        responses = {
            "pay": "You take the original option. The cost is added to your month.",
            "skip": "You send a polite 'not this time'. No extra cost this round.",
            "savings": "The emergency fund steps in. Your savings balance is now smaller.",
            "reduce": "You trade some planned entertainment for this expense.",
            "alternative": event.consequence,
        }
        print("\n  >>> RESULT")
        print("  " + responses[action])
    print(f"  Wallet buffer: {money(before)} -> {money(simulation.available)}")


def save_report(simulation, path):
    report = simulation.report()
    report["saved_at"] = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(report, ensure_ascii=False) + "\n")


def show_history(path):
    """Read saved summaries; skip malformed records instead of crashing."""
    try:
        with path.open(encoding="utf-8") as handle:
            count = 0
            for line in handle:
                try:
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise ValueError("Not a report")
                    balance = record["final_available_cents"]
                    savings = record["final_savings_cents"]
                    if type(balance) is not int or type(savings) is not int:
                        raise ValueError("Invalid money")
                    if not isinstance(record["saved_at"], str) or record["level"] not in (
                        "BROKE", "CAUTION", "STABLE", "COMFORTABLE"
                    ):
                        raise ValueError("Invalid summary")
                    print(f"{record['saved_at']} | {record['level']} | "
                          f"Available {money(balance)} | Savings {money(savings)}")
                    count += 1
                except (ValueError, KeyError, TypeError):
                    print("Skipped a damaged history record.")
            if count == 0:
                print("No valid saved reports yet.")
    except FileNotFoundError:
        print("No saved reports yet. Complete and save a simulation first.")
    except (OSError, UnicodeError) as error:
        print(f"Could not read history: {error}")


def run_session(seed, history_path, budget=None):
    if budget is None:
        budget = read_budget()
    show_budget(budget)
    simulation = Simulation(budget)
    print("\nFour hypothetical events will test your plan.")
    print("Base expenses are reserved once; event costs are ADDITIONAL.")
    print("Entertainment reductions assume that money has not yet been spent.")
    dashboard(simulation, 0)
    for number, event in enumerate(simulation.draw_events(seed), 1):
        input(f"\n  >>> NEXT: Press Enter to reveal EVENT {number}/4...")
        event_start(number)
        play_event(simulation, event, number)
        dashboard(simulation, number)
        event_end(number)
    input("\n  >>> FINISH: Press Enter to see your month-end results...")
    ending(simulation)
    print(f"Survival level: {simulation.level}")
    print("Game rules: BROKE < $0; CAUTION < 5%; STABLE < 20%; otherwise COMFORTABLE.")
    print("Percentages use initial monthly funds; savings are excluded. Zero funds = CAUTION unless negative.")
    if simulation.available < 0:
        print(f"Unfunded costs: {money(-simulation.available)}. Revise the plan and try again.")
    if choose("Save this report? [y/n]: ", ("y", "n")) == "y":
        try:
            save_report(simulation, history_path)
            print(f"Saved to {history_path}")
        except OSError as error:
            print(f"Could not save the report: {error}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, help="Repeatable event selection for demonstrations")
    parser.add_argument("--history", type=Path, default=DEFAULT_HISTORY, help="Optional history file path")
    args = parser.parse_args()
    welcome()
    try:
        while True:
            section("MAIN MENU / CHOOSE YOUR NEXT STEP")
            print("\n[1] My own budget    [2] Past months    [3] Exit")
            print("[4] Quick play: just landed ($400 buffer, $500 savings)")
            print("[5] Quick play: rent squeeze ($100 buffer, $200 savings)")
            choice = choose("Choose: ", ("1", "2", "3", "4", "5"))
            if choice == "1":
                run_session(args.seed, args.history)
            elif choice == "2":
                show_history(args.history)
            elif choice in ("4", "5"):
                funds, savings = (300000, 50000) if choice == "4" else (270000, 20000)
                budget = Budget(funds, savings, dict(zip(CATEGORIES, (160000, 50000, 16000, 20000, 14000))))
                run_session(args.seed, args.history, budget)
            else:
                print("Goodbye!")
                break
    except (EOFError, KeyboardInterrupt):
        print("\nSession ended. Only previously saved reports were kept.")


if __name__ == "__main__":
    main()
