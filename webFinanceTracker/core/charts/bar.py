import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

def generate_bar_chart(transactions, year):
    category_totals = {}
    for t in transactions:
        if t.category:
            category_totals[t.category] = category_totals.get(t.category, 0) + float(t.amount)
        else:
            category_totals['Uncategorized'] = category_totals.get('Uncategorized, 0') + float(t.amount)

    labels = list(category_totals.keys())
    values = list(category_totals.values())

    buf = io.BytesIO()

    if not labels:
        print("No categories found, displaying 'No data' message")
        plt.figure(figsize=(12, 12))
        plt.text(0.5, 0.5, 'No data to display', ha='center', va='center', fontsize=12)
        plt.axis('off')
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
    else:
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(18, 9), dpi=120, facecolor="#050505")
        ax = fig.add_subplot(111)

        ax.bar(labels, values, color="orange")
        ax.grid(True, alpha=0.3)
        ax.set_xlabel("Category")
        ax.set_ylabel("Total Amount (€)")
        ax.set_title(f"Total Amount by Category ({year})")
        ax.tick_params(axis="x", rotation=45)

        for i, v in enumerate(values):
            ax.text(i, v + max(values) * 0.01, f'€{v:,.0f}', ha='center', va='bottom')

        fig.tight_layout()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close()

    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    return image_base64