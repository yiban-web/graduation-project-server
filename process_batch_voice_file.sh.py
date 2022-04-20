import os

import eyed3

from File import File
from file_operation import upload_file, upload_file_text
from tool import db


# 负责更新cos内文件
def upload_folder(url: str):
    # 上传本地音频文件夹至cos
    path = url
    if os.path.exists(path):
        files = os.listdir(path)
        for item in files:
            voice_name = item.split('.')[0]
            voice_file = eyed3.load(path + '//' + item)
            secs = int(voice_file.info.time_secs)
            with open(url + '\\' + item, 'rb') as f:
                voice_url = upload_file(voice_name + '.mp3', f.read())
                new_file = File(voice_name + '.mp3', voice_url, secs, 0, voice_name + '.txt', '')
                if db.session.query(File).filter(File.voice_name == voice_name).count() == 0:
                    new_file.add()
    else:
        print('空文件夹')


def upload_folder_txt(url: str):
    # 上传本地txt文件至cos
    path = url
    if os.path.exists(path):
        files = os.listdir(path)
        for item in files:
            voice_name = item.split('.')[0]
            with open(url + '\\' + item, 'rb') as f:
                upload_file_text(voice_name + '.txt', f.read())
    else:
        print('空文件夹')


# upload_folder('D:\毕设语音+文本素材\语音')
# upload_folder_txt('D:\毕设语音+文本素材\文本\语音转文本\后五十')
# record_duration('D:\毕设语音+文本素材\语音')
