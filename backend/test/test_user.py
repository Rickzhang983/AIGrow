
from flask_sqlalchemy import SQLAlchemy
from flask import Flask




app = Flask("test")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///d:/project/greenway/aigrow/myplot.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = ''
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    username = db.Column(db.String(24))
    mobile = db.Column(db.String(20))
    password = db.Column(db.String(16))
    state = db.Column(db.Integer)


class Datarecord(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    hostid = db.Column(db.Integer, db.ForeignKey('user.id'))
    time = db.Column(db.String(20))
    place = db.Column(db.String(20))  # where the senser is placed, could be either Reservoir or Ambience
    type = db.Column(db.String(20))  # either sensor or actuater
    name = db.Column(db.String(40))  # type: String;
    #event_type = db.Column(db.String(20))  # temperature, humility, rain, light, PH, EC, heater
    value1 = db.Column(db.String(16))
    unit1 = db.Column(db.String(16))
    value2 = db.Column(db.String(16))
    #unit2 = db.Column(db.String(16))

    def __repr__(self):
        return self.id

    def decodeJson(self, json):
        self.name = json.get("name")

users = db.session.query(User).filter_by(username = "Rick")
user = users.first()


print(user)

