# Flask api for c02 intensity
# Author Sean Hoyal, 2020
#
# miguelgrinberg/REST-auth licensed for use without limitation
# Tutorial loc:
# https://blog.miguelgrinberg.com/post/restful-authentication-with-flask
#
# Modified by Sean Hoyal, 2020
# 
# Imports
import os
import json
import requests
from flask import Flask, request, jsonify, abort, g, url_for
from flask_login import LoginManager, current_user
from cassandra.cluster import Cluster
from flask_sqlalchemy import SQLAlchemy
from passlib.apps import custom_app_context as pwd_context
from flask_httpauth import HTTPBasicAuth
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)

# Initialize cluster connection
cluster = Cluster(contact_points=['18.232.62.164'],port=9042)
session = cluster.connect()

# Initialise app and set configuartion
app = Flask(__name__)
app.config['SECRET_KEY'] = 'foxes in the night have eaten the rasberries'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Extentions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

# Class model for SQLlite, table, with appropriate functions relating to the User.
class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(32), index=True)
	password_hash = db.Column(db.String(64))
	# Use given p/word to generate a hash
	def hash_password(self, password):
		self.password_hash = pwd_context.encrypt(password)
	# Check a given password matches the stored hash against that User.
	def verify_password(self, password):
		return pwd_context.verify(password, self.password_hash)
	# Create a token for a User to access protected endpoints.
	def generate_auth_token(self, expiration=1800):
		s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
		return s.dumps({'id': self.id})
	# Static method to check if the token is valid or expired
	@staticmethod
	def verify_auth_token(token):
		s = Serializer(app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except SignatureExpired:
			return None # Token was valid, but has since expired.
		except BadSignature:
			return None # Token is invalid
		user = User.query.get(data['id'])
		return user # Returns user the token is associated with

@auth.verify_password
def verify_password(username_or_token, password):
	# try to verify by token first
	user = User.verify_auth_token(token)
	# if not, authenticate with username and password
	if not user:
		user = User.query.filter_by(username=username).first()
		if not user or not user.verify_password(password):
			return False
	g.user = user
	return True

# Default home endpoint. Direct user to register.
@app.route('/')
def hello():
	return('<h1>Hello, and welcome to my restful c02 app: Visit /register to register<h1>')

# Route to support registration
@app.route('/user/register', methods=['POST'])
def new_user():
	username = request.json['username']
	password = request.json['password']
	if username is None or password is None:
		abort(400) # Abort is json username or password field is left empty
	if User.query.filter_by(username=username).first() is not None:
		abort(400) # Abort if the username already exists
	user = User(username=username)
	user.hash_password(password)
	db.session.add(user)
	db.session.commit()
	return (jsonify({user.username:'User registered'}), 201,
		{'Location': url_for('get_user', id=user.id, _external=True)})

# Protected endpoint. Requires username&password to get a token.
@app.route('/token', methods=['GET'])
@auth.login_required
def get_auth_token():
	token = g.user.generate_auth_token(1800)
	return jsonify({'token':token.decode('ascii'), 'duration': 1800 }), 200

# Unprotected endpoint to view entries in API
@app.route('/c02/postcodes', methods=['GET'])
def profile():
	tuples = session.execute("""Select * From c02.stats""")
	results = []
	for x in tuples:
		results.append({"regionid":x.regionid,"name":x.name,"postcode":x.postcode,"forecast":x.forecast,"indx":x.indx,"date":x.date})
	return jsonify(results), 200

# Unprotected endpoint to view a specific entry in API
@app.route('/c02/<postcode>', methods=['GET'])
def internal_postcode(postcode):
	results = []
	resp = requests.get(c02_postcode_template.format(pstcd = postcode))
	if not resp.ok:
		abort(404) # Postcode not found
	else:
	tuples = session.execute("""Select * From c02.stats WHERE postcode='{}'""".format(postcode))
		results = []
		for x in tuples:
			results.append({"regionid":x.regionid,"name":x.name,"postcode":x.postcode,"forecast":x.forecast,"indx":x.indx,"date":x.date})
		return jsonify(results), 200

# Unprotected endpoint to retrieve data for a new postcode
@app.route('/new/<postcode>', methods=['GET'])
def external_postcode(postcode):
	resp = requests.get(c02_postcode_template.format(pstcd = postcode))
	if not resp.ok:
		abort(404) # Postcode not found
	else:
		c02 = resp.json()
		return jsonify(c02), 200

# Protected endpoint (token required) to post a new entry to the database
@app.route('/c02/postcode', methods=['POST'])
@auth.login_required
def create():
	postcode = request.json['postcode']
	resp = requests.get(c02_postcode_template.format(pstcd = postcode))
	if not resp.ok:
		abort(404) # Postcode not found
	else:
		session.execute("""INSERT INTO c02.stats(regionid,name,postcode,forecast,indx,date) VALUES({},'{}','{}','{}','{}','{}')""".format(int(request.json['regionid']),request.json['name'],request.json['postcode'],request.json['forecast'],request.json['indx'],request.json['date']))
		return jsonify({'message': 'created: /c02/{}'.format(request.json['postcode'])}), 201

# Protected endpoint (token required) to update an entry in the database
@app.route('/c02/postcode', methods=['PUT'])
@auth.login_required
def update():
	postcode = request.json['postcode']
	resp = requests.get(c02_postcode_template.format(pstcd = postcode))
	if not resp.ok:
		abort(404) # Postcode not found
	else:
		session.execute("""UPDATE c02.stats SET forecast= '{}', indx= '{}', date= '{}' WHERE postcode= '{}'""".format(request.json['forecast'],request.json['indx'],request.json['date'],request.json['postcode']))
		return jsonify({'message': 'updated: /c02/{}'.format(request.json['postcode'])}), 200

# Protected endpoint (token required) to delete an entry from the database
@app.route('/c02/postcode', methods=['DELETE'])
@auth.login_required
def delete():
	postcode = request.json['postcode']
	resp = requests.get(c02_postcode_template.format(pstcd = postcode))
	if not resp.ok:
		abort(404) # Postcode not found
        else:
		session.execute("""DELETE FROM c02.stats WHERE postcode='{}'""".format(request.json['postcode']))
		return jsonify({'message': 'deleted: /c02/{}'.format(request.json['postcode'])}), 200

if __name__ == '__main__':
	# if the SQL db has not previously been initialized, create all
	if not os.path.exists('db.sqlite'):
		db.create_all()
	# Run app on port 80
	app.run(host='0.0.0.0',port=80)

