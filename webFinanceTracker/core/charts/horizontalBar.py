import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import numpy as np

def generate_horizontalBar_chart(transactions, year):
    topExpenses = {}
    for t in transactions:
        try:
            category = t.category
            description = t.description
            amount = float(t.amount)
            transactionType = t.type
        except(ValueError, AttributeError):
            continue

        if transactionType == 'expense':
            key = f"{category}: {description}"
            if key not in topExpenses:
                topExpenses[key] = 0
            topExpenses[key] += amount

    sortedExpenses = sorted(topExpenses.items(), key=lambda x: x[1], reverse=True)[:5]

    if not sortedExpenses:
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

    descriptions = [item[0] for item in sortedExpenses]
    expenseValues = [abs(item[1]) for item in sortedExpenses]

    y = np.arange(len(descriptions))
    width=0.4

    bars = ax.barh(y, expenseValues, width, align='center', color="red")
    ax.grid(True, alpha=0.3)
    ax.set_yticks(y)
    ax.set_yticklabels(descriptions, fontsize=10, rotation=45)
    ax.invert_yaxis()
    ax.set_xlabel("Expense amount (€)")
    ax.set_title(f"Top 5 Expenses by Category & Description ({year})")

    for i, (bar, value) in enumerate(zip(bars, expenseValues)):
        ax.text(bar.get_width() + max(expenseValues) * 0.01, bar.get_y() + bar.get_height()/2, f'€{value:,.0f}', va='center', fontsize=8)

    fig.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    return image_base64