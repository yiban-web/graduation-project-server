import redis

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import json
import pymysql
from sqlalchemy import func

from const import DB_USER, DB_PASSWORD

pymysql.install_as_MySQLdb()
app = Flask(__name__)


class Config(object):
    """配置参数"""
    # 设置连接数据库的URL
    user = DB_USER
    password = DB_PASSWORD
    database = 'graduation-project'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://%s:%s@127.0.0.1:3306/%s' % (user, password, database)

    # 设置sqlalchemy自动更跟踪数据库
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    # 查询时会显示原始SQL语句
    app.config['SQLALCHEMY_ECHO'] = True

    # 禁止自动提交数据处理
    app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = False


app.config.from_object(Config)
# 创建数据库读取配置
db = SQLAlchemy(app)
r = redis.StrictRedis(host='localhost', port=6379, db=0)


class Tag(db.Model):
    __tablename__ = 'tags-list'
    tag_name = db.Column(db.CHAR(50))
    tag_id = db.Column(db.INT, primary_key=True, autoincrement=True)
    tag_type = db.Column(db.CHAR(30))


def test_redis():
    r.set('foo', 'bar')
    return r.get('foo')


def cache_data():
    # 缓存数据库数据
    tags_list = db.session.query(Tag).all()
    for item in tags_list:
        # tag_key = 'tag' + item.tag_id
        r.set(item.tag_name, item.tag_type)
        print(item.tag_name)
    # print(bool(r.get('你好')))


def have_tag(tag_name):
    # 返回是否在关键字中存在
    res = False
    # print(f'redis  {tag_name} {bool(r.get(tag_name))}')
    if bool(r.get(tag_name)):
        res = True
    else:
        tag = db.session.query(Tag).filter(Tag.tag_name == tag_name)
        if tag.count() > 0:
            r.set(tag.first().tag_name, tag.first().tag_type)
            res = True
        else:
            res = False
    print(f'res {tag_name} {res}')
    return res
