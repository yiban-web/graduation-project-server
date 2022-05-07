import json

from tool import db


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
    # 是否盲呼
    blind_call = db.Column(db.INT)

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
            'voiceTags': json.loads(self.voice_tags),
            'blind_call': self.blind_call
        }

    def stats_count(self, floor_score, ceil_score):
        number = db.session.query(File).filter(File.voice_score <= ceil_score, File.voice_score > floor_score)
        return number.count()
