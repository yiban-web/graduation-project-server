from main import db


class User(db.Model):
    tableName = 'userinfo'
    user_id = db.Column(db.inspect, primary_key=True, autoincrement=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(30))

    def add(self):
        db.session.add(self)
        db.session.commit()


