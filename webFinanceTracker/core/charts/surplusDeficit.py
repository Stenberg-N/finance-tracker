import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import io
import base64
import datetime

def generate_surplusDeficit_chart(transactions, year):
    monthly_data = {}

    for t in transactions:
        try:
            date = t.date
            month_key = date.strftime("%m-%Y")
            amount = float(t.amount)
            transactionType = t.type
        except(ValueError, AttributeError):
            continue
        
        if month_key not in monthly_data:
            monthly_data[month_key] = {'income': 0, 'expense': 0}
        
        if transactionType == 'income':
            monthly_data[month_key]['income'] += amount
        elif transactionType == 'expense':
            monthly_data[month_key]['expense'] += abs(amount)

    dates = sorted(monthly_data.keys(), key=lambda x: datetime.datetime.strptime(x, "%m-%Y"))
    
    months = []
    surpluses = []
    colors = []
    labels = [datetime.datetime.strptime(date, "%m-%Y").strftime("%b %Y") for date in dates]
    
    for month in dates:
        data = monthly_data[month]
        months.append(month)
        surplus = data['income'] - data['expense']
        surpluses.append(surplus)
        colors.append('green' if surplus >= 0 else 'red')

    if not months:
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

    bars = ax.bar(months, surpluses, color=colors, alpha=0.7)
    ax.grid(True, alpha=0.3)
    ax.set_xlabel("Month")
    ax.set_ylabel("Surplus/Deficit (€)")
    ax.set_title(f"Monthly Surplus/Deficit Trends ({year})")
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax.set_xticklabels(labels, rotation=45, ha='right')

    for bar, value in zip(bars, surpluses):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + (max(surpluses) * 0.01 if height >= 0 else -abs(min(surpluses)) * 0.01),
                f'€{value:,.0f}', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)

    legend_elements = [Patch(facecolor='green', alpha=0.7, label='Surplus'),
                        Patch(facecolor='red', alpha=0.7, label='Deficit')]
    ax.legend(handles=legend_elements, loc='upper right')

    fig.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    plt.close()
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    return image_base64