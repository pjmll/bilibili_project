# Bilibili 弹幕视频网大数据分析项目

本项目旨在通过爬虫、数据清洗、Spark 大数据架构以及数据可视化技术，对 B 站“每周必看”栏目的视频数据进行全面深入的收集与分析。通过构建从数据采集到分布式计算、机器学习预测再到大屏可视化的端到端大数据 Pipeline，探索热门视频的内在规律，并挖掘决定视频“破圈”的核心流量密码。

## 🎯 项目目标与核心任务

本项目基于常见的大数据处理流，完成了以下五项核心任务：
1. **数据采集 (Spider)**：采用 Python 爬虫技术，跨接口收集截止至 5月20日 B 站所有《每周必看》栏目的视频数据以及 UP 主信息。
2. **数据清洗与预处理 (Data Process)**：利用 Pandas 对原始 JSON 数据进行清洗，完成异常数据的剔除、无效文本的修正、核心字段抽取与结构化，生成可供 Hadoop/Spark 读取的标准 `.txt` 格式数据。
3. **基于 Spark SQL 的多维特征分析 (Data Analysis 1)**：使用 Spark SQL 对海量清洗数据进行分布式多维度统计，挖掘诸如：收录次数最多的 UP 主、热门分区分布、视频各项指标 Top 10、UP主“破圈”能力、每周平均播放量趋势，以及视频互动率和“干货度”（投币点赞比）等深层指标。
4. **基于 Spark MLlib 的机器学习分类预测 (Data Analysis 2)**：利用 Spark MLlib 研究点赞数、播放量、互动热度等特征之间的斯皮尔曼相关性，利用逻辑回归(LR)、决策树(DT)、随机森林(RF)和梯度提升树(GBT)对“视频能否进入热搜榜/破圈”进行二分类预测，并提取了机器学习推导出的“核心特征重要性”。
5. **数据交互大屏可视化 (Visualization)**：基于 Pyecharts 数据可视化技术，将上述所有的 SQL 离线统计与机器学习分析产物，整合渲染成包含 12 项复杂图表（饼图、柱状图、折线图、词云、热力图、漏斗图、雷达图、散点图等）的动态交互式 HTML 数据大屏。

## 📁 目录结构与模块说明

```text
├── spider/               # 爬虫采集模块，包含对视频列表和视频详情的抓取
├── data_process/         # 数据清洗与标签化模块，生成带有 label 的标准数据集
├── data/                 # 离线数据存储目录
│   ├── bilibili.txt      # 最终清洗好的结构化数据文本（用于传至 HDFS）
│   └── 负样本/正样本/      # 原始样本集合
├── spark_analysis/       # Spark 分布式处理模块
│   ├── data_analysize1.py # 任务一：Spark SQL 深入业务多维指标分析
│   └── data_analysize2.py # 任务二：Spark MLlib 机器学习模型预测与特征提取
├── output/               # Spark SQL 统计指标 CSV 输出目录
├── static/               # MLlib 模型特征与性能比较 CSV 输出目录
├── visualization/        # Pyecharts 可视化大屏渲染模块
│   └── pyecharts_render.py # 读取 output/static 数据生成 HTML 仪表盘大屏
└── utils/                # 爬虫请求伪装与日志等通用工具
```

## 🚀 快速开始与运行流

请按照大数据处理流水线的顺序，依次执行以下模块：

1. **环境准备**：启动 Hadoop (HDFS) 与 Spark 环境（如需在集群运行）。单机测试可直接依赖本地 PySpark。
2. **数据处理准备**：
   确保 `data/bilibili.txt` 存在。该数据由 `spider` 目录采集后经 `data_process` 目录处理得来。
3. **第一阶段分析：Spark SQL 大数据统计**
   ```bash
   cd spark_analysis
   python data_analysize1.py  # 或使用 spark-submit 提交
   ```
   **产物**：会在 `output/` 目录下生成大量业务指标统计 `.csv`，例如 `top_view_videos.csv`、`coin_like_ratio_by_subject.csv` 等。
4. **第二阶段分析：Spark MLlib 机器学习**
   ```bash
   cd spark_analysis
   python data_analysize2.py 
   ```
   **产物**：会在 `static/` 目录下生成 `comparison.csv`（模型评分对比）、`cor_matrix.csv`（相关性矩阵）以及 `rf_feature_importance.csv` 等机器学习评估特征。
5. **第三阶段：生成可视化大屏**
   ```bash
   cd ../visualization
   python pyecharts_render.py
   ```
   **产物**：会在 `visualization` 文件夹下生成 `Bilibili_BigData_Dashboard.html` 数据大屏页面，直接用浏览器打开即可体验炫酷的数据洞察！

## 💡 扩展与未来优化方向
本项目已具备很高的工程完整度，未来可扩展的方向为：
* **引入实时流处理**：采用 Kafka + Spark Streaming，对最新的 B 站弹幕/投币数据进行实时处理与大屏动态更新。
* **工作流调度化**：引入 Apache Airflow 编排整个从爬虫 -> HDFS 上传 -> Spark 分析 -> 可视化渲染 的自动化工作流。