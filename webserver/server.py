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
num = 1
error = 0
user = ""
board_id = 1

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

DB_SERVER = "w4111project1part2db.cisxo09blonu.us-east-1.rds.amazonaws.com"

DATABASEURI = "postgresql://"+DB_USER+":"+DB_PASSWORD+"@"+DB_SERVER+"/proj1part2"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


# Here we create a test table and insert some values in it

def get_date():
  date_query = """SELECT DATE('now');"""  
  date_cursor = g.conn.execute(date_query)
  date = []
  for result in date_cursor:
    date.append(result['date'])
  date_cursor.close()
  date = date[0].strftime("%Y-%m-%d")
  return date

def get_current_guesses():
  date = get_date()
  guess_query = """SELECT g.guess FROM guesses_has AS g, games AS b WHERE g.username = %s AND b.date = %s AND g.board_id = b.board_id"""
  guess_cursor = g.conn.execute(guess_query, user, date)
  guesses = []
  for result in guess_cursor:
    guesses.append(result['guess'].upper())  # can also be accessed using result[0]
  guess_cursor.close()
  return guesses

def get_current_word():
    date = get_date()
    today_word_query = """SELECT word FROM games WHERE date = %s"""
    today_word_cursor = g.conn.execute(today_word_query, date)
    t_word = []
    for result in today_word_cursor:
      t_word.append(result['word'])
    today_word_cursor.close()
    t_word = t_word[0]
    return t_word


@app.route('/')
def logon():
  global error
  global user
  return render_template('login.html', errorcode = error, user=user)

@app.route('/logout')
def logout():
  global user
  user = ""
  return redirect('/')

@app.route('/join_squad', methods=['POST'])
def join_squad():
  global user
  global error
  error = 0
  squad = request.form['joinsquad']
  date = get_date()
  cmd = 'INSERT into joins(username,squad_name,date) VALUES (:user, :squad, :date)';
  try:
    g.conn.execute(text(cmd),user=user,squad=squad,date=date)
  except Exception as er:
    #print("Can't join")
    error = 7
  return redirect('/squad/' + squad)
  




@app.route('/squads')
def squads():
  global user
  global error
  return render_template('squads.html', errorcode = error, user=user)

@app.route('/homepage')
def homepage():
  global user
  global board_id
  global error
  win = False
  lost = False
  guesses = get_current_guesses()
  t_word = get_current_word()
  if len(guesses) != 0:
    if guesses[-1] == t_word:
      win = True

  color = []
  for guess in guesses:
    row = []
    for i in range(len(t_word)):
      if guess[i] == t_word[i]:
        row.append((2, guess[i]))
      elif guess[i] in t_word:
        row.append((1, guess[i]))
      else:
        row.append((0, guess[i]))
    color.append(row)
  context = dict(data = guesses)
  if len(guesses) == 6:
    lost = True
    
  share_query = """SELECT username, board_id FROM shares WHERE username_2 = %s"""
  share_cursor = g.conn.execute(share_query, user)

  shared = []
  c = 15
  for result in share_cursor:
    if c == 0:
      break
    else:
      shared.append((result['username'], result['board_id']))
  share_cursor.close()
  return render_template('homepage.html', **context, user = user, win=win, color = color, lost = lost, word = t_word, errorcode = error, shared=shared)

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

@app.route('/squad/<squad>')
def squad(squad):
  global user
  global error
  joins_query = 'SELECT username FROM joins WHERE squad_name = %s'
  joins_cursor = g.conn.execute(joins_query, squad)
  people = []
  for results in joins_cursor:
    people.append(results['username'])
  joins_cursor.close()
  return render_template('squad_profile.html', errorcode=error, people = people, user=user, squad=squad)

@app.route('/attends', methods=['POST'])
def attend():
  global user
  school = request.form['attend']
  school.upper()
  attends_query = 'SELECT name FROM school WHERE name = %s'
  attends_cursor = g.conn.execute(attends_query, school)
  schools = []
  for results in attends_cursor:
    schools.append(results['name'])
  attends_cursor.close()
  if len(schools) == 0:
    cmd = 'INSERT INTO school(school_id,name) VALUES (DEFAULT, :name)';
    g.conn.execute(text(cmd), name = school)
  id_query = 'SELECT school_id FROM school WHERE name = %s'
  id_cursor = g.conn.execute(id_query, school)
  id = []
  for results in id_cursor:
    id.append(results['school_id'])
  id_cursor.close()
  cmd = 'INSERT INTO attends(username, school_id) VALUES (:name, :schoolid)';
  g.conn.execute(text(cmd), name = user, schoolid = id[0])
  return redirect('/profile/'+user)

