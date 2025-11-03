import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import io
import base64
import numpy as np
import datetime

def generate_prediction_plot(months, actuals, predictions, monthsAmount=12, mse=None):
    months_labels = [datetime.datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in months]
    actuals = np.array(actuals, dtype=float)
    predictions = np.array(predictions if isinstance(predictions, (list, np.ndarray)) else [predictions]).flatten()

    try:
        monthsAmount = int(monthsAmount)
        if monthsAmount < 1:
            monthsAmount = 12
    except (ValueError, TypeError):
        print(f"Invalid monthsAmount provided: {monthsAmount}, defaulting to 12")
        monthsAmount = 12

    if len(months) > monthsAmount:
        filtered_months = months[-monthsAmount:]
        filtered_actuals = actuals[-monthsAmount:]
        months_labels = [datetime.datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in filtered_months]
    else:
        filtered_months = months
        filtered_actuals = actuals
        months_labels = [datetime.datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in months]

    last_month = datetime.datetime.strptime(months[-1], "%Y-%m")
    future_labels = []

    for i in range(len(predictions)):
        future_month = last_month + datetime.timedelta(days=32 * (i + 1))
        future_month = future_month.replace(day=1)
        future_labels.append(future_month.strftime("%b %Y"))

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(18, 9), dpi=150, facecolor="#050505")

    ax.plot(months_labels, filtered_actuals, marker='o', label="Actual expenses", color="#2bff00")
    ax.plot([months_labels[-1]] + future_labels, [actuals[-1]] + list(predictions), marker='o', linestyle="--", color="white", label="Predicted expenses")
    ax.scatter(future_labels, predictions, color="red", zorder=5)

    last_y = None

    for label, pred in zip(future_labels, predictions):
        y_offset = 10
        if last_y is not None and abs(pred - last_y) < 100:
            y_offset += 70
        ax.annotate(f"Predicted: {pred:.2f}", (label, pred), xytext=(0, y_offset), textcoords="offset points", ha="center", va="bottom", color="red", arrowprops=dict(arrowstyle="->", color="#FAA000"))
        last_y = pred

    ax.set_xlabel("Month")
    ax.set_ylabel("Expenses")
    ax.set_title(f"Monthly expenses & predictions" + (f" (Last {monthsAmount} months)" if monthsAmount else ""))
    min_y = min(np.min(filtered_actuals), np.min(predictions)) if len(predictions) > 0 else np.min(filtered_actuals)
    max_y = max(np.max(filtered_actuals), np.max(predictions)) if len(predictions) > 0 else np.max(filtered_actuals)
    ax.set_ylim(min_y * 0, max_y * 1.2)
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.tick_params(axis="x", rotation=45)

    if mse is not None:
        ax.text(0.02, 0.98, f"MSE: {mse:.2f}", transform=ax.transAxes, fontsize=12, verticalalignment='top', bbox=dict(facecolor='black', alpha=0.5))

    fig.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64