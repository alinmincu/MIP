from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3

app = Flask(__name__)
app.secret_key = "1234"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DB_NAME = "expenses.db"

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return User(id=user[0], username=user[1])
    return None

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL NOT NULL,
            category TEXT,
            type TEXT NOT NULL,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

def calculate_balance(user_id):
    """Calculează balance-ul total pentru utilizatorul curent."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE type = 'income' AND user_id = ?", (user_id,))
    total_income = cursor.fetchone()[0] or 0
    
    cursor.execute("SELECT SUM(amount) FROM expenses WHERE type = 'expense' AND user_id = ?", (user_id,))
    total_expense = cursor.fetchone()[0] or 0
    
    conn.close()
    return total_income - total_expense

def calculate_totals(user_id):
    """Calculează totalurile pentru income și expenses pentru utilizatorul curent."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(amount) FROM expenses WHERE type = 'income' AND user_id = ?", (user_id,))
    total_income = cursor.fetchone()[0] or 0

    cursor.execute("SELECT SUM(amount) FROM expenses WHERE type = 'expense' AND user_id = ?", (user_id,))
    total_expenses = cursor.fetchone()[0] or 0

    conn.close()
    return total_income, total_expenses

@app.route('/')
@login_required
def index():
    """Pagina principală."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses WHERE user_id = ?", (current_user.id,))
    expenses = cursor.fetchall()
    conn.close()
    
    total_income, total_expenses = calculate_totals(current_user.id)
    
    balance = total_income - total_expenses
    
    return render_template("index.html", expenses=expenses, balance=balance, total_income=total_income, total_expenses=total_expenses)



@app.route('/add', methods=["GET", "POST"])
@login_required
def add():
    """Adaugă o nouă tranzacție."""
    if request.method == "POST":
        try:
            amount = float(request.form['amount']) 
            transaction_type = request.form['type']  
            category = request.form['category'] if transaction_type == 'expense' else None 
            
            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO expenses (amount, category, type, user_id) VALUES (?, ?, ?, ?)",
                           (amount, category, transaction_type, current_user.id))
            conn.commit()
            conn.close()
            return redirect(url_for('index'))
        except Exception as e:
            return f"An error occurred: {e}", 400
    return render_template("add.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            login_user(User(id=user[0], username=user[1]))
            return redirect(url_for('index'))
        return "Invalid credentials", 401
    return render_template("login.html")

@app.route('/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already exists."
    return render_template("register.html")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
