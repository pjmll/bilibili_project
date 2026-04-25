# -*- coding: utf-8 -*-
"""
使用 Pyecharts 对 Spark 和 MLlib 分析输出的产物进行可视化
生成包含多个复杂图表组合的交互式 HTML 数据大屏。
"""
import os
import math
import pandas as pd
from pyecharts.charts import Bar, Line, Pie, WordCloud, Page, HeatMap, Radar, Scatter, Funnel
from pyecharts import options as opts
from pyecharts.globals import ThemeType

OUTPUT_DIR = "../output"
STATIC_DIR = "../static"
REPORT_HTML = "Bilibili_BigData_Dashboard.html"

def read_data(filename, source_dir=OUTPUT_DIR):
    return pd.read_csv(os.path.join(source_dir, filename))

def draw_top_videos():
    """图1：Top 10 播放量视频柱状图"""
    df = read_data("top_view_videos.csv").head(10).iloc[::-1]
    bar = (
        Bar(init_opts=opts.InitOpts(theme=ThemeType.MACARONS))
        .add_xaxis(df['title'].str[:15].tolist())
        .add_yaxis("播放量", [int(x) for x in df['value'].tolist()])
        .reversal_axis()
        .set_series_opts(label_opts=opts.LabelOpts(position="right"))
        .set_global_opts(title_opts=opts.TitleOpts(title="播放量 Top 10 视频"))
    )
    return bar

def draw_popular_subject():
    """图2：热门收录视频分区占比"""
    df = read_data("popular_subject.csv").head(10)
    pie = (
        Pie(init_opts=opts.InitOpts(theme=ThemeType.DARK))
        .add("收录次数", [(str(k), int(v)) for k, v in zip(df['tname'], df['count'])], 
             radius=["30%", "75%"], rosetype="radius")
        .set_global_opts(title_opts=opts.TitleOpts(title="热搜视频分区分布情况"),
                         legend_opts=opts.LegendOpts(orient="vertical", pos_left="2%", pos_top="20%"))
        .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}: {c}次"))
    )
    return pie

def draw_trend_line():
    """图3：整体趋势图"""
    df = read_data("weekly_performance_trends.csv").head(20)
    line = (
        Line(init_opts=opts.InitOpts(theme=ThemeType.LIGHT))
        .add_xaxis(df['week_name'].tolist())
        .add_yaxis("平均播放量", [float(x) for x in df['avg_view']], is_smooth=True)
        .add_yaxis("平均互动量", [float(x) for x in df['avg_interact']], is_smooth=True)
        .set_global_opts(title_opts=opts.TitleOpts(title="栏目平均播放与互动趋势"),
                         xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-45)))
    )
    return line

def draw_wordcloud():
    """图4：标题词云图（修复显示与过滤无效词）"""
    df = read_data("pos_title_word_freq.csv")
    stop_words = {'em', 'class', 'keyword', '什么', '怎么', '我们', '这个', '一个', '可以', '没有', 'quot'}
    df_filtered = df[~df['word'].isin(stop_words)].head(100)
    
    # 必须转换为原生的 str 和 int 类型，否则 pyecharts 会渲染成 {}
    data = [(str(row['word']), int(row['count'])) for _, row in df_filtered.iterrows()]
    
    wc = (
        WordCloud(init_opts=opts.InitOpts(theme=ThemeType.VINTAGE))
        .add(series_name="高频热词", data_pair=data, word_size_range=[20, 100])
        .set_global_opts(title_opts=opts.TitleOpts(title="爆款视频标题词云"))
    )
    return wc

def draw_model_comparison():
    """图5：机器学习模型分类性能对比"""
    df = read_data("comparison.csv", STATIC_DIR)
    bar = (
        Bar(init_opts=opts.InitOpts(theme=ThemeType.WALDEN))
        .add_xaxis(df['classifier'].tolist())
        .add_yaxis("准确率 (Accuracy)", [round(float(val)*100, 2) for val in df['Acc']])
        .add_yaxis("AUC 面积", [round(float(val)*100, 2) for val in df['Auc']])
        .set_global_opts(title_opts=opts.TitleOpts(title="多分类器基于特征预测热搜评估"))
    )
    return bar

