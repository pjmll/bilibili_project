
from typing import Optional, TypedDict

from crawl_bilibili_bv_info import MediaInfo

class PdBvInfo(TypedDict):
    """
    Information about the Bilibili video.
    """
    bvid: Optional[str]  # 视频的 bvid
    title: Optional[str]  # 视频标题
    intro: Optional[str]  # 视频简介
    duration: Optional[int]  # 音频/视频时长
    upper_mid: Optional[int]  # UP 主的 mid
    upper_name: Optional[str]  # UP 主的名称
    view: Optional[int]  # 播放数
    danmaku: Optional[int]  # 弹幕数
    reply: Optional[int]  # 评论数
    favorite: Optional[int]  # 收藏数
    coin: Optional[int]  # 硬币数
    share: Optional[int]  # 分享数
    his_rank: Optional[int]  # 历史最高排名
    like: Optional[int]  # 点赞数
    dislike: Optional[int]  # 点踩数
    evaluation: Optional[str]  # 视频评分
    ctime: Optional[int]  # 投稿时间
    pubtime: Optional[int]  # 发布时间
    fav_time: Optional[int]  # 收藏时间
    tname: Optional[str]  # 分区名称
    tid: Optional[int]  # 分区 ID
    ptname: Optional[str]  # 大分区名称
    dynamic: Optional[str]  # 视频同步发布的的动态的文字内容
    is_upower_exclusive: Optional[bool]  # 是否为充电专属视频
    tags: list[str]  # 视频标签

class TidInfo(TypedDict):
    """
    Information about the Bilibili video.
    """
    tid: Optional[int]  # 视频的 tid
    tname: Optional[str]  # 视频的分区名称
    ptname: Optional[str]  # 视频的大分区名称
    nickname: Optional[str]  # 视频的分区代号
    url: Optional[str]  # 视频的分区链接
    desc: Optional[str]  # 视频的分区简介