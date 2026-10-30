"""Budget model and event simulation. All money is stored as integer cents."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import random


CATEGORIES = ("rent", "food", "transport", "entertainment", "other")


def parse_money(text):
    """Convert non-negative dollars to cents without floating-point rounding."""
    try:
        amount = Decimal(text.strip())
    except InvalidOperation:
        raise ValueError("Enter a number such as 350 or 350.50.") from None
    if not amount.is_finite() or amount < 0 or amount > 1_000_000:
        raise ValueError("Enter an amount between 0 and 1,000,000 dollars.")
    cents = amount * 100
    if cents != cents.to_integral_value():
        raise ValueError("Use no more than two decimal places.")
    return int(cents)


def money(cents):
    """Format integer cents as AUD."""
    sign = "-" if cents < 0 else ""
    dollars, remainder = divmod(abs(cents), 100)
    return f"{sign}${dollars:,}.{remainder:02d}"


@dataclass
class Budget:
    """One month of available funds, separate savings, and planned expenses."""

    funds: int
    savings: int
    expenses: dict
    days: int = 30

    def __post_init__(self):
        if set(self.expenses) != set(CATEGORIES):
            raise ValueError("Provide all five expense categories.")
        values = [self.funds, self.savings, *self.expenses.values()]
        if any(type(value) is not int or value < 0 for value in values):
            raise ValueError("Money values must be non-negative integer cents.")
        if type(self.days) is not int or not 28 <= self.days <= 31:
            raise ValueError("Month length must be between 28 and 31 days.")
        self.expenses = dict(self.expenses)

    @property
    def total(self):
        return sum(self.expenses.values())

    @property
    def remaining(self):
        return self.funds - self.total

    def percentage(self, amount):
        return None if self.funds == 0 else amount / self.funds * 100


@dataclass(frozen=True)
class Event:
    """A hypothetical additional cost or payment, beyond the base budget."""

    title: str
    amount: int
    optional: bool = False
    story: str = ""
    alternative: str = ""
    alternative_cost: int = 0
    consequence: str = ""


EVENTS = (
    Event("The unexpected commute", -5000, story="Your group changes its meeting spot. Those extra trips were not in your Opal budget."),
    Event("Newtown group-chat pressure", -6000, True,
          "'Just a casual dinner,' they said. Then someone shared the menu.",
          "Suggest a shared home-cooked dinner", 1500,
          "You still catch up, but you volunteer for the washing-up."),
    Event("Payday, finally", 18000, story="The extra shift you already worked has finally appeared in your account. Refreshing the app worked!"),
    Event("Laptop versus deadline", -25000, False,
          "Your laptop stops charging. Your assignment, unfortunately, has not stopped being due.",
          "Choose a slower repair service", 12000,
          "The repair takes longer. You finish this week's work on a campus computer."),
    Event("The Bondi invitation", -3500, True,
          "The weather is perfect. Your friends are heading to the beach, with cafe stops planned.",
          "Join, but pack lunch and skip the cafe", 1000,
          "Same ocean, homemade sandwich. You carry the picnic bag all afternoon."),
    Event("A small refund miracle", 4000, story="That returned purchase has finally been refunded. A rare pleasant notification."),
    Event("The missing textbook", -8000, False,
          "Your textbook has vanished right before revision week.",
          "Buy a marked-up second-hand copy", 3000,
          "The previous owner's notes are everywhere. At least the pages are all there."),
    Event("One night off", -2500, True,
          "A campus show offers a break from your assignment tabs.",
          "Meet friends at a free campus activity instead", 0,
          "You miss the show, but still get an evening away from your desk."),
    Event("The share-house kitchen incident", -9000, False,
          "The shared rice cooker breaks. Your agreed share of a replacement is due.",
          "Agree on a basic replacement with your housemates", 4500,
          "Fewer buttons, same rice. Everyone agrees to the cheaper model."),
    Event("The late-night delivery temptation", -3000, True,
          "It is 11 pm. Your assignment has 17 tabs open. The delivery app has one very tempting button.",
          "Cook with groceries already in your food budget", 0,
          "Twenty minutes of cooking, then back to the assignment. No extra grocery cost."),
    Event("Marketplace success", 5500, story="Someone actually turns up to buy the spare desk chair you listed. More space, more cash."),
    Event("Rain versus umbrella", -2000, False,
          "A sudden downpour finishes off your umbrella just before a campus day.",
          "Buy the basic replacement", 800,
          "It is small and plain, but it gets you to class dry."),
)


@dataclass
class Simulation:
    """Reserve base expenses, then apply extra events and funding decisions."""

    budget: Budget
    available: int = field(init=False)
    savings: int = field(init=False)
    entertainment: int = field(init=False)
    history: list = field(default_factory=list, init=False)

    def __post_init__(self):
        self.available = self.budget.remaining
        self.savings = self.budget.savings
        self.entertainment = self.budget.expenses["entertainment"]

    def draw_events(self, seed=None):
        """Include a cost, a social choice and a windfall in every four-event run."""
        rng = random.Random(seed)
        selected = [
            rng.choice([event for event in EVENTS if event.amount < 0 and not event.optional]),
            rng.choice([event for event in EVENTS if event.optional]),
            rng.choice([event for event in EVENTS if event.amount > 0]),
        ]
        selected.append(rng.choice([event for event in EVENTS if event not in selected]))
        rng.shuffle(selected)
        return selected

    def apply(self, event, action="pay", amount=0):
        """Apply one decision. Negative available funds represent a shortfall.

        Savings and entertainment reductions are transfers, not new income.
        A funding amount can cover this event and any existing shortfall.
        Invalid decisions leave the simulation unchanged.
        """
        if event.amount >= 0:
            if action != "pay" or amount != 0:
                raise ValueError("Income events are received automatically.")
        else:
            if action not in ("pay", "skip", "savings", "reduce", "alternative"):
                raise ValueError("Unknown decision.")
            if action == "skip" and not event.optional:
                raise ValueError("An essential cost cannot be skipped.")
            if action == "alternative" and not event.alternative:
                raise ValueError("This event has no alternative.")
            if action in ("pay", "skip", "alternative") and amount != 0:
                raise ValueError("This decision does not use a transfer.")
            if action in ("savings", "reduce"):
                limit = self.savings if action == "savings" else self.entertainment
                if type(amount) is not int or not 0 < amount <= limit:
                    raise ValueError("The transfer must be positive and within its balance.")
                if action == "savings":
                    self.savings -= amount
                else:
                    self.entertainment -= amount
                self.available += amount
        change = 0 if action == "skip" else event.amount
        if action == "alternative":
            change = -event.alternative_cost
        self.available += change
        self.history.append({
            "event": event.title, "event_cents": event.amount,
            "action": action, "transfer_cents": amount,
            "applied_cents": change, "available_cents": self.available,
            "savings_cents": self.savings,
            "decision": event.alternative if action == "alternative" else action,
        })

    @property
    def level(self):
        """Project-defined labels based on unallocated funds, excluding savings."""
        if self.available < 0:
            return "BROKE"
        if self.budget.funds == 0 or self.available < self.budget.funds * 0.05:
            return "CAUTION"
        if self.available < self.budget.funds * 0.20:
            return "STABLE"
        return "COMFORTABLE"

    def report(self):
        return {
            "funds_cents": self.budget.funds,
            "initial_savings_cents": self.budget.savings,
            "planned_expenses_cents": dict(self.budget.expenses),
            "days": self.budget.days,
            "initial_remaining_cents": self.budget.remaining,
            "final_available_cents": self.available,
            "final_savings_cents": self.savings,
            "entertainment_released_cents": (
                self.budget.expenses["entertainment"] - self.entertainment
            ),
            "level": self.level,
            "events": list(self.history),
        }
