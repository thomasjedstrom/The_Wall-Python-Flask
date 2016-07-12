from flask import Flask, request, redirect, render_template, session, flash
from mysqlconnection import MySQLConnector
from flask.ext.bcrypt import Bcrypt
import re
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'KeepItSecretKeepItSafe'
mysql = MySQLConnector(app, 'the_wall')

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')
noNumbers = re.compile(r'^[^0-9]+$')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    user_name = request.form['user_name']
    password = request.form['pw']
    user_query = "SELECT * FROM users WHERE user_name = :user_name LIMIT 1"
    query_data = { 'user_name': user_name }
    user = mysql.query_db(user_query, query_data) # user will be returned in a list
    if bcrypt.check_password_hash(user[0]['pw_hash'], password):
        session['name'] = user_name
        return redirect('/wall')
    else:
        flash('Invalid user or password', 'error')
        return redirect('/')

@app.route('/register', methods=['GET', 'POST'])
def register():
    user_name = request.form['user_name']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    email = request.form['email']
    password = request.form['pw']
    confirm_password = request.form['cpw']

    errors = []
    if len(user_name) < 1:
        errors.append('Username must be at least 2 characters')
    else:
        username_query = "SELECT user_name FROM users WHERE user_name = :user_name LIMIT 1"
        query_username = { 'user_name': user_name }
        existencematch = mysql.query_db(username_query, query_username)
        if len(existencematch) != 0:
            errors.append('Username is already taken')
    if (len(first_name) < 2) and (not noNumbers.match(request.form['first_name'])):
        errors.append('First Name must be at least 2 characters and cannot contain numbers')
    if (len(last_name) < 2) and (not noNumbers.match(request.form['last_name'])):
        errors.append('Last Name must be at least 2 characters and cannot contain numbers')
    if not EMAIL_REGEX.match(request.form['email']):
        errors.append('Invalid email address')
    else:
        email_query = "SELECT email FROM users WHERE email = :email LIMIT 1"
        query_email = { 'email': email }
        existencematch = mysql.query_db(email_query, query_email)
        if len(existencematch) != 0:
            errors.append('Email address already in use')
    if len(password) < 7:
        errors.append('Password must be at least 8 characters')
    if password != confirm_password:
        errors.append('Password does not match')

    if len(errors) != 0:
        for each_error in errors:
            flash(each_error, 'error')
            print errors
        return redirect('/')
    else:
        pw_hash = bcrypt.generate_password_hash(password)
        insert_query = "INSERT INTO users (user_name, first_name, last_name, email, pw_hash, created_at, updated_at) VALUES (:user_name, :first_name, :last_name, :email, :pw_hash, NOW(), NOW())"
        query_data = { 'user_name': user_name,
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': email,
                        'pw_hash': pw_hash 
                        }
        mysql.query_db(insert_query, query_data)
        return redirect('/wall')

@app.route('/wall')
def wall():
    post_query = "SELECT messages.message, messages.created_at, users.user_name FROM messages JOIN users ON messages.user_id=users.id"
    all_messages = mysql.query_db(post_query)
    return render_template('wall.html', all_messages=all_messages, name=session['name'])






app.run(debug=True)