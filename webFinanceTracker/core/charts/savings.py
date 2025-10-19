import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64
import matplotlib.patheffects as pe
import datetime
import matplotlib.dates as mdates

def generate_savings_chart(transactions, year):
    savings_data = {}
    cumulative_savings = 0
    totalIncome = 0
    totalExpense = 0
    skippedTransactions = []

    transactions = sorted(transactions, key=lambda t: t.date, reverse=False)
    
    for t in transactions:
        try:
            date = t.date
            amount = float(t.amount)
            transactionType = t.type
            date_key = date.strftime("%d-%m-%Y")
        except(ValueError, AttributeError) as e:
            skippedTransactions.append((t, str(e)))
            continue

        if transactionType == 'income':
            cumulative_savings += amount
            totalIncome += amount
        elif transactionType == 'expense':
            cumulative_savings -= abs(amount)
            totalExpense -= abs(amount)
        
        savings_data[date_key] = cumulative_savings

    print(f"Total income: {totalIncome:.2f}")
    print(f"Total expense: {totalIncome:.2f}")
    print(f"Net savings: {cumulative_savings:.2f}")
    print(f"Skipped transactions: {len(skippedTransactions)}")
    if skippedTransactions:
        print("First few skipped transactions:", skippedTransactions[:5])

    dates = sorted(savings_data, key=lambda x: datetime.datetime.strptime(x, "%d-%m-%Y"))
    
    if not dates:
        buf = io.BytesIO()
        plt.figure(figsize=(12, 12))
        plt.text(0.5, 0.5, 'No data to display', ha='center', va='center')
        plt.axis('off')
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
        plt.close()
        image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        buf.close()
        return image_base64
    
    savings_values = [savings_data[date] for date in dates]
    date_objects = [datetime.datetime.strptime(date, "%d-%m-%Y") for date in dates]

    MAX_POINTS = 200 # Change this value to affect the date intervals in the savings chart. Greater value = more data shown
    if len(date_objects) > MAX_POINTS:
        month_last = {}
        for date, value in zip(date_objects, savings_values):
            key = date.strftime("%Y-%m")
            if key not in month_last or date > month_last[key][0]:
                month_last[key] = (date, value)

        date_objects = [value[0] for value in month_last.values()]
        savings_values = [value[1] for value in month_last.values()]
        dates = [date.strftime("%d-%m-%Y") for date in date_objects]
        sorted_pairs = sorted(zip(date_objects, savings_values))
        date_objects, savings_values = zip(*sorted_pairs)

    plt.style.use('dark_background')
    fig = plt.figure(figsize=(18, 9), dpi=120, facecolor="#050505")
    ax = fig.add_subplot(111)
    
    ax.plot(date_objects, savings_values, marker='o', linewidth=2, markersize=4, color="#00FF00")
    ax.set_xlabel("Date")
    ax.set_ylabel("Cumulative Savings (€)")
    ax.set_title(f"Savings Progress Over Time ({year})")
    ax.grid(True, alpha=0.3)
    ax.axhline(y=0, color='#C80000', linestyle='-', alpha=0.5)

    locator = mdates.AutoDateLocator(maxticks=15)
    ax.xaxis.set_major_locator(locator)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    ANNOTATION_LIMIT = 6 # Edit this to affect the amount of markers on the chart.
    for i, (date, value) in enumerate(zip(date_objects, savings_values)):
        if i == 0 or i == len(savings_values) - 1 or value == max(savings_values) or value == min(savings_values) or i % (len(savings_values) // ANNOTATION_LIMIT) == 0:
            ax.annotate(
                f'€{value:,.0f}',
                xy=(date, value),
                xytext=(10, 10),
                textcoords='offset points',
                fontsize=10,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7),
                arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                color="#FF9100",
                weight="bold",
                path_effects=[pe.withStroke(linewidth=3, foreground="#000000")]
            )

    fig.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=120)
    plt.close()
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    buf.close()
    return image_base64