import datetime
from database.db import viewTransactionsByMonth

def generateFeedMessages(user_id):
    now = datetime.datetime.now()
    this_month = now.month
    this_year = now.year
    last_month = this_month - 1 if this_month > 1 else 12
    last_month_year = this_year if this_month > 1 else this_year - 1

    this_month_rows = viewTransactionsByMonth(this_month, this_year, user_id)
    last_month_rows = viewTransactionsByMonth(last_month, last_month_year, user_id)

    def combine(rows):
        description_totals = {}

        for row in rows:
            description = row[3]
            amount = row[4]
            transaction_type = row[5]
            if transaction_type == "expense":
                description_totals[description] = description_totals.get(description, 0) + abs(amount)
        return description_totals

    this_month_totals = combine(this_month_rows)
    last_month_totals = combine(last_month_rows)

    feed = []
    for description in set(this_month_totals) | set(last_month_totals):
        this_total = this_month_totals.get(description, 0)
        last_total = last_month_totals.get(description, 0)
        if last_total == 0 and this_total > 0:
            feed.append(f"You started spending on {description} this month: {this_total:.2f}€")
        elif last_total > 0:
            change = this_total - last_total
            percent = (change / last_total) * 100 if last_total else 0
            if abs(percent) >= 10:
                more_or_less = "more" if percent > 0 else "less"
                feed.append(f"You have spent {abs(percent):.1f}% {more_or_less} on {description} this month {this_total:.2f}€ compared to last month's {last_total:.2f}€")
    if not feed:
        feed.append("No significant changes in your spending this month.")
    return feed