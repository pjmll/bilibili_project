import requests
import json
import time

def get_bilibili_weekly_data(num_weeks=20, output_path='./bilibili_weekly_positive.json'):
    """
    定向爬取B站“每周必看”榜单数据，提取爆款正样本
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/v/popular/weekly'
    }
    
    # 步骤一：获取期数列表
    list_url = "https://api.bilibili.com/x/web-interface/popular/series/list"
    try:
        series_resp = requests.get(list_url, headers=headers)
        series_data = series_resp.json().get('data', {}).get('list', [])
    except Exception as e:
        print(f"期数列表获取失败: {e}")
        return

    all_videos = []
    
    # 步骤二：按期数遍历获取具体视频详情
    for series in series_data[:num_weeks]:
        number = series['number']
        subject = series['subject']
        print(f"正在抓取: {subject}...")
        
        detail_url = f"https://api.bilibili.com/x/web-interface/popular/series/one?number={number}"
        try:
            res = requests.get(detail_url, headers=headers)
            items = res.json().get('data', {}).get('list', [])
            
            for item in items:
                # 遵循下游清洗脚本规范进行 Schema 映射
                video_info = {
                    "title": item.get('title'),
                    "bvid": item.get('bvid'),
                    "tname": item.get('tname'),
                    "owner": {
                        "mid": item.get('owner', {}).get('mid'),
                        "name": item.get('owner', {}).get('name')
                    },
                    "stat": {
                        "view": item.get('stat', {}).get('view'),
                        "danmaku": item.get('stat', {}).get('danmaku'),
                        "reply": item.get('stat', {}).get('reply'),
                        "favorite": item.get('stat', {}).get('favorite'),
                        "coin": item.get('stat', {}).get('coin'),
                        "share": item.get('stat', {}).get('share'),
                        "like": item.get('stat', {}).get('like'),
                        "his_rank": item.get('stat', {}).get('his_rank', 0)
                    },
                    "desc": item.get('desc'),
                    "rcmd_reason": item.get('rcmd_reason', ""),
                    "week_name": subject,
                    "data_source": "weekly" # 标记为正样本数据源
                }
                all_videos.append(video_info)
            
            # 延时防风控
            time.sleep(1.5) 
        except Exception as e:
            print(f"第 {number} 期抓取异常: {e}")

    # 数据持久化
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=4)
    print(f"正样本采集完成，共 {len(all_videos)} 条。")

if __name__ == '__main__':
    get_bilibili_weekly_data()
