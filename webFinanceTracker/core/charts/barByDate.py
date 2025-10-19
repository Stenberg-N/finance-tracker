import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
import datetime

def generate_barByDate_chart(transactions, year):
    date_data = {}

    for t in transactions:
        try:
            date_obj = t.date
            month_key = date_obj.strftime("%m-%Y")
            transaction_type = t.type
            amount = float(t.amount)
        except(ValueError, AttributeError):
            continue

        if month_key not in date_data:
            date_data[month_key] = {'income': 0, 'expense': 0}
        date_data[month_key][transaction_type] += amount

    dates = sorted(date_data.keys(), key=lambda x: datetime.datetime.strptime(x, "%m-%Y"))

    if not dates:
        buf = io.BytesIO()
        plt.figure(figsize=(12, 12))
        plt.text(0.5, 0.5, 'No transactions for this year', ha='center', va='center', fontsize=12)
        plt.axis('off')
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()
        return image_base64

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(18, 9), dpi=120, facecolor="#050505")
    ax = fig.add_subplot(111)

    labels = [datetime.datetime.strptime(date, "%m-%Y").strftime("%b %Y") for date in dates]
    income_values = [date_data[date]['income'] for date in dates]
    expense_values = [abs(date_data[date]['expense']) for date in dates]

    x = np.arange(len(dates))
    width = 0.4

    bars_income = ax.bar(x, income_values, width, label="Income", color="green", alpha=0.7)
    bars_expense = ax.bar(x, [-exp for exp in expense_values], width, label="Expense", color="red", alpha=0.7)

    ax.set_xlabel("Date")
    ax.set_ylabel("Amount (€)")
    ax.set_title(f"Income vs. Expense by Month ({year})")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45, ha='right')
    ax.legend(loc="upper right")
    ax.grid(True, alpha=0.3)

    for i, (income, expense) in enumerate(zip(income_values, expense_values)):
        if income > 0:
            ax.text(i, income + max(income_values) * 0.01, f'€{income:,.0f}', ha='center', va='bottom', fontsize=8)
        if expense > 0:
            ax.text(i, -expense - max(expense_values) * 0.01, f'€{expense:,.0f}', ha='center', va='bottom', fontsize=8)

    fig.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    return image_base64