# -*- coding=utf-8
# -*- coding: utf-8 -*-
import json
import re

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import sys
import logging

from const import SECRET_ID, SECRET_KEY, REGION, BUCKET, TEXT_NAME, VOICE_NAME

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.asr.v20190614 import asr_client, models

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


def upload_file_text(file_name: str, body: bytes):
    response = client.put_object(
        Bucket=bucket,
        Key=text_name + file_name,
        Body=body,
        ACL='public-read'
    )
    url = client.get_object_url(
        Bucket=bucket,
        Key=text_name + file_name,
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
    # 读取txt文件内容
    response = client.get_object(
        Bucket=bucket,
        Key=text_name + file_name,
        # Range='bytes=0-100'
    )
    print('文件下载')
    res = ''
    for line in response['Body'].get_raw_stream().readlines():
        line = line.strip()
        res += str(line, 'ANSI') + '\n'
    return res


def download_voice(file_name):
    response = client.get_object(
        Bucket=bucket,
        Key=text_name + file_name,
        # Range='bytes=0-100'
    )
    return response['Body'].get_raw_stream().read()


def creat_change_task(file_url):
    url = "asr.tencentcloudapi.com"
    task_id = 0
    params = {
        "EngineModelType": "16k_zh",
        "ChannelNum": 1,
        "ResTextFormat": 0,
        "SourceType": 0,
        "Url": file_url
    }
    resp = join_SDK(params, 'request')
    task_id = resp.Data.TaskId
    print(resp.Data.TaskId, task_id)
    return task_id


def get_text(url):
    # 语音转文字
    task_id = creat_change_task(url)
    res = ''
    statusStr = ''
    params = {
        "TaskId": task_id
    }
    if task_id == -1:
        return res
    while statusStr != 'success':
        statusStr = join_SDK(params, 'check').Data.StatusStr
        res = join_SDK(params, 'check').Data.Result
    # print(re.sub(r"\[.*\]\s", "", res))
    return re.sub(r"\[.*\]\s", "", res)


def join_SDK(params, join_type):
    try:
        url = "asr.tencentcloudapi.com"
        cred = credential.Credential(secret_id, secret_key)
        httpProfile = HttpProfile()
        httpProfile.endpoint = url
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = asr_client.AsrClient(cred, "", clientProfile)
        if join_type == 'check':
            req = models.DescribeTaskStatusRequest()
            req.from_json_string(json.dumps(params))
            resp = client.DescribeTaskStatus(req)
        if join_type == 'request':
            req = models.CreateRecTaskRequest()
            req.from_json_string(json.dumps(params))
            resp = client.CreateRecTask(req)
        return resp
    except TencentCloudSDKException as err:
        print(err)
        return {
            'Data': {
                'TaskId': -1
            }
        }


# get_text()
