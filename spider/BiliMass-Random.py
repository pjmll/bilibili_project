import requests
import json
import time
import random

def crawl_massive_bilibili_data(target_count=10000, output_path='./bilibili_random_negative.json', save_interval=1000):
    """
    基于随机 AV 号的全域海量数据抓取，带定时持久化容灾机制
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.bilibili.com/'
    }
    
    all_videos = []
    success_count = 0
    attempts = 0
    
    print(f"启动海量抓取，目标: {target_count} 条，存档频率: 每 {save_interval} 条")

    while success_count < target_count:
        attempts += 1
        # 在活跃视频区间内随机生成 aid
        random_aid = random.randint(300000000, 990000000)
        url = f"https://api.bilibili.com/x/web-interface/view?aid={random_aid}"
        
        try:
            res = requests.get(url, headers=headers, timeout=10)
            res_json = res.json()
            
            # 过滤失效、删除或私密视频 (code == 0 视为正常响应)
            if res_json.get('code') == 0:
                item = res_json.get('data', {})
                
                video_info = {
                    "title": item.get('title', ''),
                    "bvid": item.get('bvid', ''),
                    "tname": item.get('tname', ''),
                    "owner": {
                        "mid": item.get('owner', {}).get('mid', 0),
                        "name": item.get('owner', {}).get('name', '')
                    },
                    "stat": {
                        "view": item.get('stat', {}).get('view', 0),
                        "danmaku": item.get('stat', {}).get('danmaku', 0),
                        "reply": item.get('stat', {}).get('reply', 0),
                        "favorite": item.get('stat', {}).get('favorite', 0),
                        "coin": item.get('stat', {}).get('coin', 0),
                        "share": item.get('stat', {}).get('share', 0),
                        "like": item.get('stat', {}).get('like', 0),
                        "his_rank": item.get('stat', {}).get('his_rank', 0)
                    },
                    "desc": item.get('desc', ''),
                    "rcmd_reason": item.get('dynamic', ''),
                    "week_name": "mass_random", 
                    "data_source": "random_sample" # 标记为负样本数据源
                }
                
                all_videos.append(video_info)
                success_count += 1
                
                # 持久化容灾机制：达到阈值自动落盘
                if success_count % save_interval == 0:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(all_videos, f, ensure_ascii=False, indent=4)
                    print(f"-> 触发自动存档: 已安全写入 {success_count} 条数据。")

            # 动态延时模拟人类请求频率
            time.sleep(random.uniform(0.8, 1.5))
            
        except Exception as e:
            time.sleep(3) # 异常退避策略

    # 终止态保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_videos, f, ensure_ascii=False, indent=4)
    
    print(f"全域抓取结束：总尝试 {attempts} 次，成功命中 {success_count} 条有效数据。")

if __name__ == '__main__':
    crawl_massive_bilibili_data()
