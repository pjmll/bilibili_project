import pandas as pd
import json
import re
import os

def preprocess_bilibili_data(input_files, output_txt):
    """
    input_files: 包含多个 JSON 路径的列表
    output_txt: 清洗后保存的路径
    """
    print("开始执行数据预处理与特征治理...")
    
    raw_data = []
    for file in input_files:
        if os.path.exists(file):
            with open(file, 'r', encoding='utf-8') as f:
                raw_data.extend(json.load(f))

    # 1. 数据扁平化与标签生成
    flat_data = []
    if not raw_data:
        print("警告：未读取到任何原始数据，请先确保已运行爬虫脚本生成了 JSON 文件。")
        return

    for item in raw_data:
        # 标签逻辑：只有来自weekly的才是爆款正样本 (1)，其他(如random_sample)均为负样本 (0)
        label = 1 if item.get('data_source') == 'weekly' else 0
        
        flat_item = {
            'up_name': str(item.get('owner', {}).get('name', '')).strip(),
            'week_name': str(item.get('week_name', '')).strip(),
            'title': str(item.get('title', '')).strip(),
            'desc': str(item.get('desc', '')).strip(),
            'view': item.get('stat', {}).get('view', 0),
            'danmaku': item.get('stat', {}).get('danmaku', 0),
            'reply': item.get('stat', {}).get('reply', 0),
            'favorite': item.get('stat', {}).get('favorite', 0),
            'coin': item.get('stat', {}).get('coin', 0),
            'share': item.get('stat', {}).get('share', 0),
            'like': item.get('stat', {}).get('like', 0),
            'rcmd_reason': str(item.get('rcmd_reason', '')).strip(),
            'tname': str(item.get('tname', '')).strip(),
            'his_rank': item.get('stat', {}).get('his_rank', 0),
            'label': label
        }
        flat_data.append(flat_item)

    df = pd.DataFrame(flat_data)

    # 2. 核心去重逻辑：基于UP主+标题的复合主键去重
    df = df.drop_duplicates(subset=['up_name', 'title'], keep='first')

    # 3. 异常值过滤：确保播放量有效且无负值
    df = df[df['view'] > 0]

    # 4. 文本规范化：利用正则清洗掉会破坏TSV格式的换行符和Tab键
    def clean_special_chars(text):
        text = str(text)
        text = re.sub(r'[\n\t\r]', ' ', text) # 替换为单个空格
        return re.sub(r'\s+', ' ', text).strip()

    for col in ['title', 'desc', 'rcmd_reason']:
        df[col] = df[col].apply(clean_special_chars)

    # 5. 格式导出：导出为无表头的TSV文件（制表符分隔），适配Hadoop/Hive
    final_columns = [
        'up_name', 'week_name', 'title', 'desc', 
        'view', 'danmaku', 'reply', 'favorite', 'coin', 'share', 'like', 
        'rcmd_reason', 'tname', 'his_rank', 'label'
    ]
    
    df[final_columns].to_csv(output_txt, sep='\t', header=False, index=False, encoding='utf-8')
    print(f"共生成 {len(df)} 条结构化记录。")

if __name__ == '__main__':
    # 动态获取项目根路径以兼容不同执行路径
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 获取输入文件绝对路径（兼容直接在根目录或spider目录运行产生的文件）
    pos_file = os.path.join(base_dir, 'bilibili_weekly_positive.json')
    if not os.path.exists(pos_file):
        pos_file = os.path.join(base_dir, 'spider', 'bilibili_weekly_positive.json')
        
    neg_file = os.path.join(base_dir, 'bilibili_random_negative.json')
    if not os.path.exists(neg_file):
        neg_file = os.path.join(base_dir, 'spider', 'bilibili_random_negative.json')
        
    # 输出到 data 目录
    output_dir = os.path.join(base_dir, 'data')
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, 'bilibili_final_clean.txt')
    
    preprocess_bilibili_data([pos_file, neg_file], out_file)