def draw_corr_heatmap():
    """图6：互相关热力图"""
    df = read_data("cor_matrix.csv", STATIC_DIR)
    if 'Unnamed: 0' in df.columns:
        df = df.set_index('Unnamed: 0')
    features = [str(c) for c in df.columns]
    data = [[i, j, float(round(df.iloc[i, j], 2))] for i in range(len(features)) for j in range(len(features))]
    heat = (
        HeatMap(init_opts=opts.InitOpts(width="800px", height="600px"))
        .add_xaxis(features)
        .add_yaxis("Correlation", features, data)
        .set_global_opts(title_opts=opts.TitleOpts(title="特征相关性矩阵"),
                         visualmap_opts=opts.VisualMapOpts(min_=-1, max_=1))
    )
    return heat

def draw_popular_up():
    """图7(新增)：王者UP主上榜次数漏斗图"""
    df = read_data("popular_up.csv")
    # 剔除UP主名称为空（爬虫未抓取到或无效数据）的行，否则会导致漏斗图比例失衡
    df = df[df['up'].notnull() & (df['up'] != '') & (df['up'] != ' ')]
    df = df.head(8)
    max_val = int(df['count'].max())
    data = [(str(w), int(c)) for w, c in zip(df['up'], df['count'])]
    funnel = (
        Funnel()
        .add("上榜次数", data, sort_="descending", min_=0, max_=max_val, label_opts=opts.LabelOpts(position="inside"))
        .set_global_opts(title_opts=opts.TitleOpts(title="收录次数最多UP主 Top 8"))
    )
    return funnel

def draw_radar_comparison():
    """图8(新增)：破圈视频与普通视频多维指标对比雷达图"""
    df = read_data("label_comparison.csv").fillna(0)
    # 取平均各项指标进行对比
    features = ["avg_view", "avg_like", "avg_coin", "avg_favorite", "avg_danmaku"]
    feature_names = ["平均播放量(log10)", "平均点赞(log10)", "平均投币(log10)", "平均收藏(log10)", "平均弹幕(log10)"]
    # 破圈爆款的数据量大约是普通视频的100倍甚至1000倍，用原始值普通视频只剩中心的一个小点
    # 因此在雷达图展示时，使用对数缩放 (log10) 才能客观对比两者的量级差别
    max_values = [math.log10(max(1, df[f].max())) * 1.1 for f in features]
    
    radar = (
        Radar()
        .add_schema(schema=[opts.RadarIndicatorItem(name=k, max_=v) for k, v in zip(feature_names, max_values)])
    )
    for _, row in df.iterrows():
        name = "破圈爆款(Label=1)" if int(row['label']) == 1 else "普通视频(Label=0)"
        # 增加 area_style_opts 让雷达图有颜色填充效果，便于直观看到边界区分
        radar.add(
            series_name=name, 
            data=[[math.log10(max(1, int(row[f]))) for f in features]],
            areastyle_opts=opts.AreaStyleOpts(opacity=0.3),
            linestyle_opts=opts.LineStyleOpts(width=2)
        )
        
    radar.set_global_opts(
        title_opts=opts.TitleOpts(title="破圈 vs 普通 视频多维指标对数量级雷达图"),
        legend_opts=opts.LegendOpts(pos_bottom="bottom")
    )
    return radar

def draw_subject_quality():
    """图9(新增)：各分区质量与爆款率散点图"""
    df = read_data("subject_quality_analysis.csv")
    # 为了表现出散点的错落，这里取包含频次数较高的前40个分区
    df = df.sort_values(by="video_count", ascending=False).head(40)
    scatter = (
        Scatter()
        .add_xaxis([str(x) for x in df['tname'].tolist()])
        .add_yaxis("爆款率(pos_rate)", [float(x) for x in df['pos_rate'].tolist()],
                   symbol_size=10, 
                   label_opts=opts.LabelOpts(is_show=False))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="各分区爆款率散点分布"),
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=-60)),
            yaxis_opts=opts.AxisOpts(name="爆款率(%)")
        )
    )
    return scatter

def main():
    print("[INFO] 开始生成可视化数据大屏...")
    page = Page(layout=Page.DraggablePageLayout)
    page.add(
        draw_top_videos(),
        draw_popular_subject(),
        draw_trend_line(),
        draw_wordcloud(),
        draw_model_comparison(),
        draw_corr_heatmap(),
        draw_popular_up(),
        draw_radar_comparison(),
        draw_subject_quality()
    )
    page.render(REPORT_HTML)
    print(f"[SUCCESS] 交互式大屏已生成！文件路径: {os.path.abspath(REPORT_HTML)}")

if __name__ == "__main__":
    main()
