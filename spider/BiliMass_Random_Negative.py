"""
B站负样本采集脚本
从B站各细分分区采集普通视频作为负样本（标签为0）用于破圈潜力预测
通过随机采样全站细分分区的最新视频，确保样本的多样性和代表性
"""

import requests
import time
import os
import json
import random
from retry import retry

MY_COOKIE = "buvid3=BF196175-C69E-75FC-5A09-4CB287C1CBB411863infoc; b_nut=1763606811; _uuid=F3BB7FB3-C6CD-4410E-263D-B478B16C8BC611771infoc; buvid4=49D6B8BC-BC56-1D76-85F6-861D5E9270E512695-025112010-fQCLKz731Jhg8lHN5RCznQ%3D%3D; buvid_fp=c6839aa88c7581ce3a2aa1ab0ad5902d; DedeUserID=505245134; DedeUserID__ckMd5=15985dc573f96f7d; bsource=search_google; theme-tip-show=SHOWED; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzYyMjIwMjAsImlhdCI6MTc3NTk2Mjc2MCwicGx0IjotMX0.iJqlGsjDiIBWodMvyrfaU7aOWM6djhalcLVviYJRtgQ; bili_ticket_expires=1776221960; SESSDATA=1d1dc8d4%2C1791514821%2Ce05d0%2A41CjB-vRppc17vT4L1zmzjx16Zxs6oRqB7AfFWkw51ebrfvSZUjox56Rn8v4-OZYdDBBgSVmoyZTZIMjFrc2tHWDlISVNVUW1FZy1yckJkM2pZaGlYRXUtMXdFLVlibnA2YjNEdmpzN0lncEJtOG54UGs3WkIzblhKRWVCVnBWQnJEVlZaSkZORWdnIIEC; bili_jct=4f0ef890de69d6b44af25a60fd884483; sid=4j1mljor; home_feed_column=4; browser_resolution=1144-935; b_lsid=FB7F5765_19D7FA35BAC"


def get_safe_headers():
    """获取安全的请求头，包含必要的User-Agent和Cookie"""
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "referer": "https://www.bilibili.com/",
        "Cookie": MY_COOKIE.encode('utf-8').decode('latin-1')
    }


@retry(tries=3, delay=2)
def get_ordinary_videos(rid, page):
    """获取指定分区的最新视频列表"""
    url = f"https://api.bilibili.com/x/web-interface/newlist?rid={rid}&pn={page}&ps=50"
    res = requests.get(url, headers=get_safe_headers(), timeout=10)
    data = res.json()
    if data.get('code') == 0:
        return "SUCCESS", data.get('data', {}).get('archives', [])
    return "FAILED", []


if __name__ == '__main__':
    OUTPUT_FILE = './data/负样本/负样本数据集_普通视频.json'
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # 全站 70+ 个细分子分区的 RID 列表
    # 涵盖动画、音乐、舞蹈、游戏、知识、科技、生活、美食、汽车、时尚等所有毛细血管
    sub_rids = [
        24, 25, 47, 86, 27, 33, 32, 51, 152,  # 动画/番剧
        28, 31, 30, 194, 59, 193, 29, 130,  # 音乐
        20, 154, 156, 198, 199, 200,  # 舞蹈
        17, 171, 172, 65, 173, 121, 136, 19,  # 游戏
        201, 124, 228, 207, 208, 209, 229,  # 知识
        122, 39, 96, 98, 176,  # 科技
        138, 21, 76, 75, 161, 162, 163, 174,  # 生活
        212, 213, 214, 215,  # 美食
        223, 224, 225, 226, 227,  # 汽车
        157, 158, 159, 192  # 时尚
    ]

    # 每个子分区只抓最表层的 15 页，确保 100% 不重复
    PAGES_PER_RID = 15

    negative_samples = {}  # 直接用字典按 bvid 去重收集

    for rid in sub_rids:
        print(f"抓取细分 RID: {rid} ...", end=" ")
        success_count = 0
        for page in range(1, PAGES_PER_RID + 1):
            status, archives = get_ordinary_videos(rid, page)
            if status == "SUCCESS":
                for v in archives:
                    bvid = v.get('bvid')
                    if not bvid or bvid in negative_samples:
                        continue  # 边抓边去重

                    stat = v.get('stat', {})
                    negative_samples[bvid] = {
                        'title': v.get('title', ''),
                        'bvid': bvid,
                        'tname': v.get('tname', ''),
                        'owner': {'name': v.get('owner', {}).get('name', ''), 'mid': v.get('owner', {}).get('mid', 0)},
                        'stat': {
                            'view': stat.get('view', 0), 'danmaku': stat.get('danmaku', 0),
                            'reply': stat.get('reply', 0), 'favorite': stat.get('favorite', 0),
                            'coin': stat.get('coin', 0), 'share': stat.get('share', 0),
                            'like': stat.get('like', 0), 'his_rank': 0, 'dislike': 0
                        },
                        'pubdate': v.get('pubdate', 0),
                        'desc': v.get('desc', ''),
                        'rcmd_reason': '',
                        'week_name': '普通最新视频',
                        'data_source': 'negative_sample'
                    }
                    success_count += 1
            time.sleep(1)  # 轻微休眠
        print(f"获取 {success_count} 条。目前总库: {len(negative_samples)} 条不重复数据")

    # 写入文件
    unique_list = list(negative_samples.values())
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=4)

    print(f"\n提取了 {len(unique_list)} 条纯净无重复的负样本，保存在: {OUTPUT_FILE}")
