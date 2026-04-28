"""
B站视频数据合并、清洗与预处理脚本
功能：
1. 从各榜单爬虫获取的原始JSON数据中提取标准化的视频列表
2. 合并《每周必看》、《热门排行榜》、《入站必刷》等多个榜单的正样本
3. 整合负样本数据，进行联合去重
4. 扁平化嵌套的JSON结构，进行字段标准化
5. 异常值过滤与文本规范化
6. 导出为TSV格式供Spark处理
"""

import json
import os
import shutil
import pandas as pd
import re
from glob import glob


# ==========================================
# 第一步：合并多个榜单的正样本数据
# ==========================================

def extract_videos_from_api_json(filepath, source_label):
    """从 B站 API 返回的原始 JSON 中提取标准化的视频列表"""
    videos = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

            # API 数据的两种常见包裹形式
            video_list = []
            if isinstance(data, list):
                video_list = data
            elif isinstance(data, dict):
                video_list = data.get('data', {}).get('list', [])

            # 提取所属期数/标签
            week_name = data.get('data', {}).get('config', {}).get('name', '') if isinstance(data, dict) else ''

            for v in video_list:
                stat = v.get('stat', {})
                standard_v = {
                    'title': v.get('title', ''),
                    'bvid': v.get('bvid', ''),
                    'tname': v.get('tname', v.get('tnamev2', '')),
                    'owner': v.get('owner', {'name': '', 'mid': 0}),
                    'stat': {
                        'view': stat.get('view', 0),
                        'danmaku': stat.get('danmaku', 0),
                        'reply': stat.get('reply', 0),
                        'favorite': stat.get('favorite', 0),
                        'coin': stat.get('coin', 0),
                        'share': stat.get('share', 0),
                        'like': stat.get('like', 0),
                        'his_rank': stat.get('his_rank', 1),
                        'dislike': stat.get('dislike', 0)
                    },
                    'pubdate': v.get('pubdate', 0),
                    'desc': v.get('desc', ''),
                    'rcmd_reason': v.get('rcmd_reason', ''),
                    'week_name': week_name,
                    'data_source': source_label
                }

                # 处理可能嵌在 dict 里的 rcmd_reason
                if isinstance(standard_v['rcmd_reason'], dict):
                    standard_v['rcmd_reason'] = standard_v['rcmd_reason'].get('content', '')

                videos.append(standard_v)
    except Exception as e:
        print(f"读取文件 {filepath} 失败: {e}")
    return videos


def merge_positive_samples(input_dir='./data', output_dir='./data'):
    """
    合并多个榜单的正样本数据
    输入：从爬虫脚本生成的多个 JSON 文件
    输出：标准化的正样本 JSON 文件
    """
    
    print("="*50)
    print("第一步：合并多个榜单的正样本数据")
    print("="*50)
    
    # 任务 1：整合《每周必看》
    print("\n[1.1] 整合《每周必看》数据集...")
    weekly_files = glob(os.path.join(input_dir, '周必看', 'week_*.json'))
    weekly_data = []
    for f in weekly_files:
        weekly_data.extend(extract_videos_from_api_json(f, "weekly"))
    
    weekly_out_path = os.path.join(output_dir, '正样本', '每周必看数据集.json')
    os.makedirs(os.path.dirname(weekly_out_path), exist_ok=True)
    with open(weekly_out_path, 'w', encoding='utf-8') as f:
        json.dump(weekly_data, f, ensure_ascii=False, indent=4)
    print(f"  ✓ 《每周必看》合并完成，共 {len(weekly_data)} 条")

    # 任务 2：整合《热门排行榜》（如果存在）
    print("\n[1.2] 整合《热门排行榜》数据集...")
    popular_files = glob(os.path.join(input_dir, '热门排行榜', '*.json'))
    popular_data = []
    for f in popular_files:
        popular_data.extend(extract_videos_from_api_json(f, "popular"))
    
    popular_out_path = os.path.join(output_dir, '正样本', '热门排行榜数据集.json')
    with open(popular_out_path, 'w', encoding='utf-8') as f:
        json.dump(popular_data, f, ensure_ascii=False, indent=4)
    print(f"  ✓ 《热门排行榜》合并完成，共 {len(popular_data)} 条")

    # 任务 3：整合《入站必刷》（如果存在）
    print("\n[1.3] 整合《入站必刷》数据集...")
    rcmd_files = glob(os.path.join(input_dir, '入站必刷', '*.json'))
    rcmd_data = []
    for f in rcmd_files:
        rcmd_data.extend(extract_videos_from_api_json(f, "rcmd"))
    
    rcmd_out_path = os.path.join(output_dir, '正样本', '入站必刷数据集.json')
    with open(rcmd_out_path, 'w', encoding='utf-8') as f:
        json.dump(rcmd_data, f, ensure_ascii=False, indent=4)
    print(f"  ✓ 《入站必刷》合并完成，共 {len(rcmd_data)} 条")

    return weekly_out_path, popular_out_path, rcmd_out_path


# ==========================================
# 第二步：合并正负样本并去重
# ==========================================

