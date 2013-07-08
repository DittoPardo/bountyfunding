
from flask.ext.sqlalchemy import SQLAlchemy
from gang_api import app, GANG_HOME
from utils import Enum 
from os import path
#import logging

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + path.join(GANG_HOME, 'db', 'test.db')
db = SQLAlchemy(app)

#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

class Issue(db.Model):
	issue_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer)
	issue_ref = db.Column(db.String(256))
	status = db.Column(db.Integer)

	class Status(Enum):
		NEW = 10
		ASSIGNED = 20
		COMPLETED = 30
		DELETED = 90

	def __init__(self, project_id, issue_ref):
		self.project_id = project_id
		self.issue_ref = issue_ref
		self.status = Issue.Status.NEW

	def __repr__(self):
		return '<Issue project_id: "%s", issue_ref: "%s">' % self.project_id, self.issue_ref

class User(db.Model):
	user_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer)
	name = db.Column(db.String(256))

	def __init__(self, project_id, name):
		self.project_id = project_id
		self.name = name

	def __repr__(self):
		return '<User project_id: "%s", name: "%s">' % self.project_id, self.nae

class Sponsorship(db.Model):
	sponsorship_id = db.Column(db.Integer, primary_key=True)
	issue_id = db.Column(db.Integer, db.ForeignKey(Issue.issue_id))
	user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))
	amount = db.Column(db.Integer)
	status = db.Column(db.Integer)

	user = db.relation(User, lazy="joined")
	
	class Status(Enum):
		PLEDGED = 10
		CONFIRMED = 20
		VALIDATED = 30

	def __init__(self, issue_id, user_id, amount=0):
		self.issue_id = issue_id
		self.user_id = user_id
		self.amount = amount
		self.status = Sponsorship.Status.PLEDGED

	def __repr__(self):
		return '<Sponsorship issue_id: "%s", user_id: "%s">' % (self.issue_id, self.user_id)
	
class Email(db.Model):
	email_id = db.Column(db.Integer, primary_key=True)
	project_id = db.Column(db.Integer)
	user_id = db.Column(db.Integer, db.ForeignKey(User.user_id))
	subject = db.Column(db.String(128))
	body = db.Column(db.String(1024))

	user = db.relation(User, lazy="joined")
	
	def __init__(self, project_id, user_id, subject, body):
		self.project_id = project_id
		self.user_id = user_id
		self.subject = subject
		self.body = body

	def __repr__(self):
		return '<Email project_id: "%s", user_id: "%s", subject: "%s">' %\
				(self.project_id, self.user_id, self.subject)

