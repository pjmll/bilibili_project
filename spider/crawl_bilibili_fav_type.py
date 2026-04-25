
from typing import TypedDict

from utils.request_bv_type import CommonResponse


class FavRequestParams(TypedDict):
    """
    Parameters for the request to get the favorite list.
    """
    media_id: int
    pn: int
    ps: int
    order: str
    keyword: str
    type: int
    tid: int
    platform: str
    web_location: str

class FavResponse(CommonResponse):
    """
    Response from the request to get the favorite list.
    """
    data: 'FavResponseData'

class FavResponseData(TypedDict):
    """
    Data from the response to the request to get the favorite list.
    """
    info: 'FavInfo'
    medias: list['FavMedia']
    has_more: bool
    ttl: int

class FavInfo(TypedDict):
    """
    Information about the favorite list.
    """
    id: int
    fid: int
    mid: int
    attr: int
    title: str
    cover: str
    upper: 'FavInfoUpper'
    cover_type: int
    cnt_info: dict
    type: int
    intro: str
    ctime: int
    mtime: int
    state: int
    fav_state: int
    like_state: int
    media_count: int
    is_top: bool

class FavInfoUpper(TypedDict):
    """
    Information about the upper user.
    """
    mid: int
    name: str
    face: str
    followed: bool
    vip_type: int
    vip_statue: int

class FavInfoCntInfo(TypedDict):
    """
    Count information about the favorite list.
    """
    collect: int
    play: int
    thumb_up: int
    share: int

class FavMedia(TypedDict):
    """
    Information about the media in the favorite list.
    """
    id: int
    type: int
    title: str
    cover: str
    intro: str
    page: int
    duration: int
    upper: 'FavInfoUpper'
    attr: int
    cnt_info: 'FavMediaCntInfo'
    link: str
    ctime: int
    pubtime: int
    fav_time: int
    bv_id: str
    bvid: str
    season: None
    ogv: None
    ugc: dict
    media_list_link: str

class FavMediaCntInfo(TypedDict):
    """
    Count information about the media in the favorite list.
    """
    collect: int
    play: int
    danmaku: int
    vt: int
    play_switch: int
    reply: int
    view_text_1: str