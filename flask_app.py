from flask import Flask, request, flash, url_for, redirect, render_template
from flask_sqlalchemy import SQLAlchemy
#https://flask-sqlalchemy.palletsprojects.com/en/2.x/quickstart/

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///students.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = "random string"


import folium

db = SQLAlchemy(app)

class user(db.Model):
    id = db.Column('user_id', db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(60))

    def __init__(self, name, email):
        self.name = name
        self.email = email

class quest(db.Model):
    id = db.Column('quest_id', db.Integer, primary_key = True)
    author = db.Column(db.String(100))
    quest_name = db.Column(db.String(100))

    def __init__(self, author, quest_name):
        self.author = author
        self.quest_name = quest_name

#class quest_location(db.Model):
#    id = db.Column('quest_id', db.Integer, primary_key = True)




class students(db.Model):
    id = db.Column('student_id', db.Integer, primary_key = True)
    name = db.Column(db.String(100))
    city = db.Column(db.String(50))
    addr = db.Column(db.String(200))
    pin = db.Column(db.String(10))

    def __init__(self, name, city, addr,pin):
        self.name = name
        self.city = city
        self.addr = addr
        self.pin = pin


@app.route('/')
def index():
     return render_template('index.html' )

@app.route('/map')
def map():
    start_coords = (46.9540700, 142.7360300)
    folium_map = folium.Map(location=start_coords, zoom_start=14)
    return folium_map._repr_html_()


@app.route('/start')
def start():
    db.create_all()
    new_quest = quest(author ='Liam', quest_name = 'UNESCO')
    db.session.add(new_quest)
    db.session.commit()

@app.route('/db')
def show_all():
    return render_template('show_all.html', students = students.query.all() )

@app.route('/new', methods = ['GET', 'POST'])
def new():
    if request.method == 'POST':
        if not request.form['name'] or not request.form['city'] or not request.form['addr']:
            flash('Please enter all the fields', 'error')
        else:
            student = students(request.form['name'], request.form['city'],
                request.form['addr'], request.form['pin'])

            db.session.add(student)
            db.session.commit()
            flash('Record was successfully added')
            return redirect(url_for('show_all'))
    return render_template('new.html')

if __name__ == '__main__':
    db.create_all()
    app.run(debug = True)
