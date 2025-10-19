import matplotlib.pyplot as plt
from io import BytesIO
import base64
from collections import defaultdict
from decimal import Decimal

def generate_pie_chart(transactions, year):
    category_totals = defaultdict(Decimal)
    for t in transactions:
        if t.type == 'expense':
            category_totals[t.category] += Decimal(t.amount)

    if not category_totals:
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, 'No expense data available', horizontalalignment='center', verticalalignment='center')
        ax.axis('off')
    else:
        labels = list(category_totals.keys())
        sizes = [float(v) for v in category_totals.values()]

        fig, ax = plt.subplots()
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        ax.set_title('Expenses by Category' + (f' ({year})' if year else ''))

    buf = BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')