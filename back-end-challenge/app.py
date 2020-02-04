from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from bson.json_util import dumps
from bson import ObjectId
from pymongo import MongoClient
import bcrypt
from scraper import * # Web Scraping utility functions for Online Clubs with Penn.
from Club import *
import dns



app = Flask(__name__) #initialize the flask app
app.config['JSON_SORT_KEYS'] = False #don't want to sort the keys, otherwise club description will come first 
app.secret_key = "flask is great!" #This will be the secret that will be used in encryption and decryption


client = MongoClient("mongodb+srv://test-user:test@cluster0-yh4za.mongodb.net/test?retryWrites=true&w=majority") #connect the database, in this case MongoDB Atlas
db = client.get_database('users_clubs') #the database is called users_clubs, and has three collections, one 


#add documents to the database if the collections aren't already initalized 
def initialize():
  club_soups = get_clubs(soupify(get_clubs_html()))
  for club_soup in club_soups:
    new_club = {"name" : get_club_name(club_soup), "tags" : get_club_tags(club_soup), "description" : get_club_description(club_soup) }
    if db.clubs.find_one({"name" : get_club_name(club_soup)}) is not None:
      break;
    else:
      db.clubs.insert_one(new_club)

#this is the index route of the web app front end portion of the assignment
@app.route('/')
def main():
  if session.get('username'):
    result_string = "Welcome to Penn Club Review " + session['username']
    clubs = db.clubs.find({})
    return render_template('main.html', response=result_string, username=session.get('username'), clubs=clubs)
  else:
    result_string = "Welcome to Penn Club Review!"
    return render_template('main.html', response=result_string, username=session.get('username'))

#this is the login route
@app.route('/login', methods = ['POST', 'GET'])
def login():
  if request.method == 'POST':
    users = db.users
    curr_user = users.find_one({'username' : request.form['username']})
    if curr_user:
        if bcrypt.hashpw(request.form['password'].encode('utf-8'), curr_user['password']) == curr_user['password']: #hashes password and compares it to hashed password in the database
           session['username'] = request.form['username']
           return redirect(url_for('main'))                         
    return 'Invalid username/password'
  else:
    return render_template('login.html', username=session.get('username'))

#this is the logout route 
@app.route('/logout')
def logout():
    session.pop('username', None) #pops user from the session
    return render_template('logout.html', logoutMessage="You have logged out!")

#this is the registration route
@app.route('/register', methods = ['POST', 'GET'])
def register():
  if request.method == 'POST':
    users = db.users
    print("this is username: " + request.form['username']);
    existing_user = users.find_one({'username' : request.form['username']})
    if existing_user is None:
      hashedpw = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt()) #hashes the password and stores it within the database
      users.insert({'username' : request.form['username'], 'first_name' : request.form["first_name"],
        'last_name' : request.form['last_name'], 'age' : request.form['age'], 'grad_year' : request.form["year"], 'phone' : request.form['phone']
        , "password" : hashedpw})
      session['username'] = request.form['username']
      return redirect(url_for('main'))    
    return 'This username already exists'
  else: 
    return render_template('register.html', username=session.get('username'))

#goes to the form to add a club
@app.route('/add_club')
def add_club():
    return render_template('newclub.html', username=session.get('username'))

#Goes to the route to add a review
@app.route('/review/<objectid>')
def review_club(objectid):
    current_club = db.clubs.find_one({"_id" : ObjectId(objectid)})
    name = current_club["name"]
    return render_template('addComment.html', username=session.get('username'), object_id=objectid, club_name=name)

#Goes to the club/objectid route to display specific club information (including comments)
@app.route('/clubs/<objectid>', methods = ['POST', 'GET'])
def display_club(objectid):
    if request.method == 'POST':
        review = request.form["review"]
        db.comments.insert({'club_id' : objectid, 'comment' : review})
        return redirect(url_for('display_club', objectid=objectid))
    else:
      current_club = db.clubs.find_one({"_id" : ObjectId(objectid)})
      comments = db.comments.find({"club_id" : objectid}).limit(3)
      print(comments)
      if current_club:
          return render_template('displayclub.html', username=session.get('username'), club=current_club, comments=comments)
      return "there is no club with that id"

