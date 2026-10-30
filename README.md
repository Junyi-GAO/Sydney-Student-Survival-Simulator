# Sydney Student Survival Simulator

**Can your budget survive a month in Sydney?**

A Python terminal simulation for university students, especially those new to Sydney. Set a monthly budget, face four unexpected events, and see how your choices affect your remaining funds.

## Run

Requires Python 3.8 or newer. Uses only the Python standard library.
Download the repository files into one folder, open a terminal there, and run:

```bash
python3 main.py
```

On Windows, use `python main.py` if that is your Python command.
Choose **4** for a quick play with a $400 buffer, **5** for a tighter $100 buffer, or **1** to enter your own budget.

For repeatable event selection:

```bash
python3 main.py --seed 42
```

## Features

- Monthly budgeting for rent, food, transport, entertainment and other expenses.
- Four distinct encounters from twelve Sydney student-life scenarios.
- Pay, skip optional expenses, use savings, reduce entertainment spending, or choose a cheaper alternative when available.
- ASCII illustrations, clear event separators, progress indicators and themed endings.
- A final decision summary and optional local report saving.

## Tests

```bash
python3 -m unittest -v
```

The 12 tests cover money input, budget calculations, funding decisions, alternative costs, event selection, rating boundaries and history file handling.

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Entry point, interaction, report saving and history reading |
| `budget.py` | Budget model, event pool and financial rules |
| `display.py` | ASCII illustrations and terminal layouts |
| `test_budget.py` | Automated tests |

## How the budget works

All amounts are AUD. Enter monthly expenses and keep emergency savings separate from monthly funds. Base expenses are reserved once. Events are additional costs or payments. Savings transfers do not create income; entertainment reductions release money previously reserved for that category. Cheaper alternatives replace the original event cost.

A negative buffer represents unfunded costs. Survival ratings use the remaining buffer as a percentage of initial monthly funds: BROKE below zero, CAUTION below 5%, STABLE below 20%, and COMFORTABLE at 20% or more. With zero initial funds, a non-negative outcome is CAUTION. Savings are displayed separately.

Reports are created in `survival_history.jsonl` only when you choose to save. No existing history file is needed to run the program.

## Project context

Created for the COMP9001 final project. File input/output and automated testing demonstrate advanced course topics. Event amounts are fictional and the ratings are game rules, not predictions of real financial security.
