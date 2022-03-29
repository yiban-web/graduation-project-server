import redis

import pymysql

from tool import db

pymysql.install_as_MySQLdb()


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
        r.set(item.tag_name, item.tag_type)
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