@app.route('/search_squad', methods=['POST'])
def search_squad():
  global user
  squadsearch = request.form['searchsquad'].upper()
  squad_query = """SELECT squad_name FROM squad WHERE squad_name LIKE %s"""
  squad_cursor = g.conn.execute(squad_query, '%' +squadsearch+ '%')
  squadlist = []
  for results in squad_cursor:
    squadlist.append(results['squad_name'])
  squad_cursor.close()
  return render_template('searchsquads.html', squadlist = squadlist, name = squadsearch, user=user)

@app.route('/makesquad', methods=['POST'])
def makesquad():
  global error
  global user
  error = 0
  squadname = request.form['createsquad'].upper()
  q = """SELECT username FROM joins WHERE username=%s"""
  q_cursor = g.conn.execute(q, user)
  qs = []
  for result in q_cursor:
    qs.append(result['username'])
  if len(qs) > 0:
    error = 5
    return redirect('/squads')

  cmd = 'INSERT INTO squad(squad_name) VALUES (:squad)';
  try:
    g.conn.execute(text(cmd), squad = squadname)
  except Exception as er:
    print("Squad name already exists")
    
    error = 4
    return redirect('/squads')
  date = get_date()
  cmd = 'INSERT INTO joins(username, squad_name, date) VALUES (:user, :squad, :date)';
  g.conn.execute(text(cmd), user = user, squad = squadname, date = date)
  #print(g.conn.execute("""SELECT * FROM joins"""))
  return redirect('/squads')
  
@app.route('/share', methods=['POST'])
def share():
  global error
  global user
  error = 0
  user2 = request.form['share']
  isUser = []
  user_query = """SELECT username FROM users WHERE username = %s"""
  user_cursor = g.conn.execute(user_query, user2)
  for results in user_cursor:
    isUser.append(results['username'])
  user_cursor.close()
  if len(isUser) == 0:
    error = 6
    return redirect('/homepage')
  date = get_date()
  boardid = []
  board_query = """SELECT board_id FROM games WHERE date = %s"""
  board_cursor = g.conn.execute(board_query, date)
  for results in board_cursor:
    boardid.append(results['board_id'])
  board_cursor.close()
  cmd = 'INSERT INTO shares(username, username_2, board_id, time) VALUES (:user1, :user2, :board, :time)';
  g.conn.execute(text(cmd), user1 = user, user2 = user2, board = boardid[0], time = date)
  return redirect('/homepage')

@app.route('/addguess', methods=['POST'])
def addguess():
  global num
  global user
  if num > 5:  
    return redirect('/homepage')
  guesses = get_current_guesses()
  t_word = get_current_word()
  if len(guesses) != 0:
    if guesses[-1] == t_word:
      return redirect('/homepage')
  date = get_date()
  board_query = """SELECT board_id FROM games WHERE date = %s;"""
  board_cursor = g.conn.execute(board_query, date)
  board = []
  for result in board_cursor:
    board.append(result['board_id'])
  board_cursor.close()
  guess = request.form['guessinput']
  if len(guess) != 5:
    return redirect('/homepage')
  num_query = """SELECT max(numguess) as ng FROM guesses_has as gh, games as g WHERE username = %s AND gh.board_id = g.board_id AND g.date = %s;"""
  num_query_cursor = g.conn.execute(num_query,user,date)
  max_num = []
  for result in num_query_cursor:
    max_num.append(result['ng'])
  num_query_cursor.close()
  if max_num[0] == None:
    num = 1
  else:
    num = max_num[0] + 1
  cmd = 'INSERT INTO guesses_has(numguess,guess,username,board_id) VALUES (:numg, :g, :user, :board)';
  g.conn.execute(text(cmd), numg = num, g = guess.upper(), user = user, board = board[0])
  if num == 1:
    cmd = 'INSERT INTO plays(username, board_id) VALUES (:user, :board)';
    g.conn.execute(text(cmd), user = user, board = board[0])

  return redirect('/homepage')
  

