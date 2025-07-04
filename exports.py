# Export logic

import sqlite3
import os
import csv
import openpyxl
from fpdf import FPDF
from database.db import db_path
from database.db import script_directory

exports_path = os.path.join(script_directory, 'exports')
if not os.path.exists(exports_path):
    os.makedirs(exports_path)

def export_transactions_to_csv():
    connect_to_database = sqlite3.connect(db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('SELECT * FROM transactions')
    rows = db_cursor.fetchall()
    connect_to_database.close()

    filename = input("Enter filename for CSV export (e.g. transactions.csv): ")
    if not filename.endswith('.csv'):
        filename += '.csv'
    filepath = os.path.join(exports_path, filename)

    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';') # ';' is used as the delimiter to make differentiating categories easier.
        writer.writerow(['ID', 'Date', 'Category', 'Description', 'Amount'])
        writer.writerows(rows)
    print(f"Transactions have been exported to {filepath}")

def export_transactions_to_excel():
    connect_to_database = sqlite3.connect(db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('SELECT * FROM transactions')
    rows = db_cursor.fetchall()
    connect_to_database.close()

    filename = input("Enter filename for Excel export (e.g. transactions.xlsx): ")
    if not filename.endswith('xlsx'):
        filename += '.xlsx'
    filepath = os.path.join(exports_path, filename)

    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.append(['ID', 'Date', 'Category', 'Description', 'Amount'])
    for row in rows:
        worksheet.append(row)
    workbook.save(filepath)
    print(f"Transactions have been exported to {filepath}")

def export_transactions_to_pdf():
    connect_to_database = sqlite3.connect(db_path)
    db_cursor = connect_to_database.cursor()
    db_cursor.execute('SELECT * FROM transactions')
    rows = db_cursor.fetchall()
    connect_to_database.close()

    filename = input("Enter filename for PDF export (e.g, transactions.pdf): ")
    if not filename.endswith('.pdf'):
        filename += '.pdf'
    filepath = os.path.join(exports_path, filename)

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Transaction History", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=10)
    headers = ['ID', 'Date', 'Category', 'Description', 'Amount']
    pdf.cell(10, 10, headers[0], 1)
    pdf.cell(30, 10, headers[1], 1)
    pdf.cell(30, 10, headers[2], 1)
    pdf.cell(80, 10, headers[3], 1)
    pdf.cell(30, 10, headers[4], 1)
    pdf.ln()
    for row in rows:
        pdf.cell(10, 10, str(row[0]), 1)
        pdf.cell(30, 10, row[1], 1)
        pdf.cell(30, 10, row[2], 1)
        pdf.cell(80, 10, row[3], 1)
        pdf.cell(30, 10, str(row[4]), 1)
        pdf.ln()
    pdf.output(filepath)
    print(f"Transactions have been exported to {filepath}")