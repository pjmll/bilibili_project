# Bilibili 弹幕视频网数据分析项目

本项目旨在通过爬虫、数据清洗、Spark 大数据分析以及数据可视化等技术，对 B 站“每周必看”栏目的视频数据进行全面深入的收集与分析，探索热门视频的内在规律，并构建预测模型。

## 🎯 项目目标与任务
本项目主要完成了以下五项核心任务：
1. **数据采集**：采用爬虫技术，收集截止至5月20日 B 站所有《每周必看》栏目的数据。
2. **数据清洗与预处理**：对原始数据进行清洗，涵盖有价值字段的选择、异常数据的删除以及文本数据的修正等，最终将清洗后的数据保存为 `.txt` 文件并具备上传至 HDFS 的准备。
3. **基于 Spark SQL 的特征分析**：使用 Spark SQL 组件对存入 HDFS 的数据进行多维度分析，主要统计各收录视频的基本播放情况以及 UP 主的累计数据。
4. **基于 Spark MLlib 的机器学习分析**：利用 Spark MLlib 组件，研究视频的点赞数、播放量、互动热度等特征之间的相关性，并训练机器学习模型进行分类（预测视频能否进入热搜榜前十）。
5. **数据可视化展示**：基于分析的结果数据，采用 pyecharts 工具对结果进行可视化全方位呈现。

## 📁 目录结构

- `spider/`: 爬虫模块。包含抓取“每周必看”列表和视频详情数据的代码。
- `data_process/`: 数据处理模块。用于对原始 JSON 等数据进行清洗并提取有用字段。
- `spark_analysis/`: Spark 大数据分析模块。包含基于 Spark SQL 的业务逻辑分析脚本。
- `visualization/`: 数据可视化模块。包含 pyecharts 绘图逻辑。
- `utils/`: 工具类模块。
- `data/`: 数据存储目录。

## 🚀 快速开始与使用说明

1. 爬虫抓取数据: `python spider/crawl_bilibili_fav.py`
2. 处理数据: `python data_process/pd_label_data.py`
3. Spark 分析: `spark-submit spark_analysis/spark_analyse.py`
4. 数据可视化: `python visualization/data_analysize1.py`