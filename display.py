"""Small ASCII decorations and readable terminal summaries. No extra libraries."""

from textwrap import wrap
from budget import money


ART = {
    "The unexpected commute": r"""
       .----------------.
       | [] [] [] [] [] |   NEXT STOP: CAMPUS
       |________________|
          O          O
    =======|======|=======
""",
    "Newtown group-chat pressure": r"""
       .--------------.       ( ( (
       | Dinner?  [3] |      .-----.
       | You: ...     |      |     |)
       '--------------'      '-----'
                           ----------
""",
    "Payday, finally": r"""
          .------------------.
          | BANK    + $180   |
          |   PAYMENT IN!    |
          '------------------'
               *  $  *
""",
    "Laptop versus deadline": r"""
          .----------------.
          |   LOW BATTERY  |
          |      [!]       |
          |________________|
         /__________________\
""",
    "The Bondi invitation": r"""
           \ | /       .-^-.
         --  O  --    /_____\
           / | \        |
      ~~~~~~~~    ~~~~~  |  ~~~~
      ..............___|___....
""",
    "A small refund miracle": r"""
          .----------------.
          | RETURN ACCEPTED|
          |     + $40      |
          '----------------'
             \  (^_^)  /
""",
    "The missing textbook": r"""
          ______   ______
         /      \ /      \
        | STUDY  | WHERE? |
        |        |   ?    |
         \_______|_______/
""",
    "One night off": r"""
        .----------------------.
        | *  CAMPUS SHOW  *    |
        |   ADMIT ONE     :::: |
        '----------------------'
             \  o  /   o
""",
    "The share-house kitchen incident": r"""
              )  )  )
           .----------.
         __| RICE  [!]|__
        (__|          |__)
           '----------'
""",
    "The late-night delivery temptation": r"""
           .-----------.
           |   23:00   |
           | ORDER NOW?|
           |   [YES]   |
           '-----o-----'
""",
    "Marketplace success": r"""
              .------.
              | SOLD |
              |______|
             /________\
             |        |    + $55
""",
    "Rain versus umbrella": r"""
          '  '  '  '  '  '
              .-^-.
            .'_____'.
           /___|_|___\
               |    '  '
               J
""",
}


def section(title):
    """A high-contrast landmark in scrollback; no screen-clearing needed."""
    print("\n\n" + "=" * 68)
    print("  >>> " + title.upper())
    print("=" * 68)


def event_start(number):
    section(f"NEW EVENT {number} / 4")
    stops = [f"[{index}]" if index == number else f" {index} " for index in range(1, 5)]
    print("  YOUR MONTH:  " + " ---- ".join(stops) + "  ---> FINISH")


def event_end(number):
    print("\n" + "-" * 68)
    print(f"  [DONE] EVENT {number} / 4 COMPLETE")
    print("-" * 68)


def card(title, message, art=""):
    """Wrap long text so event cards remain readable in a normal terminal."""
    width = 66
    print("\n+" + "-" * width + "+")
    if art:
        for line in art.strip("\n").splitlines():
            print("| " + line.ljust(width - 2) + " |")
        print("| " + " " * (width - 2) + " |")
    for paragraph in (title.upper(), "", message):
        for line in wrap(paragraph, width - 4) or [""]:
            print("| " + line.ljust(width - 2) + " |")
    print("+" + "-" * width + "+")


def event_card(event):
    card(event.title, event.story, ART.get(event.title, ""))


def welcome():
    print(r"""
                 SYDNEY STUDENT
              SURVIVAL SIMULATOR

                      |        |\
                  |\  |\    |\ | \
                  | \ | \   | \|  \
              ____|__\|__\__|__\___\____
          ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
             Rent paid. Plot twists pending.
    """)
    card("Your mission", "Make it to the end of the month with a plan you can live with. "
         "Four encounters. A few awkward choices. One student wallet.")
    print("Fictional AUD scenarios; ratings are game rules.")


def dashboard(simulation, completed):
    progress = "#" * completed + "." * (4 - completed)
    print(f"\n  +--- WALLET CHECK ----------------------- [{progress}] {completed}/4 ---+")
    print(f"  Wallet buffer : {money(simulation.available):>12}  | {simulation.level}")
    print(f"  Savings       : {money(simulation.savings):>12}")
    print(f"  Reserved fun  : {money(simulation.entertainment):>12}")
    if simulation.available < 0:
        print("  [!] This is an unfunded shortfall, not an automatic loan.")


def ending(simulation):
    endings = {
        "COMFORTABLE": ("THE HARBOUR VIEW", "You reach month-end with breathing room. Your wallet can finally unclench."),
        "STABLE": ("THE STEADY COMMUTER", "You made it through the plot twists with money still unallocated. A quiet win."),
        "CAUTION": ("THE TIGHTROPE WALKER", "You reached month-end, but the buffer is thin. One more surprise could change the ending."),
        "BROKE": ("THE BUDGET CLIFFHANGER", "The plan has unfunded costs. Time for a rewrite before next month's opening scene."),
    }
    title, story = endings[simulation.level]
    section("MONTH'S END / YOUR RESULTS")
    print(r"""
           .-------------------.
       .---|  MONTH COMPLETED  |---.
        \  '-------------------'  /
         '---/   *   *   *   \---'
    """)
    card(title, story)
    dashboard(simulation, 4)
    print("\nYOUR MONTH IN RECEIPTS")
    for index, item in enumerate(simulation.history, 1):
        print(f"  {index}. {item['event']}")
        print(f"     {item['decision']} | event change {money(item['applied_cents'])}")
        if item["transfer_cents"]:
            print(f"     Funding moved: {money(item['transfer_cents'])} (not income)")
    used = simulation.budget.savings - simulation.savings
    released = simulation.budget.expenses["entertainment"] - simulation.entertainment
    print(f"\n  Starting buffer  {money(simulation.budget.remaining)}")
    print(f"  Final buffer     {money(simulation.available)}")
    print(f"  Savings used     {money(used)}")
    print(f"  Fun released     {money(released)}")
    print("\nSOUVENIRS FROM THIS RUN")
    if used == 0 and simulation.budget.savings > 0:
        print("  [VAULT KEEPER] Emergency savings stayed untouched.")
    alternatives = sum(item["action"] == "alternative" for item in simulation.history)
    if alternatives:
        print(f"  [PLAN B EXPLORER] Found a cheaper route {alternatives} time(s).")
    if any(item["action"] == "skip" for item in simulation.history):
        print("  [BOUNDARY SETTER] Said no to an optional extra.")
    print("  [MONTH COMPLETE] Four encounters, one story to tell.")
