
import requests
from retry import retry
from fake_useragent import UserAgent

from utils.request_bv_type import BvViewResponse, BvTagsResponse


@retry()
def get_bv_view(bvid: str) -> BvViewResponse:
    """
    Get the view count of a Bilibili video.
    """
    url = "https://api.bilibili.com/x/web-interface/view"
    params = {
        "bvid": bvid,
    }
    # Use a random User-Agent to avoid being blocked
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return BvViewResponse(**response.json())


@retry()
def get_bv_tags(bvid: str) -> BvTagsResponse:
    """
    Get the tags of a Bilibili video.
    """
    url = "https://api.bilibili.com/x/tag/archive/tags"
    params = {
        "bvid": bvid,
    }
    # Use a random User-Agent to avoid being blocked
    ua = UserAgent()
    headers = {
        "User-Agent": ua.random,
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return BvTagsResponse(**response.json())