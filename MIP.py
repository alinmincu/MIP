from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

# Configurare baza de date
DB_NAME = "expenses.db"

def init_db():
    """Creează sau actualizează baza de date cu noua structură."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Verificăm dacă tabela `expenses` există
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expenses'")
    table_exists = cursor.fetchone()

    if not table_exists:
        # Dacă tabela nu există, o creăm direct
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT,
                type TEXT NOT NULL  -- "expense" sau "income"
            )
        ''')
    else:
        # Dacă tabela există, recreăm structura
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS new_expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT,
                type TEXT NOT NULL  -- "expense" sau "income"
            )
        ''')

        # Copiază datele relevante din tabela veche (fără coloana name)
        cursor.execute('''
            INSERT INTO new_expenses (id, amount, category, type)
            SELECT id, amount, category, type
            FROM expenses
        ''')

        # Șterge tabela veche
        cursor.execute('DROP TABLE expenses')

        # Renumește tabela temporară în tabela originală
        cursor.execute('ALTER TABLE new_expenses RENAME TO expenses')

    conn.commit()
    conn.close()

def calculate_balance():
    """Calculează balance-ul total (income - expenses)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Calculăm totalul veniturilor
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE type = 'income'")
    total_income = cursor.fetchone()[0] or 0
    
    # Calculăm totalul cheltuielilor
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE type = 'expense'")
    total_expense = cursor.fetchone()[0] or 0
    
    conn.close()
    return total_income - total_expense

@app.route('/')
def index():
    """Rădăcina aplicației - afișează toate tranzacțiile și balance-ul."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    conn.close()
    
    balance = calculate_balance()
    return render_template("index.html", expenses=expenses, balance=balance)

@app.route('/add', methods=["GET", "POST"])
def add():
    """Adaugă o nouă tranzacție (income/expense)."""
    if request.method == "POST":
        amount = float(request.form['amount'])
        transaction_type = request.form['type']
        category = request.form['category'] if transaction_type == 'expense' else None

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO expenses (amount, category, type) VALUES (?, ?, ?)", 
                       (amount, category, transaction_type))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    return render_template("add.html")


@app.route('/delete/<int:expense_id>')
def delete(expense_id):
    """Șterge o tranzacție din baza de date."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
