from .. import db

class UserNode(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    host_id = db.Column(db.Integer)
    node_id = db.Column(db.String(36)) #UUID might be applied
    ip_address = db.Column(db.String(36))
    alias = db.Column(db.String(8))
    interval = db.Column(db.Integer)


class UserRecipe(db.Model):
    id = db.Column(db.Integer,primary_key=True,autoincrement=True)
    domain = db.Column(db.String(20))
    template = db.Column(db.String(20))
    start_time = db.Column(db.String(30))
    offset_minutes = db.Column(db.Integer)
    #user_id = db.Column(db.Integer, db.ForeignKey('User.id'))
    user_id = db.Column(db.Integer)
    expired = db.Column(db.Boolean) #empty or "expired"

    def __repr__(self):
        return self.id

class Datarecord(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True, index=True)
    host_id = db.Column(db.Integer)  # ,db.ForeignKey('user.id'))
    time = db.Column(db.String(20))
    place = db.Column(db.String(20))  # where the senser is placed, could be either Reservoir or Ambience
    type = db.Column(db.String(20))  # either sensor or actuater
    name = db.Column(db.String(40))  # type: String;
    value1 = db.Column(db.String(16))
    unit1 = db.Column(db.String(16))
    value2 = db.Column(db.String(16))

    #    unit2 = db.Column(db.String(16))

    def __repr__(self):
        return self.id

    def decodeJson(self, json):
        self.name = json.get("name")





def getUseridByNode(nodeid):
    query_result = db.session.query(UserNode.host_id).filter_by(node_id=nodeid)
    #print("getUseridByNode count", query_result.count())
    if query_result.count():
        return query_result.first().host_id
    else:
        return None