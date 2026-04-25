
from crawl_bilibili_fav_type import FavMedia
from utils.request_bv_type import BvViewResponseData, BvTagsResponseData


class MediaInfo(FavMedia):
    view: BvViewResponseData
    tags: list[BvTagsResponseData]