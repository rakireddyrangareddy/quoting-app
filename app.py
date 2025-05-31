from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize the database
def init_db():
    with sqlite3.connect('database.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            material TEXT,
            part_size REAL,
            quantity INTEGER,
            cycle_time REAL,
            delivery_zip TEXT,
            quote_value REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

# Call DB init
init_db()

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('database.db') as conn:
            try:
                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                return redirect(url_for('login'))
            except sqlite3.IntegrityError:
                return render_template('register.html', error="Username already exists")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect('database.db') as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM users WHERE username=? AND password=?", (username, password))
            user = cur.fetchone()
            if user:
                session['user_id'] = user[0]
                session['username'] = username
                return redirect(url_for('quote_form'))
            else:
                return render_template('login.html', error="Invalid username or password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/quote', methods=['GET', 'POST'])
def quote_form():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        material = request.form['material']
        part_size = float(request.form['part_size'])
        quantity = int(request.form['quantity'])
        cycle_time = float(request.form['cycle_time'])
        delivery_zip = request.form['delivery_zip']

        # Injection molding cost formula (example logic)
        setup_cost = 100
        machine_rate = 0.5  # cost per second
        material_cost_per_cm3 = 0.1
        packaging_cost = 0.05 * quantity

        material_cost = material_cost_per_cm3 * part_size * quantity
        processing_cost = machine_rate * cycle_time * quantity

        total_cost = setup_cost + material_cost + processing_cost + packaging_cost

        # Save quote in DB
        with sqlite3.connect('database.db') as conn:
            conn.execute('''INSERT INTO quotes (user_id, material, part_size, quantity, cycle_time, delivery_zip, quote_value)
                            VALUES (?, ?, ?, ?, ?, ?, ?)''',
                         (session['user_id'], material, part_size, quantity, cycle_time, delivery_zip, total_cost))

        return f"<h3>Your Quote is: ${total_cost:.2f}</h3><br><a href='/quote'>Request New Quote</a>"

    return render_template('quote.html')
@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    with sqlite3.connect('database.db') as conn:
        cur = conn.cursor()
        cur.execute('''SELECT material, part_size, quantity, cycle_time, delivery_zip, quote_value, timestamp
                       FROM quotes WHERE user_id = ? ORDER BY timestamp DESC''', (session['user_id'],))
        quotes = cur.fetchall()

    return render_template('history.html', quotes=quotes)

if __name__ == '__main__':
    app.run(debug=True)