def merge_positive_negative_samples(input_dir='./data', output_dir='./data'):
    """
    合并正样本和负样本，进行联合去重
    输入：正样本目录和负样本文件
    输出：去重后的合并JSON文件
    """
    
    print("\n" + "="*50)
    print("第二步：合并正负样本并进行去重")
    print("="*50)
    
    # 收集所有正样本
    positive_files = glob(os.path.join(input_dir, '正样本', '*.json'))
    positive_data = []
    for f in positive_files:
        with open(f, 'r', encoding='utf-8') as fp:
            data = json.load(fp)
            if isinstance(data, list):
                positive_data.extend(data)
            print(f"  ✓ 加载: {os.path.basename(f)} ({len(data)} 条)")

    # 加载负样本
    negative_file = os.path.join(input_dir, '负样本', '负样本数据集_普通视频.json')
    negative_data = []
    if os.path.exists(negative_file):
        with open(negative_file, 'r', encoding='utf-8') as f:
            negative_data = json.load(f)
        print(f"  ✓ 加载负样本: {len(negative_data)} 条")
    else:
        print(f"  ⚠ 未找到负样本文件")

    # 合并并去重
    all_data = positive_data + negative_data
    print(f"\n[2.2] 正在合并 {len(positive_data)} 条正样本 + {len(negative_data)} 条负样本...")
    
    unique_data = {}
    for item in all_data:
        # 优先用 bvid，如果没有就用 标题+UP主名
        unique_key = item.get('bvid') if item.get('bvid') else f"{item.get('title')}_{item.get('owner', {}).get('name')}"
        if unique_key and unique_key not in unique_data:
            unique_data[unique_key] = item

    final_unique_list = list(unique_data.values())
    
    # 保存合并后的数据
    final_json_path = os.path.join(output_dir, '数据集合并版.json')
    with open(final_json_path, 'w', encoding='utf-8') as f:
        json.dump(final_unique_list, f, ensure_ascii=False, indent=4)

    print(f"  ✓ 去重完成，保留 {len(final_unique_list)} 条唯一数据")
    print(f"  ✓ 合并结果保存至: {final_json_path}")
    
    return final_json_path


# ==========================================
# 第三步：数据扁平化与清洗
# ==========================================

def preprocess_and_export(input_json_path, output_txt_path='./data/bilibili_week.txt'):
    """
    进行数据预处理：
    1. 扁平化嵌套的JSON结构
    2. 字段标准化与标签映射
    3. 去重处理
    4. 异常值过滤
    5. 文本规范化
    6. 导出为TSV格式
    """
    
    print("\n" + "="*50)
    print("第三步：数据扁平化与清洗")
    print("="*50)
    
    os.makedirs(os.path.dirname(output_txt_path), exist_ok=True)
    
    # 读取合并后的JSON数据
    print(f"\n[3.1] 读取输入文件: {input_json_path}")
    with open(input_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"  ✓ 加载 {len(data)} 条记录")

    # 扁平化与标签生成
    print("\n[3.2] 进行数据扁平化与标签映射...")
    flat_data = []
    for item in data:
        # 动态生成机器学习的 Label：负样本为 0，其他爆款榜单为 1
        label = 0 if item.get('data_source') == 'negative_sample' else 1

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
            'dislike': item.get('stat', {}).get('dislike', 0),
            'label': label
        }
        flat_data.append(flat_item)
    
    df = pd.DataFrame(flat_data)
    print(f"  ✓ 扁平化 {len(df)} 条记录")

    # 去重处理
    print("\n[3.3] 进行去重处理...")
    original_len = len(df)
    df = df.drop_duplicates(subset=['up_name', 'title'], keep='first')
    print(f"  ✓ 去重前: {original_len} 条，去重后: {len(df)} 条，删除 {original_len - len(df)} 条重复记录")

    # 异常值过滤
    print("\n[3.4] 进行异常值过滤...")
    before_filter = len(df)
    df = df[df['view'] > 0]
    print(f"  ✓ 过滤播放量≤0的异常记录，删除 {before_filter - len(df)} 条")

    # 文本规范化
    print("\n[3.5] 进行文本规范化...")
    def clean_text(text):
        """清洗文本中会破坏TSV格式的字符"""
        if not isinstance(text, str):
            return text
        # 将换行符、回车符、制表符替换为空格，并合并连续空格
        text = re.sub(r'[\r\n\t]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    text_columns = ['title', 'desc', 'rcmd_reason']
    for col in text_columns:
        df[col] = df[col].apply(clean_text)
    print(f"  ✓ 清洗文本字段完成")

    # 导出为TSV格式
    print("\n[3.6] 导出为TSV格式...")
    feature_order = [
        'up_name', 'week_name', 'title', 'desc', 'view', 'danmaku', 'reply',
        'favorite', 'coin', 'share', 'like', 'rcmd_reason', 'tname', 'his_rank',
        'dislike', 'label'
    ]
    
    df_export = df[feature_order]
    df_export.to_csv(output_txt_path, sep='\t', index=False, header=False, encoding='utf-8')
    print(f"  ✓ 共生成 {len(df)} 条结构化记录")
    print(f"  ✓ 导出至: {output_txt_path}")


# ==========================================
# 主程序入口
# ==========================================

if __name__ == '__main__':
    # 获取项目根路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(project_root, 'data')
    
    print("\n" + "="*50)
    print("B站视频数据处理流程")
    print("="*50)
    print(f"项目根路径: {project_root}")
    print(f"数据目录: {data_dir}\n")

    # 执行步骤 1：合并正样本
    weekly_out, popular_out, rcmd_out = merge_positive_samples(data_dir, data_dir)

    # 执行步骤 2：合并正负样本
    merged_json = merge_positive_negative_samples(data_dir, data_dir)

    # 执行步骤 3：数据预处理和导出
    output_txt = os.path.join(data_dir, 'bilibili.txt')
    preprocess_and_export(merged_json, output_txt)

    print("\n" + "="*50)
    print("✓ 所有数据处理步骤完成！")
    print("="*50)
    print(f"\n输出文件位置:")
    print(f"  • 正样本合并: {os.path.join(data_dir, '正样本')}/*.json")
    print(f"  • 正负样本合并: {merged_json}")
    print(f"  • 最终TSV: {output_txt}")
