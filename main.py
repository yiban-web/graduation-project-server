import os.path

import eyed3
import jieba
from flask import request, make_response
import json
import pymysql
from sqlalchemy import func

from File import File
from User import User
from file_operation import upload_file, delete, download_file, upload_file_text
from participle_words import keys_words_grade
from redis_operation import have_tag
from test_text import test_voice_change_txt
from tool import app, db

pymysql.install_as_MySQLdb()


@app.route('/')
def index():
    return "hello world"


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


@app.route('/upload', methods=['POST'])
# 上传文件
def upload():
    print()
    # print(f"request.files: {request.values.get('fileName')}")
    code = 200
    msg = ""
    new_file_id = -1
    try:
        file_byte = request.files.get('voiceFile').read()
        voice_url = upload_file(request.values.get('fileName'), file_byte)
        voice_name = request.values.get('fileName')
        duration = get_voice_time_secs(file_byte, '.\\temporary.mp3')
        time_grade = 0
        if duration <= 30:
            time_grade = 30 - duration
        # 以下代码模拟上传文件后转为文字文件，存储到cos
        change_text = test_voice_change_txt
        voice_text_url = voice_name.split('.')[0] + '.txt'
        with open('.\\' + voice_text_url, 'w', encoding='ANSI') as f:
            f.write(change_text)
            print(f'上传文件${f}')
            f.close()
        with open('.\\' + voice_text_url, 'rb') as f:
            upload_file_text(voice_text_url, f.read())
            f.close()

        new_file = File(voice_name, voice_url)
        new_file.voice_text_url = voice_text_url
        new_file.voice_duration = duration
        new_file.voice_score = 100 - time_grade
        new_file_id = new_file.add()
    except Exception as e:
        code = 0
        msg = "上传失败"
        print(e)
        print(msg)
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
        test_tags = '宗教信仰,避税,反人类,开票,票'
        illegal_tags = ''
        file = db.session.query(File).filter(File.voice_id == file_id).first()

        # 这里放置测试用的假文本数据地址，实际由机器学习解析语音生成
        # file.voice_text_url = '4161c287b86d0550.txt'
        # tag_list = test_tags.split(',')

        # 进行分词，返回{应该扣除的分数，关键字字符串}
        res = keys_words_grade(file.voice_text_url)
        # for item in tag_list:
        #     if have_tag(item):
        #         illegal_tags += item + ','
        #         if grade < 30:
        #             grade += 2
        file.voice_score = file.voice_score - res.sub_grade
        file.voice_tags = res.illegal_tags
        db.session.commit()
    except Exception as e:
        print(f'错误 {e}')
        code = 0
        msg = '操作失败'
    finally:
        return json.dumps({
            'code': code,
            'msg': msg,
        })


def participle_words(sentence):
    seg_list = jieba.cut("中国上海是一座美丽的国际性大都市", cut_all=False)
    print("Full Mode: " + "/ ".join(seg_list))


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
# 分页返回已有文件
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


@app.route('/selectFiles', methods=['GET'])
# 查询已有文件
def selectFiles():
    name = request.args.get('name')
    # print(name)
    code = 200
    msg = ""
    files_list = db.session.query(File).filter(File.voice_name.like(f'%{name}%'))
    if files_list.count() >= 10:
        files_list = files_list.limit(10)
        msg = "仅展示十条查询结果"
    res = []
    for item in files_list:
        res.append(item.to_dict())
    return json.dumps({
        'code': code,
        'msg': msg,
        'data': {
            'filesList': res
        }
    })


@app.route('/statsCount', methods=['GET'])
# 返回统计数据
def stats_count():
    code = 200
    msg = ""
    range_list = [[0, 60], [61, 70], [71, 80], [81, 90], [91, 100]]
    range_data = []
    con_data = []
    for item in range_list:

        con = File.stats_count(None,item[0], item[1])
        range_data.append("至".join(str(i) for i in item) + '分')
        con_data.append(con)
    return json.dumps({
        'code': code,
        'msg': '',
        'data': {
            'x': range_data,
            'y': con_data
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


if __name__ == '__main__':
    app.run()