@app.route('/login', methods=['POST'])
def login():
  global error
  global user
  global num
  num = 1
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
  global user
  error = 0
  email = request.form['email']
  password = request.form['password']
  birthday = request.form['birthday']
  cmd = 'INSERT INTO users(username, password, birthday) VALUES (:user, :passw, :bday)';
  try:
    g.conn.execute(text(cmd), user = email, passw = password, bday = birthday)
  except Exception as er:
    #print("Cannot insert username")
    error = 1
    return redirect('/signup')
  user = email
  return redirect('/homepage')
  
@app.route('/search_users', methods=['POST'])
def search_users():
  global user
  search = request.form['searchbar']
  query1 = """SELECT username FROM users WHERE username LIKE %s"""
  cursor = g.conn.execute(query1, '%'+search+'%')
  profiles = [] 
  for result in cursor:
    profiles.append(result['username'])
  cursor.close()
  return render_template('searchresults.html', profiles = profiles, user=user)

@app.route('/profile/<people>')
def view(people):
  global user
  caninsert = False
  query2 = """SELECT school_id FROM attends WHERE username = %s"""
  cursor = g.conn.execute(query2, people)
  schools = []
  sname = []
  for result in cursor:
    schools.append(result['school_id'])
  cursor.close()
  if people == user:
    if len(schools) == 0:
      caninsert = True
      sname = []
  if len(schools) != 0:
    query2 = """SELECT name FROM school WHERE school_id = %s"""
    cursor = g.conn.execute(query2, schools[0])
    sname = []
    for result in cursor:
      sname.append(result['name'])
    cursor.close()  
  query2 = """SELECT username, birthday FROM users WHERE username = %s"""
  cursor = g.conn.execute(query2, people)
  data = [] 
  for result in cursor:
    data.append(result['username'])
    data.append(result['birthday'])
  cursor.close()
  puzzles_played = []
  puzzles_completed = []
  total_guesses = []
  played_query = """SELECT COUNT(board_id) AS count FROM plays WHERE username = %s"""
  played_cursor = g.conn.execute(played_query, people)
  for result in played_cursor:
    puzzles_played.append(result['count'])
  played_cursor.close()
  completed_query = """SELECT board_id FROM guesses_has WHERE username=%s AND (guess,board_id) in (SELECT word, board_id FROM GAMES)"""
  completed_cursor = g.conn.execute(completed_query,people)
  for result in completed_cursor:
    puzzles_completed.append(result['board_id'])
  completed_cursor.close()
  total_guesses_query = """SELECT COUNT(*) as count FROM guesses_has WHERE username = %s"""
  total_guesses_cursor = g.conn.execute(total_guesses_query,people)
  for result in total_guesses_cursor:
    total_guesses.append(result['count'])
  total_guesses_cursor.close()
  puzzles_played = puzzles_played[0]
  total_guesses = total_guesses[0]
  todays_puzzle_id_q = """SELECT board_id FROM games WHERE date=%s"""
  todays_cursor = g.conn.execute(todays_puzzle_id_q, get_date())
  todays_id = []
  for result in todays_cursor:
    todays_id.append(result['board_id'])
  counter = todays_id[0]
  streak = 0
  while counter in puzzles_completed:
    streak += 1
    counter -= 1
  followcount = []
  follower_query = """SELECT count(*) as follow FROM follows WHERE username_2 = %s"""
  follower_cursor = g.conn.execute(follower_query, people)
  for results in follower_cursor:
    followcount.append(results['follow'])
  follower_cursor.close()
  if len(puzzles_completed) == 0:
    avg = 0
  else:
    avg = total_guesses/len(puzzles_completed)
  

  return render_template('profile.html',data=data, caninsert=caninsert, sname = sname,user=user, avg=avg, streak=streak, completed=len(puzzles_completed), followers = followcount[0])
  
@app.route('/follow', methods=['POST'])
def follow():
  global user
  user2 = request.form['val']
  cmd = 'INSERT INTO follows(username,username_2) VALUES (:user1, :usern2)';
  try:
    g.conn.execute(text(cmd), user1 = user, usern2 = user2)
  except Exception as er:
    #print("Cannot follow")
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
