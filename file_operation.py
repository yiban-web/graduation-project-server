# -*- coding=utf-8
# -*- coding: utf-8 -*-
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import logging

from const import SECRET_ID, SECRET_KEY, REGION, BUCKET, TEXT_NAME, VOICE_NAME

# 正常情况日志级别使用INFO，需要定位时可以修改为DEBUG，此时SDK会打印和服务端的通信信息
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

# 1. 设置用户属性, 包括 secret_id, secret_key, region等。Appid 已在CosConfig中移除，请在参数 Bucket 中带上 Appid。Bucket 由 BucketName-Appid 组成
secret_id = SECRET_ID  # 替换为用户的 SecretId，请登录访问管理控制台进行查看和管理，https://console.cloud.tencent.com/cam/capi
secret_key = SECRET_KEY  # 替换为用户的 SecretKey，请登录访问管理控制台进行查看和管理，https://console.cloud.tencent.com/cam/capi
region = REGION  # 替换为用户的 region，已创建桶归属的region可以在控制台查看，https://console.cloud.tencent.com/cos5/bucket
# COS支持的所有region列表参见https://cloud.tencent.com/document/product/436/6224
token = None  # 如果使用永久密钥不需要填入token，如果使用临时密钥需要填入，临时密钥生成和使用指引参见https://cloud.tencent.com/document/product/436/14048
scheme = 'https'  # 指定使用 http/https 协议来访问 COS，默认为 https，可不填

config = CosConfig(Region=region, SecretId=secret_id, SecretKey=secret_key, Token=token, Scheme=scheme)
client = CosS3Client(config)

voice_name = VOICE_NAME
text_name = TEXT_NAME
bucket = BUCKET


def upload_file(file_name: str, body: bytes):
    response = client.put_object(
        Bucket=bucket,
        Key=voice_name + file_name,
        Body=body,
        ACL='public-read'
    )
    url = client.get_object_url(
        Bucket=bucket,
        Key=voice_name + file_name,
    )
    print(response)
    return url


def delete(file_name):
    response = client.delete_object(
        Bucket=bucket,
        Key=voice_name + file_name
    )
    print(response)


def download_file(file_name):
    response = client.get_object(
        Bucket=bucket,
        Key=text_name + file_name,
        # Range='bytes=0-100'
    )
    print('文件下载')
    # print(str(response['Body'].get_raw_stream().read(), 'ANSI'))
    res = ''
    for line in response['Body'].get_raw_stream().readlines():  # 依次读取每行
        line = line.strip()  # 去掉每行头尾空白
        res += str(line, 'ANSI') + '\n'
        # print(f'line:{line}')
        #
    return res
