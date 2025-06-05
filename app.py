# app.py
from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime

app = Flask(__name__)

def init_db():
    with sqlite3.connect('survey.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS surveys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                age INTEGER NOT NULL,
                contact_number TEXT NOT NULL,
                favorite_food TEXT,
                rating_watchmovies INTEGER NOT NULL,
                rating_listenradio INTEGER NOT NULL,
                rating_eatout INTEGER NOT NULL,
                rating_watchtv INTEGER NOT NULL
            )
        ''')

def calculate_age(dob_str):
    try:
        birth_date = datetime.strptime(dob_str, '%Y-%m-%d')
        today = datetime.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except:
        return None

def format_contact_number(number):
    return f"{number[:3]}-{number[3:6]}-{number[6:]}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        dob = request.form.get('date')
        contact = request.form.get('contact', '').replace('-', '').strip()
        favorite_foods = request.form.getlist('food')
        fav_food = ', '.join(favorite_foods)

        try:
            rating_watchmovies = int(request.form['rating_watchmovies'])
            rating_listenradio = int(request.form['rating_listenradio'])
            rating_eatout = int(request.form['rating_eatout'])
            rating_watchtv = int(request.form['rating_watchtv'])
        except:
            return "Please answer all the rating questions."

        if not (name and email and dob and contact):
            return "All fields are required."

        if not contact.isdigit() or len(contact) != 10:
            return "Contact number must be exactly 10 digits."

        age = calculate_age(dob)
        if age is None or age < 5 or age > 120:
            return "Age must be between 5 and 120."

        formatted_contact = format_contact_number(contact)

        with sqlite3.connect('survey.db') as conn:
            conn.execute('''
                INSERT INTO surveys 
                (name, email, date_of_birth, age, contact_number, favorite_food,
                 rating_watchmovies, rating_listenradio, rating_eatout, rating_watchtv)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (name, email, dob, age, formatted_contact, fav_food,
                  rating_watchmovies, rating_listenradio, rating_eatout, rating_watchtv))

        return redirect('/results')

    return render_template('index.html')

@app.route('/results')
def results():
    with sqlite3.connect('survey.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM surveys")
        rows = cursor.fetchall()

        if not rows:
            return render_template('results.html', message="No Surveys Available")

        total = len(rows)
        ages = [row[4] for row in rows]
        avg_age = round(sum(ages) / total, 1)
        oldest = max(ages)
        youngest = min(ages)

        pizza_fans = sum(['Pizza' in row[6] for row in rows])
        pasta_fans = sum(['Pasta' in row[6] for row in rows])
        pap_fans = sum(['Pap and Wors' in row[6] for row in rows])

        pizza_percentage = round((pizza_fans / total) * 100, 1)
        pasta_percentage = round((pasta_fans / total) * 100, 1)
        pap_percentage = round((pap_fans / total) * 100, 1)

        avg_eatout = round(sum([row[9] for row in rows]) / total, 1)
        avg_movies = round(sum([row[7] for row in rows]) / total, 1)
        avg_radio = round(sum([row[8] for row in rows]) / total, 1)
        avg_tv = round(sum([row[10] for row in rows]) / total, 1)

        food_counts = {}
        for row in rows:
            foods = row[6].split(', ')
            for food in foods:
                if food:
                    food_counts[food] = food_counts.get(food, 0) + 1

        food_labels = list(food_counts.keys())
        food_data = list(food_counts.values())

        return render_template('results.html',
                               total=total,
                               avg_age=avg_age,
                               oldest=oldest,
                               youngest=youngest,
                               pizza_percent=pizza_percentage,
                               pasta_percent=pasta_percentage,
                               pap_percent=pap_percentage,
                               avg_movies=avg_movies,
                               avg_radio=avg_radio,
                               avg_tv=avg_tv,
                               eatout_avg=avg_eatout,
                               food_labels=food_labels,
                               food_data=food_data)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
