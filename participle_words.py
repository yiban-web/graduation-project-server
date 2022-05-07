import json
import re

import jieba

from File import File
from file_operation import client, bucket, text_name

from redis_operation import have_tag
from tool import db


# 本文件进行操作：
# 将cos中的txt文件进行分词，计算分数存入对应的数据库项中

def participle_words(sentence):
    # 语段分词，返回关键字序列
    seg_list = jieba.cut(sentence, cut_all=False)
    res_list = []
    for item in seg_list:
        # 如果相同的关键字只扣一次分数 if words_test(item) and item not in res_list:
        # 如果出现就扣分 if words_test(item)
        if words_test(item) and item not in res_list:
            res_list.append(item)
    return res_list


def words_test(word):
    # 去掉一些语气词、标点、数字序列
    regular = r'([\?|,|.|，|。|？]+)|([0-9]+)|([吧|啊|奥|噢|哦|呢|嘛|要|好|呃|哪|吗|的|嗯|你|我|你们|我们|喂|了|对|是|什么|这]+)'
    res = True
    # print(f"正则判断 ${word} ${re.match(regular,word)}")
    if re.match(regular, word) is not None:
        res = False
    return res


def keys_words_grade(file_name):
    # 读取txt文件内容,返回关键字扣除的分数
    response = client.get_object(
        Bucket=bucket,
        Key=text_name + file_name,
        # Range='bytes=0-100'
    )
    print('文件下载')
    text = ''

    # 返回值类型,{sub_grade:关键字需要减去的分数，illegal_tags:关键字序列}
    class KeyWordsRes:
        def __init__(self, sub_grade, tags, is_blind_call):
            self.sub_grade = sub_grade
            self.illegal_tags = tags
            self.blind_call = is_blind_call

    illegal_tags = []
    words_list = []
    grade = 0
    # 是否盲呼
    blind_call = 0
    for line in response['Body'].get_raw_stream().readlines():
        line = line.strip()
        print(line.decode('ansi', "ignore"))
        text += line.decode('ansi', "ignore")
    words_list.extend(participle_words(text))
    print(f'关键字序列res${words_list}')
    for item in words_list:
        print(item, have_tag(item, 'keyWord'))
        if have_tag(item, 'keyWord'):
            print(item)
            illegal_tags.append({
                'value': item,
                'type': 'keyWord'
            })
            if grade <= 30:
                grade += 2
        if have_tag(item, 'blindCall'):
            blind_call = 1
            illegal_tags.append({
                'value': item,
                'type': 'blindCall'
            })
    print(f"{grade} {blind_call}")
    return KeyWordsRes(grade, json.dumps(illegal_tags, ensure_ascii=False), blind_call)


def processing_batch(floor_id, ceil_id):
    # 批处理，可以输入处理的id范围
    file_list = db.session.query(File).filter(File.voice_id <= ceil_id, File.voice_id >= floor_id)
    for item in file_list:
        time_grade = 0
        res = keys_words_grade(item.voice_text_url)
        keys_grade = res.sub_grade
        if item.voice_duration <= 30:
            time_grade = 30 - item.voice_duration
        item.voice_score = 100 - keys_grade - time_grade
        if res.blind_call == 1:
            item.voice_score -= 40
        item.voice_tags = res.illegal_tags
        item.blind_call = res.blind_call
        db.session.commit()
        print(f'文件关键字分数${item.voice_score}')

# processing_batch(482, 482)
