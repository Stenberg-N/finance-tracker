import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import numpy as np
import datetime

def generate_monthlyCategorySplit_chart(transactions, year):
    month_catdesc_expense = {}
    expense_rows = [t for t in transactions if t.type == 'expense']

    for t in expense_rows:
        try:
            date = t.date
            category = t.category
            description = t.description
            amount = abs(float(t.amount))
            month_key = date.strftime("%b %Y")
        except(ValueError, AttributeError):
            continue

        key = (category, description)
        if month_key not in month_catdesc_expense:
            month_catdesc_expense[month_key] = {}
        if key not in month_catdesc_expense[month_key]:
            month_catdesc_expense[month_key][key] = 0
        month_catdesc_expense[month_key][key] += amount

    all_months = sorted(month_catdesc_expense.keys(), key=lambda x: datetime.datetime.strptime(x, "%b %Y"))

    if not all_months:
        buf = io.BytesIO()
        plt.figure(figsize=(12, 12))
        plt.text(0.5, 0.5, 'No data to display', ha='center', va='center')
        plt.axis('off')
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()
        return image_base64
    
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(18, 9), dpi=120, facecolor="#050505")
    ax = fig.add_subplot(111)

    all_catdesc = set()
    for v in month_catdesc_expense.values():
        all_catdesc.update(v.keys())
    all_catdesc = sorted(list(all_catdesc))
    data = {catdesc: [month_catdesc_expense.get(month, {}).get(catdesc, 0) for month in all_months] for catdesc in all_catdesc}
    bottom = np.zeros(len(all_months))
    colors = plt.cm.tab20(np.linspace(0, 1, len(all_catdesc)))

    bars = []
    for i, catdesc in enumerate(all_catdesc):
        values = data[catdesc]
        bar = ax.bar(all_months, values, bottom=bottom, label=f"{catdesc[0]}: {catdesc[1]}", color=colors[i % len(colors)])
        bars.append(bar)
        bottom += np.array(values)

    if len(bottom) > 0:
        max_y = max(bottom)
        ax.set_ylim(0, max_y * 1.05)

    ax.grid(True, alpha=0.3)
    ax.set_xlabel("Month")
    ax.set_ylabel("Expense Amount (€)")
    ax.set_title("Monthly Expenses by Category & Description")
    ax.tick_params(axis="x", rotation=45)
    ax.legend(loc="best", fontsize=9, bbox_to_anchor=(0.98, 1), borderaxespad=0.)

    fig.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
    plt.close()
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    return image_base64