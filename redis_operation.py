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
    # 批量只缓存两百条
    if db.session.query(Tag).count() >= 200:
        tags_list = db.session.query(Tag).limit(200).all()
    else:
        tags_list = db.session.query(Tag).all()
    for item in tags_list:
        r.set(item.tag_name, item.tag_type)
    # print(bool(r.get('你好')))


def have_tag(tag_name):
    # 返回是否在关键字中存在
    res = False
    print(f'redis  {tag_name} {bool(r.get(tag_name))}')
    res = bool(r.get(tag_name))

    # 测试全部从sql中查询
    # tag = db.session.query(Tag).filter(Tag.tag_name == tag_name)
    # if tag.count() > 0:
    #     res = True
    # else:
    #     res = False

    return res


# cache_data()
# print(f'测试${r.get("微信")}')
