
from typing import TypedDict, List
from typing import Optional, Any


class CommonResponse(TypedDict):
    """
    Response from the request to get the favorite list.
    """
    code: int
    message: str
    ttl: int
    data: dict


class BvViewResponse(CommonResponse):
    """
    A class to represent a view response.
    """
    data: 'BvViewResponseData'


class Dimension(TypedDict):
        width: int
        height: int
        rotate: int


class BvViewResponseData(TypedDict):
    """
    Data from the response to the request to get the favorite list.
    """
    class DescV2Item(TypedDict):
        raw_text: str
        type: int
        biz_id: int

    class Rights(TypedDict):
        bp: int
        elec: int
        download: int
        movie: int
        pay: int
        hd5: int
        no_reprint: int
        autoplay: int
        ugc_pay: int
        is_cooperation: int
        ugc_pay_preview: int
        no_background: int
        clean_mode: int
        is_stein_gate: int
        is_360: int
        no_share: int
        arc_pay: int
        free_watch: int

    class Owner(TypedDict):
        mid: int
        name: str
        face: str

        # Fields for BvViewResponseData
    bvid: str
    aid: int
    videos: int
    tid: int
    tid_v2: int
    tname: str
    tname_v2: str
    copyright: int
    pic: str
    title: str
    pubdate: int
    ctime: int
    desc: str
    desc_v2: List[DescV2Item]
    state: int
    duration: int
    mission_id: int
    rights: Rights
    owner: Owner
    class Stat(TypedDict):
        aid: int
        view: int
        danmaku: int
        reply: int
        favorite: int
        coin: int
        share: int
        now_rank: int
        his_rank: int
        like: int
        dislike: int
        evaluation: str
        vt: int

    class ArgueInfo(TypedDict):
        argue_msg: str
        argue_type: int
        argue_link: str

    class Page(TypedDict):
        cid: int
        page: int
        from_: str  # 'from' is a reserved keyword in Python
        part: str
        duration: int
        vid: str
        weblink: str
        dimension: Dimension
        ctime: int

    class Subtitle(TypedDict):
        allow_submit: bool
        list: List[Any]

    stat: Stat
    argue_info: ArgueInfo
    dynamic: str
    cid: int
    dimension: Dimension
    season_id: int
    premiere: None
    teenage_mode: int
    is_chargeable_season: bool
    is_story: bool
    is_upower_exclusive: bool
    is_upower_play: bool
    is_upower_preview: bool
    enable_vt: int
    vt_display: str
    is_upower_exclusive_with_qa: bool
    no_cache: bool
    pages: List[Page]
    subtitle: Subtitle
    ugc_season: dict
    class UserGarb(TypedDict):
        url_image_ani_cut: str

    is_season_display: bool
    user_garb: UserGarb
    honor_reply: dict
    like_icon: str
    need_jump_bv: bool
    disable_show_up_info: bool
    is_story_play: int
    is_view_self: bool


class BvTagsResponse(CommonResponse):
    """
    A class to represent a tags response.
    """
    data: List['BvTagsResponseData']


class BvTagsResponseData(TypedDict):
    """
    A class to represent a tags response data.
    """
    class Count(TypedDict):
        view: int
        use: int
        atten: int

    tag_id: int
    tag_name: str
    cover: str
    head_cover: str
    content: str
    short_content: str
    type: int
    state: int
    ctime: int
    count: Count
    is_atten: int
    likes: int
    hates: int
    attribute: int
    liked: int
    hated: int
    extra_attr: int