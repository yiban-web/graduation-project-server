import os.path

import requests
from flask import Flask, request, make_response
from flask_sqlalchemy import SQLAlchemy
import json
import pymysql
from sqlalchemy import func

from const import DB_USER, DB_PASSWORD
from file_operation import upload_file, delete, download_file, upload_file_text

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


@app.route('/')
def index():
    return "hello world"


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


@app.route('/register', methods=['POST'])
# 注册接口
def register():
    data = json.loads(request.data)
    code = 200
    msg = ""
    new_user = User(username=data['username'], password=data['password'])
    if new_user.look_up_by_name() != 0:
        code = 0
        msg = "此用户名已注册过，请直接登录"
    else:
        new_user.add()
        msg = "注册成功"
    return json.dumps({
        'code': code,
        'msg': msg
    })


@app.route('/login', methods=['POST'])
# 登录
def login():
    data = json.loads(request.data)
    code = 200
    msg = ""
    new_user = User(username=data['username'], password=data['password'])
    res = make_response()
    res.set_cookie('username', data['username'])
    if new_user.look_up() == 0:
        code = 0
        msg = '用户名或密码不正确'

    return json.dumps({
        'code': code,
        'msg': msg
    })


class File(db.Model):
    __tablename__ = 'voice-files-data'
    voice_name = db.Column(db.CHAR(40))
    voice_id = db.Column(db.INT, primary_key=True, autoincrement=True)
    # 音频时长(目前不知道怎么获取)
    voice_duration = db.Column(db.INT)
    # 分数
    voice_score = db.Column(db.INT)
    # 文本文件地址
    voice_text_url = db.Column(db.VARCHAR(100))
    # 音频地址
    voice_url = db.Column(db.VARCHAR(100))
    # 关键字标签
    voice_tags = db.Column(db.TEXT)

    def __init__(self, name: str, url: str, duration=0, score=0, text_url='', tags=''):
        self.voice_name = name
        self.voice_url = url
        self.voice_duration = duration
        self.voice_text_url = text_url
        self.voice_tags = tags
        self.voice_score = score

    def add(self):
        db.session.add(self)
        db.session.flush()
        # print(f"id  {self.voice_id}")
        db.session.commit()
        return self.voice_id

    def to_dict(self):
        # 列表展示的简略数据
        return {
            'voiceName': self.voice_name,
            # 'voiceUrl': self.voice_url,
            'voiceDuration': self.voice_duration,
            # 'voiceTextUrl': self.voice_text_url,
            'voiceScore': self.voice_score,
            'voiceId': self.voice_id
        }

    def to_dict_detail(self):
        # 文件详细数据
        return {
            'voiceName': self.voice_name,
            'voiceUrl': self.voice_url,
            'voiceDuration': self.voice_duration,
            'voiceTextUrl': self.voice_text_url,
            'voiceScore': self.voice_score,
            'voiceId': self.voice_id,
            'voiceTags': self.voice_tags
        }


@app.route('/upload', methods=['POST'])
# 上传文件
def upload():
    print()
    # print(f"request.files: {request.values.get('fileName')}")
    code = 200
    msg = ""
    try:
        voice_url = upload_file(request.values.get('fileName'), request.files.get('voiceFile').read())
        voice_name = request.values.get('fileName')
        new_file = File(voice_name, voice_url)
        # print(new_file)
        new_file_id = new_file.add()
    except:
        code = 0
        msg = "上传失败"
    finally:
        return json.dumps({
            'code': code,
            'msg': msg,
            'data': {
                'fileId': new_file_id
            }
        })


@app.route('/haveFilesNum', methods=['GET'])
def have_files_num():
    count = db.session.query(func.count('*')).select_from(File).scalar()
    print(count)
    return json.dumps({
        'code': 200,
        'msg': "",
        'data': {
            'fileCount': count
        }
    })


@app.route('/getFilesList', methods=['POST'])
# 查询已有文件
def get_files_list():
    data = json.loads(request.data)
    page = int(data['page'])
    page_size = int(data['pageSize'])
    offset_data = page_size * (page - 1)
    files_list = db.session.query(File).offset(offset_data).limit(page_size)
    res = []
    for item in files_list:
        res.append(item.to_dict())
    # print(res)
    return json.dumps({
        'code': 200,
        'msg': "",
        'data': {
            'filesList': res
        }
    })


@app.route('/getFileDetail', methods=['POST'])
# 根据文件id查找具体内容
def get_file_detail():
    code = 200
    msg = ""
    try:
        file_id = json.loads(request.data)['fileId']
        file = db.session.query(File).filter(File.voice_id == file_id).first()
    except:
        code = 0
        msg = "请求失败"
    finally:
        return json.dumps({
            'code': code,
            'msg': msg,
            'data': {
                'fileData': file.to_dict_detail()
            }
        })


@app.route('/deleteFile', methods=['POST'])
# 删除文件
def delete_file():
    code = 200
    msg = ""
    try:
        file_id = json.loads(request.data)['fileId']
        file = db.session.query(File).filter(File.voice_id == file_id).first()
        delete(file.voice_name)
        db.session.delete(file)
        db.session.commit()
        db.session.close()
    except:
        code = 0
        msg = "删除失败"
    finally:
        return json.dumps({
            'code': 200,
            'msg': "",
        })


@app.route('/readTextFile', methods=['POST'])
# 读取文件
def read_text_file():
    file_url = json.loads(request.data)['voiceTextUrl']
    code = 200
    msg = ""
    text = ""
    try:
        text = download_file(file_url)
    except:
        code = 0
        msg = "文件读取失败"
        text = ""
    finally:
        return json.dumps({
            'code': code,
            'msg': msg,
            'data': {
                'content': text
            }
        })


def upload_folder(url: str):
    path = url
    if os.path.exists(path):
        files = os.listdir(path)
        for item in files:
            voice_name = item.split('.')[0]
            with open(url + '\\' + item, 'rb') as f:
                voice_url = upload_file(voice_name + '.mp3', f.read())
                new_file = File(voice_name + '.mp3', voice_url, 0, 0, voice_name + '.txt', '')
                if db.session.query(File).filter(File.voice_name == voice_name).count() == 0:
                    new_file.add()
    else:
        print('空文件夹')


def upload_folder_txt(url: str):
    path = url
    if os.path.exists(path):
        files = os.listdir(path)
        for item in files:
            voice_name = item.split('.')[0]
            with open(url + '\\' + item, 'rb') as f:
                upload_file_text(voice_name + '.txt', f.read())
    else:
        print('空文件夹')


if __name__ == '__main__':
    app.run()

    # 负责更新cos内文件
    # upload_folder('D:\毕设语音+文本素材\语音')
    # upload_folder_txt('D:\毕设语音+文本素材\文本\语音转文本\后五十')
