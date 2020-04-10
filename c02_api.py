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

cluster = Cluster(contact_points=['54.167.248.218'],port=9042)
session = cluster.connect()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'foxes in the night have eaten the rasberries'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

db = SQLAlchemy(app)
auth = HTTPBasicAuth()

class User(db.Model):
	__tablename__ = 'users'
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(32), index=True)
	password_hash = db.Column(db.String(64))

	def hash_password(self, password):
		self.password_hash = pwd_context.encrypt(password)

	def verify_password(self, password):
		return pwd_context.verify(password, self.password_hash)

	def generate_auth_token(self, expiration=600):
		s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
		return s.dumps({'id': self.id})

	@staticmethod
	def verify_auth_token(token):
		s = Serializer(app.config['SECRET_KEY'])
		try:
			data = s.loads(token)
		except SignatureExpired:
			return None
		except BadSignature:
			return None
		user = User.query.get(data['id'])
		return user

@auth.verify_password
def verify_password(username, password):
	user = User.verify_auth_token(username)
	if not user:
		user = User.query.filter_by(username=username).first()
		if not user or not user.verify_password(password):
			return False
	g.user = user
	return True

@app.route('/')
def hello():
	return('<h1>Hello, and welcome to my restful c02 app: Visit /register to register<h1>')

@app.route('/register', methods=['POST'])
def new_user():
	username = request.json['username']
	password = request.json['password']
	if username is None or password is None:
		abort(400)
	if User.query.filter_by(username=username).first() is not None:
		abort(400)
	user = User(username=username)
	user.hash_password(password)
	db.session.add(user)
	db.session.commit()
	return (jsonify({user.username:'User registered'}), 201,
		{'Location': url_for('get_user', id=user.id, _external=True)})

@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})

@app.route('/token')
@auth.login_required
def get_auth_token():
	token = g.user.generate_auth_token(600)
	return jsonify({'token':token.decode('ascii'), 'duration': 600 })

@app.route('/postcode', methods=['GET'])
def profile():
	tuples = session.execute("""Select * From c02.stats""")
	results = []
	for x in tuples:
		results.append({"regionid":x.regionid,"name":x.name,"postcode":x.postcode,"forecast":x.forecast,"indx":x.indx,"date":x.date})
	return jsonify(results)

@app.route('/<postcode>', methods=['GET'])
def external_postcode(postcode):
	c02_postcode_template = 'https://api.carbonintensity.org.uk/regional/postcode/{pstcd}'
	resp = requests.get(c02_postcode_template.format(pstcd = postcode))
	if resp.ok:
		c02 = resp.json()
		return jsonify(c02)
	else:
		print(resp.reason)

@app.route('/postcode', methods=['POST'])
def create():
	session.execute("""INSERT INTO c02.stats(regionid,name,postcode,forecast,indx,date) VALUES({},'{}','{}','{}','{}','{}')""".format(int(request.json['regionid']),request.json['name'],request.json['postcode'],request.json['forecast'],request.json['indx'],request.json['date']))
	return jsonify({'message': 'created: /record/{}'.format(request.json['postcode'])}), 201

@app.route('/postcode', methods=['PUT'])
@auth.login_required
def update():
	session.execute("""UPDATE c02.stats SET forecast= '{}', indx= '{}', date= '{}' WHERE postcode= '{}'""".format(request.json['forecast'],request.json['indx'],request.json['date'],request.json['postcode']))
	return jsonify({'message': 'updated: /record/{}'.format(request.json['postcode'])}), 200

@app.route('/postcode', methods=['DELETE'])
@auth.login_required
def delete():
	session.execute("""DELETE FROM c02.stats WHERE postcode='{}'""".format(request.json['postcode']))
	return jsonify({'message': 'deleted: /records/{}'.format(request.json['postcode'])}), 200

if __name__ == '__main__':
	if not os.path.exists('db.sqlite'):
		db.create_all()
	app.run(host='0.0.0.0',port=80)

