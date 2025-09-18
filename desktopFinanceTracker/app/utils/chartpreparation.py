import datetime
from database.db import viewAllTransactions

def prepareChartData(user_id, year=None, typeFilter="all"):
    dbTable = viewAllTransactions(user_id)

    if year:
        try:
            dbTable = [row for row in dbTable if datetime.datetime.strptime(row[1], "%d-%m-%Y").year == int(year)]
        except ValueError:
            pass

    if typeFilter != "all":
        dbTable = [row for row in dbTable if row[5] == typeFilter]

    categoryTotals = {}
    categoryTypes = {}

    for row in dbTable:
        category = row[2]
        description = row[3]
        amount = row[4]
        transactionType = row[5]
        key = (category, description)

        if key not in categoryTotals:
            categoryTotals[key] = 0
            categoryTypes[key] = {'income': 0, 'expense': 0}

        categoryTotals[key] += amount
        categoryTypes[key][transactionType] += abs(amount)

    labels = [f"{cat}: {desc}" for (cat, desc) in categoryTotals.keys()]
    netValues = list(categoryTotals.values())
    incomeValues = [categoryTypes[key]['income'] for key in categoryTotals.keys()]
    expenseValues = [categoryTypes[key]['expense'] for key in categoryTotals.keys()]

    return dbTable, labels, netValues, incomeValues, expenseValues