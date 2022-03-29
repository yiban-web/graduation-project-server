import os.path

import eyed3
from flask import request, make_response
import json
import pymysql
from sqlalchemy import func

from file_operation import upload_file, delete, download_file, upload_file_text
from redis_operation import have_tag
from tool import app, db

pymysql.install_as_MySQLdb()


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
    # 音频时长 单位s
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
        file_byte = request.files.get('voiceFile').read()
        voice_url = upload_file(request.values.get('fileName'), file_byte)
        voice_name = request.values.get('fileName')
        duration = get_voice_time_secs(file_byte, '.\\temporary.mp3')
        # print(f'时长 {duration}')
        new_file = File(voice_name, voice_url)
        new_file.voice_duration = duration
        # print(new_file)
        new_file_id = new_file.add()
    except Exception as e:
        code = 0
        msg = "上传失败"
        print(e)
        print()
    finally:
        return json.dumps({
            'code': code,
            'msg': msg,
            'data': {
                'fileId': new_file_id
            }
        })


def get_voice_time_secs(file_data, file_name):
    # 获取文件时长
    # print(file_data)
    with open(file_name, 'wb') as f:
        f.write(file_data)
    voice_file = eyed3.load(file_name)
    secs = int(voice_file.info.time_secs)
    # os.remove(file_name)
    return secs


@app.route('/countGrade', methods=['POST', 'GET'])
# 测试用算分数接口，这里主要是关键字扣分，总分30，每个关键字-2
def count_grade():
    code = 200
    msg = ""
    grade = 0
    data = json.loads(request.data)
    # file_id = request.args.get('id')
    file_id = data['id']
    # noinspection PyBroadException
    try:
        # 这里设置测试用关键字，每出现一个关键字分数-2，实际关键字由LSTM模型学习生成
        test_tags = '财务销账,避税,假证,开票,票'
        illegal_tags = ''
        file = db.session.query(File).filter(File.voice_id == file_id).first()

        # 这里放置测试用的假文本数据地址，实际由机器学习解析语音生成
        file.voice_text_url = '4161c287b86d0550.txt'
        tag_list = test_tags.split(',')
        for item in tag_list:
            if have_tag(item):
                illegal_tags += item+','
                if grade < 30:
                    grade += 2
        file.voice_score = 100 - grade
        # print(f' illegal_tags {illegal_tags}')
        file.voice_tags = illegal_tags[:len(illegal_tags)-1]
        db.session.commit()
    except Exception as e:
        # print(f'错误 {e}')
        code = 0
        msg = '操作失败'
    finally:
        return json.dumps({
            'code': code,
            'msg': msg,
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
    # noinspection PyBroadException
    try:
        file_id = json.loads(request.data)['fileId']
        file = db.session.query(File).filter(File.voice_id == file_id).first()
    except Exception as e:
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
    # noinspection PyBroadException
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
            'code': code,
            'msg': msg,
        })


@app.route('/readTextFile', methods=['POST'])
# 读取文件
def read_text_file():
    file_url = json.loads(request.data)['voiceTextUrl']
    code = 200
    msg = ""
    text = ""
    # noinspection PyBroadException
    try:
        text = download_file(file_url)
    except Exception as e:
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


def record_duration(url):
    # 录入已有声音时长
    path = url
    if os.path.exists(path):
        files = os.listdir(path)
        for i, item in enumerate(files):
            voice_name = item.split('.')[0]
            voice_file = eyed3.load(path + '//' + item)
            secs = int(voice_file.info.time_secs)
            file = db.session.query(File).filter(File.voice_name == item).first()
            file.voice_duration = secs
            db.session.commit()
            print(f'{i} , {secs}')
    else:
        print('空文件夹')


if __name__ == '__main__':
    app.run()

    # cache_data()

    # 负责更新cos内文件
    # upload_folder('D:\毕设语音+文本素材\语音')
    # upload_folder_txt('D:\毕设语音+文本素材\文本\语音转文本\后五十')
    # record_duration('D:\毕设语音+文本素材\语音')