########################################################### API ROUTES #############################################################

@app.route('/api')
def api():
  return "Welcome to the Penn Club Review API!."

@app.route('/api/clubs', methods = ['POST', 'GET', 'PUT'])
def displayclubs():
  if request.method == 'POST':  #Post request is used to add a new club. This can be done through a form or through a json request
    if request.form:
      name = request.form["club_name"]
      tags = request.form.getlist("tags")
      desc = request.form["description"]
      new_club = {"name" : name, "tags" : tags, "description" : desc}
      db.clubs.insert_one(new_club)   
      return redirect(url_for('main'))
    elif request.get_json():    #The Json request redirects back to the api display clubs page (where the clubs are displayed in json format)
      data = request.get_json()
      name = data.get("club_name")
      tags = data.get("tags")
      desc = data.get("description")
      new_club = {"name" : name, "tags" : tags, "description" : desc}
      db.clubs.insert_one(new_club)   
      return redirect(url_for('displayclubs'))
  elif request.method == 'GET':           #In the get request, flask gets the clubs from the database and jsonifies them
      clubs_list = dumps(db.clubs.find({}))
      return jsonify(clubs_list)
  elif request.method == 'PUT': #This is used when updating a club
      if request.get_json():
        data = request.get_json()
        original_name = data["original_name"] #finds the specific club using the original name
        new_name = data.get("new_name")     
        new_tags = data.get("new_tags")                  
        new_desc = data.get("new_desc")
        updated_values = {"$set": { "name": new_name, "tags" : new_tags, "description" : new_desc}} #applies the new name, new tags, and new desc
        db.clubs.update_one({"name" : original_name}, updated_values)
      return redirect(url_for('displayclubs'))


@app.route('/api/user/<username>', methods = ['GET']) #gets user data corresponding to the username from the database
def displayUserName(username):
  existing_user = db.users.find_one({'username' : username})
  if existing_user:
    user_string = {"first_name" : existing_user["first_name"], "last_name" : existing_user["last_name"], "grad_year" : existing_user["grad_year"]}
    return jsonify(user_string)
  return jsonify("user not found")
  

@app.route('/api/favorite', methods = ['POST']) #needs a json request to work. Takes in a username and clubname. 
def favorite():
  if request.get_json():
    data = request.get_json()
    user = data['username']
    club_name = data['club_name']
    users = db.users
    clubs = db.clubs
    current_user = users.find_one({"username" : user})
    current_club = clubs.find_one({"name" : club_name})
    if "favorites" in current_user.keys():
        if "favorite_count" in current_club.keys(): 
          favorites_list = current_user["favorites"] #Stores the clubs that have been favorited in a favorite_list array (unique to each user). Used to check if clubs have already been favorited
          if club_name not in favorites_list:
            favorites_list.append(club_name)
            users.update_one({"username" : user}, {"$set" : {"favorites" : favorites_list}})
            clubs.update_one({"name" : club_name}, {"$set" : {"favorite_count" : current_club["favorite_count"] + 1}})
        else:
          favorites_list = current_user["favorites"] 
          if club_name not in favorites_list:
            favorites_list.append(club_name)
            users.update_one({"username" : user}, {"$set" : {"favorites" : favorites_list}})
            clubs.update_one({"name" : club_name}, {"$set" : {"favorite_count" : 1}})
    else:
        if "favorite_count" in current_club.keys():
          favorites_list = []
          favorites_list.append(club_name)
          users.update_one({"username" : user}, {"$set" : {"favorites" : favorites_list}})
          clubs.update_one({"name" : club_name}, {"$set" : {"favorite_count" : current_club["favorite_count"] + 1}})
        else:
          favorites_list = []
          favorites_list.append(club_name)
          users.update_one({"username" : user}, {"$set" : {"favorites" : favorites_list}})
          clubs.update_one({"name" : club_name}, {"$set" : {"favorite_count" : 1}}) #favorite counts are updated correspondingly in each document
  return redirect(url_for('displayclubs')) 

if __name__ == '__main__':
  initialize()
  app.run()