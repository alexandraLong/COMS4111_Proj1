 #!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from pydoc import render_doc
import sqlite3
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response, jsonify

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)
#guesses = ["     ","     ","     ","     ","     "]
num = 0
error = 0
user = ""


# XXX: The Database URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/<DB_NAME>
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# For your convenience, we already set it to the class database

# Use the DB credentials you received by e-mail
DB_USER = "ael2203"
DB_PASSWORD = "databasesZ1!"

DB_SERVER = "w4111.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it
engine.execute("""DROP TABLE IF EXISTS test;""")
engine.execute("""CREATE TABLE IF NOT EXISTS test (
  id serial,
  name text
);""")
engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")

engine.execute("""DROP TABLE IF EXISTS guess CASCADE;""")
engine.execute("""CREATE TABLE IF NOT EXISTS guess (
  numguess int,
  word text
);""")

engine.execute("""DROP TABLE IF EXISTS users CASCADE;""")
engine.execute("""CREATE TABLE IF NOT EXISTS users (
  username text primary key,
  password text,
  birthday date
);""")
engine.execute("""INSERT INTO users(username, password, birthday) VALUES ('ael2203@columbia.edu','wordleZ1','2000-05-22'), ('ala2201@columbia.edu', '12345', '2000-10-15');""")

engine.execute("""DROP TABLE IF EXISTS follows CASCADE;""")
engine.execute("""CREATE TABLE IF NOT EXISTS follows (
  username text,
  username_2 text,
  FOREIGN KEY (username) REFERENCES users(username)
    ON DELETE CASCADE,
  FOREIGN KEY (username_2) REFERENCES users(username)
    ON DELETE CASCADE,
  PRIMARY KEY(username, username_2)
);""")

@app.route('/')
def logon():
  global error
  return render_template('login.html', errorcode = error)

@app.route('/logout')
def logout():
  global user
  user = ""
  return redirect('/')

@app.route('/homepage')
def homepage():
  cursor = g.conn.execute("SELECT word FROM guess")
  guesses = []
  for result in cursor:
    guesses.append(result['word'])  # can also be accessed using result[0]
  cursor.close()

  context = dict(data = guesses)

  return render_template('homepage.html', **context)

@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print("uh oh, problem connecting to database")
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


@app.route('/another')
def another():
  return render_template("anotherfile.html")

@app.route('/addguess', methods=['POST'])
def addguess():
  global num
  guess = request.form['guessinput']
 # print(guess)
  cmd = 'INSERT INTO guess(numguess,word) VALUES (:numg, :g)';
  g.conn.execute(text(cmd), numg = num, g = guess)
  num += 1
  return redirect('/homepage')

@app.route('/login', methods=['POST'])
def login():
  global error
  global user
  error = 0
  email = request.form['email']
  password = request.form['password']
  query = """SELECT password FROM users WHERE username = %s"""
  cursor = g.conn.execute(query, email)
  passes = []
  for result in cursor:
    passes.append(result['password'])
  cursor.close()
  if len(passes) == 0:
    error = 3
    return redirect('/')
  elif result[0] == password:
    user = email
    return redirect('/homepage')
  else:
    error = 2
    return redirect('/')
  

@app.route('/signup')
def signup():
  global error
  return render_template('signin.html', errorcode=error)

@app.route('/signin', methods=['POST'])
def signin():
  global error
  error = 0
  email = request.form['email']
  password = request.form['password']
  birthday = request.form['birthday']
  #print(email)
  #print(password)
  #print(birthday)
  cmd = 'INSERT INTO users(username, password, birthday) VALUES (:user, :passw, :bday)';
  try:
    g.conn.execute(text(cmd), user = email, passw = password, bday = birthday)
  except Exception as er:
    print("Cannot insert username")
    error = 1
    return redirect('/signup')
  return redirect('/homepage')
  
@app.route('/search_users', methods=['POST'])
def search_users():
  search = request.form['searchbar']
  #print(search)
  query1 = """SELECT username FROM users WHERE username LIKE %s"""
  cursor = g.conn.execute(query1, '%'+search+'%')
  profiles = [] 
  for result in cursor:
    profiles.append(result['username'])
  cursor.close()
  #print(profiles)
  return render_template('searchresults.html', profiles = profiles)

@app.route('/profile/<people>')
def view(people):
  #print(people)
  query2 = """SELECT username, birthday FROM users WHERE username = %s"""
  cursor = g.conn.execute(query2, people)
  data = [] 
  for result in cursor:
    data.append(result['username'])
    data.append(result['birthday'])
  cursor.close()
  #print(data)

  return render_template('profile.html',data=data)
  
@app.route('/follow', methods=['POST'])
def follow():
  global user
  user2 = request.form['val']
  print(user2)
  cmd = 'INSERT INTO follows(username,username_2) VALUES (:user1, :usern2)';
  try:
    g.conn.execute(text(cmd), user1 = user, usern2 = user2)
  except Exception as er:
    print("Cannot insert username")
    error = 1
    return redirect('/profile/'+user2)
  return redirect('/homepage')
  
  
if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print("running on %s:%d" % (HOST, PORT))
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
