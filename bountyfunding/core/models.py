from flask.ext.sqlalchemy import SQLAlchemy
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash

from bountyfunding.core.const import SponsorshipStatus, PaymentStatus, PaymentGateway
from bountyfunding.core.config import config
from bountyfunding.core.errors import Error


db = SQLAlchemy()


class Project(db.Model):
    project_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(1024), nullable=False)
    type = db.Column(db.Integer, nullable=False)

    def __init__(self, name, description, type):
        self.name = name
        self.description = description
        self.type = type

    def __repr__(self):
        return '<Project project_id: "%s", name: "%s">' % (self.project_id, self.name)
    
    def is_mutable(self):
        return True


class Account(db.Model):
    account_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)

    users = db.relation("User", lazy="joined")
    
    def __init__(self, email, name, password=None):
        self.email = email
        self.name = name
        self.password = password

    def get_user(self, project_id):
        for user in self.users:
            if user.project_id == project_id:
                return user
        return None

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.account_id)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        if password == None:
            self.password_hash = None
        else:
            self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        if password == None or self.password_hash == None:
            return False
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<Account email: "%s">' % (self.email,)

db.Index('idx_account_email', Account.email, unique=True)


class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(256), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey(Account.account_id), nullable=True)

    #TODO: move to Account
    paypal_email = db.Column(db.String(256), nullable=True)

    def __init__(self, project_id, name):
        self.project_id = project_id
        self.name = name
        paypal_email = None

    def __repr__(self):
        return '<User project_id: "%s", name: "%s">' % (self.project_id, self.name)

db.Index('idx_user_project_id_account_id', User.project_id, User.account_id, unique=True)
db.Index('idx_user_account_id', User.account_id, unique=False)


class Issue(db.Model):
    issue_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    issue_ref = db.Column(db.String(256), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(1024), nullable=False)
    link = db.Column(db.String(1024), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=True)

    owner = db.relation(User, lazy="joined")
    
    def __init__(self, project_id, issue_ref, status, title, link, owner_id):
        self.project_id = project_id
        self.issue_ref = issue_ref
        self.status = status
        self.title = title
        self.link = link
        self.owner_id = owner_id

    def __repr__(self):
        return '<Issue project_id: "%s", issue_ref: "%s">' % (self.project_id, self.issue_ref)

    @property
    def full_link(self):
        return config[self.project_id].TRACKER_URL + self.link

class Sponsorship(db.Model):
    sponsorship_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    issue_id = db.Column(db.Integer, db.ForeignKey(Issue.issue_id), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Integer, nullable=False)

    #TODO: change nullable to False
    account_id = db.Column(db.Integer, db.ForeignKey(Account.account_id), nullable=True)
    account = db.relation(Account, lazy="joined")

    #TODO: delete
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=True)
    user = db.relation(User, lazy="joined")
    
    def __init__(self, project_id, issue_id, user_id=None, account_id=None, amount=0):
        if user_id == None and account_id == None:
            raise Error("account_id or user_id must be provided") 

        self.project_id = project_id
        self.issue_id = issue_id
        self.user_id = user_id
        self.account_id = account_id
        self.amount = amount
        self.status = SponsorshipStatus.PLEDGED

    def __repr__(self):
        return '<Sponsorship issue_id: "%s", user_id: "%s">' % (self.issue_id, self.user_id)
    
class Payment(db.Model):
    payment_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    sponsorship_id = db.Column(db.Integer, db.ForeignKey(Sponsorship.sponsorship_id), nullable=False)
    gateway_id = db.Column(db.String)
    url = db.Column(db.String)
    status = db.Column(db.Integer, nullable=False)
    gateway = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, nullable=False)

    def __init__(self, project_id, sponsorship_id, gateway):
        self.project_id = project_id
        self.sponsorship_id = sponsorship_id
        self.gateway = gateway
        self.gateway_id = ''
        self.url = ''
        self.status = PaymentStatus.INITIATED
        self.timestamp = datetime.now()

    def __repr__(self):
        return '<Payment payment_id: "%s">' % (self.payment_id,)

class Email(db.Model):
    email_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey(User.user_id), nullable=False)
    issue_id = db.Column(db.Integer, db.ForeignKey(Issue.issue_id), nullable=False)
    body = db.Column(db.String(1024))

    user = db.relation(User, lazy="joined")
    issue = db.relation(Issue, lazy="joined")
    
    def __init__(self, project_id, user_id, issue_id, body):
        self.project_id = project_id
        self.user_id = user_id
        self.issue_id = issue_id
        self.body = body

    def __repr__(self):
        return '<Email project_id: "%s", user_id: "%s", issue_id: "%s">' %\
                (self.project_id, self.user_id, self.issue_id)

class Config(db.Model):
    config_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    value = db.Column(db.String(256), nullable=False)
    
    def __init__(self, project_id, name, value):
        self.project_id = project_id
        self.name = name
        self.value = value

    def __repr__(self):
        return '<Config %s-%s: "%s">' % (self.project_id, self.name, self.value)

db.Index('idx_config_pid_name', Config.project_id, Config.name, unique=True)

class Change(db.Model):
    change_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    method = db.Column(db.String(10), nullable=False)
    path = db.Column(db.String(256), nullable=False)
    arguments = db.Column(db.Text(), nullable=False)
    status = db.Column(db.Integer, nullable=True)
    response = db.Column(db.String(4096), nullable=True)

    def __init__(self, project_id, method, path, arguments):
        self.project_id = project_id
        self.timestamp = datetime.now()
        self.method = method
        self.path = path
        self.arguments = arguments

    def __repr__(self):
        return '<Change change_id: "%s"' % (self.change_id,)

class Token(db.Model):
    token_id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey(Project.project_id), nullable=False)
    token = db.Column(db.String(64), nullable=False)
    
    def __init__(self, project_id, token):
        self.project_id = project_id
        self.token = token

    def __repr__(self):
        return '<Token project_id: "%s", token: "%s">' % (self.project_id, self.token)

db.Index('idx_token_token', Token.token, unique=True)

