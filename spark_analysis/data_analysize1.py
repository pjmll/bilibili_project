import os
import shutil
import jieba
from pyspark.sql import SparkSession, Row
from pyspark.sql.types import StructType, StructField, StringType, IntegerType
from pyspark.sql import functions as F
import pandas as pd

# 配置信息
# 读取HDFS上的数据
INPUT_PATH = "hdfs://localhost:9000/user/hadoop/bilibili.txt"
OUTPUT_DIR = "../output"
STOPWORDS_PATH = None # 可以指定停用词路径

def pretty_cut(text):
    if not text:
        return []
    # 使用jieba分词
    words = jieba.lcut(text)
    # 简单过滤：去掉长度为1的词（通常是标点或无意义单字）
    return [word for word in words if len(word) > 1]

def save_to_csv(df, filename):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    # 转为Pandas并保存
    pdf = df.toPandas()
    pdf.to_csv(os.path.join(OUTPUT_DIR, filename), index=False, encoding='utf-8-sig')
    print(f"Saved {filename}")

def main():
    # ① 创建SparkSession和SparkContext对象
    spark = SparkSession.builder \
        .appName("Bilibili Data Analysis") \
        .getOrCreate()
    sc = spark.sparkContext

    # 1. 用textFile函数读取HDFS(或本地)上的文本数据，并将其存储为RDD
    # Schema: up_name, week_name, title, desc, view, danmaku, reply, favorite, coin, share, like, rcmd_reason, tname, his_rank, label
    raw_rdd = sc.textFile(INPUT_PATH)
    
    # 2. 用map函数对RDD的每个元素进行切割并转化为包含多个字段的Row对象
    def parse_line(line):
        parts = line.split('\t')
        if len(parts) < 15:
            return None
        try:
            return Row(
                up_name=parts[0],
                week_name=parts[1],
                title=parts[2],
                description=parts[3],
                view=int(parts[4]),
                danmaku=int(parts[5]),
                reply=int(parts[6]),
                favorite=int(parts[7]),
                coin=int(parts[8]),
                share=int(parts[9]),
                like=int(parts[10]),
                rcmd_reason=parts[11],
                tname=parts[12],
                his_rank=int(parts[13]),
                label=int(parts[14])
            )
        except:
            return None

    row_rdd = raw_rdd.map(parse_line).filter(lambda x: x is not None)
    
    # 3. 定义数据集的结构schema，为Dataframe建立表头
    schema = StructType([
        StructField("up_name", StringType(), True),
        StructField("week_name", StringType(), True),
        StructField("title", StringType(), True),
        StructField("description", StringType(), True),
        StructField("view", IntegerType(), True),
        StructField("danmaku", IntegerType(), True),
        StructField("reply", IntegerType(), True),
        StructField("favorite", IntegerType(), True),
        StructField("coin", IntegerType(), True),
        StructField("share", IntegerType(), True),
        StructField("like", IntegerType(), True),
        StructField("rcmd_reason", StringType(), True),
        StructField("tname", StringType(), True),
        StructField("his_rank", IntegerType(), True),
        StructField("label", IntegerType(), True)
    ])
    
    # 将RDD转化为一个Dataframe
    df = spark.createDataFrame(row_rdd, schema)
    
    # 持久化中间数据集，加速后续多个查询
    df.cache()
    
    # 4. 在使用sql组件的时候还需要将DataFrame注册为Spark SQL中的临时视图
    df.createOrReplaceTempView("data")

    # (1) 统计视频收录次数最多的up主 (UP占比)
    popular_up = spark.sql("""
        SELECT up_name as up, count(*) as count 
        FROM data 
        GROUP BY up_name 
        ORDER BY count DESC 
        LIMIT 10
    """)
    save_to_csv(popular_up, "popular_up.csv")

    # (2) 统计入选次数最多的视频分类 (视频分区占比)
    popular_subject = spark.sql("""
        SELECT tname, count(*) as count 
        FROM data 
        GROUP BY tname 
        ORDER BY count DESC 
        LIMIT 10
    """)
    save_to_csv(popular_subject, "popular_subject.csv")

    # (2b) 新增：各分区核心质量指标分析 (为ML提供各分区的特征基准)
    subject_quality = spark.sql("""
        SELECT tname, 
               count(*) as video_count,
               round(avg(view), 2) as avg_view,
               round(avg(like), 2) as avg_like,
               round(sum(CASE WHEN label = 1 THEN 1 ELSE 0 END) / count(*), 4) as pos_rate
        FROM data 
        GROUP BY tname 
        HAVING video_count > 50
        ORDER BY pos_rate DESC
    """)
    save_to_csv(subject_quality, "subject_quality_analysis.csv")

    # (3) 各项指标 Top 10 视频统计
    metrics = {
        "view": "top_view_videos.csv",         # 播放量
        "coin": "top_coin_videos.csv",         # 投币
        "danmaku": "top_danmaku_videos.csv",   # 弹幕
        "favorite": "top_favorite_videos.csv", # 收藏
        "like": "top_like_videos.csv",         # 点赞
        "reply": "top_reply_videos.csv",       # 评论
        "share": "top_share_videos.csv"        # 转发
    }

    for metric, filename in metrics.items():
        top_df = spark.sql(f"""
            SELECT title, {metric} as value 
            FROM data 
            ORDER BY {metric} DESC 
            LIMIT 10
        """)
        save_to_csv(top_df, filename)

    # (3b) 新增：互动率 Top 10 (相对于播放量的质量，这是强有力的ML特征)
    # 过滤低播放量视频，防止分母过小导致的极端异常值
    interact_rate_stats = spark.sql("""
        SELECT title, 
               round(like / view, 4) as like_rate,
               round(coin / view, 4) as coin_rate,
               round((like + coin + favorite + share + reply) / view, 4) as total_interact_rate
        FROM data 
        WHERE view > 1000
        ORDER BY total_interact_rate DESC 
        LIMIT 10
    """)
    save_to_csv(interact_rate_stats, "top_interact_rate_videos.csv")

    # (4) UP主各项指标累计 Top 10
    up_metrics = {
        "view": "top_up_view.csv",
        "like": "top_up_like.csv",
        "coin": "top_up_coin.csv"
    }
    for metric, filename in up_metrics.items():
        up_top_df = spark.sql(f"""
            SELECT up_name as up, sum({metric}) as total_value 
            FROM data 
            GROUP BY up_name 
            ORDER BY total_value DESC 
            LIMIT 10
        """)
        save_to_csv(up_top_df, filename)

    # (4b) 新增：UP主“破圈”能力分层统计 (Task 3 深度指标)
    # 统计每个UP主上榜次数及其平均排名
    up_rank_stats = spark.sql("""
        SELECT up_name as up, 
               count(*) as total_appearances,
               round(avg(CASE WHEN his_rank > 0 THEN his_rank ELSE 100 END), 2) as avg_best_rank,
               max(view) as max_single_view
        FROM data 
        GROUP BY up_name 
        HAVING total_appearances >= 2
        ORDER BY total_appearances DESC, avg_best_rank ASC 
        LIMIT 20
    """)
    save_to_csv(up_rank_stats, "up_rank_stability.csv")

    # (5) 互动榜单 (综合热度)
    interact_stats = spark.sql("""
        SELECT title, (like + coin + favorite + share + reply) as total_interact
        FROM data 
        ORDER BY total_interact DESC 
        LIMIT 10
    """)
    save_to_csv(interact_stats, "top_interact_videos.csv")

    # (5) 破圈视频(Label=1)与普通视频(Label=0)的平均数据对比
    type_comparison = spark.sql("""
        SELECT label, 
               round(avg(view), 2) as avg_view, 
               round(avg(like), 2) as avg_like, 
               round(avg(favorite), 2) as avg_favorite,
               round(avg(danmaku), 2) as avg_danmaku,
               round(avg(coin), 2) as avg_coin,
               count(*) as video_count
        FROM data 
        GROUP BY label
    """)
    save_to_csv(type_comparison, "label_comparison.csv")

    # (5b) 新增：期数/时间趋势分析 (Task 3 深度指标)
    # 统计每周必看视频的平均播放量变化趋势
    week_trends = spark.sql("""
        SELECT week_name, 
               count(*) as count,
               round(avg(view), 0) as avg_view,
               round(avg(like + coin + share), 0) as avg_interact
        FROM data 
        WHERE week_name LIKE '%期%'
        GROUP BY week_name 
        ORDER BY week_name ASC
    """)
    save_to_csv(week_trends, "weekly_performance_trends.csv")

    # (5c) 新增：破圈视频分区分布
    break_circle_subject = spark.sql("""
        SELECT tname, count(*) as count 
        FROM data 
        WHERE label = 1
        GROUP BY tname 
        ORDER BY count DESC 
        LIMIT 10
    """)
    save_to_csv(break_circle_subject, "break_circle_subject.csv")

    # (5d) 新增：点赞投币比 (衡量内容质量/干货程度)
    coin_like_ratio = spark.sql("""
        SELECT tname, 
               round(sum(coin) / sum(like), 4) as coin_like_ratio,
               count(*) as count
        FROM data
        GROUP BY tname
        HAVING count > 50
        ORDER BY coin_like_ratio DESC
        LIMIT 10
    """)
    save_to_csv(coin_like_ratio, "coin_like_ratio_by_subject.csv")

    # (6) 词频统计 - 分别对正负样本进行标题词频分析
    # 正样本标题词频
    pos_titles = spark.sql("SELECT title FROM data WHERE label = 1")
    pos_word_counts = pos_titles.rdd.flatMap(lambda row: pretty_cut(row.title)) \
        .map(lambda word: (word, 1)) \
        .reduceByKey(lambda a, b: a + b) \
        .sortBy(lambda x: x[1], ascending=False)
    save_to_csv(spark.createDataFrame(pos_word_counts.take(200), ["word", "count"]), "pos_title_word_freq.csv")

    # 推荐理由词频 (仅针对有推荐理由的视频)
    rcmd_df = spark.sql("SELECT rcmd_reason FROM data WHERE rcmd_reason != title AND rcmd_reason IS NOT NULL")
    rcmd_word_counts = rcmd_df.rdd.flatMap(lambda row: pretty_cut(row.rcmd_reason)) \
        .map(lambda word: (word, 1)) \
        .reduceByKey(lambda a, b: a + b) \
        .sortBy(lambda x: x[1], ascending=False)
    save_to_csv(spark.createDataFrame(rcmd_word_counts.take(200), ["word", "count"]), "rcmd_reason_word_freq.csv")

    spark.stop()

if __name__ == "__main__":
    main()
