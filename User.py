from tool import db


class User(db.Model):
    __tablename__ = 'userinfo'
    user_id = db.Column(db.INT, primary_key=True, autoincrement=True)
    username = db.Column(db.CHAR(30), unique=True)
    password = db.Column(db.CHAR(20))

    # 根据username查找
    def look_up_by_name(self):
        res_count = db.session.query(User).filter(User.username == self.username).count()
        return res_count

    def add(self):
        db.session.add(self)
        db.session.commit()

    def look_up(self):
        res_count = db.session.query(User).filter(User.username == self.username
                                                  and User.password == self.password).count()
        return res_count