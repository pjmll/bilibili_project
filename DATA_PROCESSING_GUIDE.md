## 爬虫和数据处理执行指南

### 📋 快速开始

本指南说明如何使用整理后的爬虫和数据处理脚本。

### 🔄 完整数据流程

```
第1步: 采集数据 (spider/)
    ↓
第2步: 合并清洗 (data_process/)
    ↓
第3步: 统计分析 (spark_analysis/)
    ↓
第4步: 可视化展示 (visualization/)
```

---

## 第1步：数据采集 (spider/)

### 1.1 采集每周必看数据

```bash
cd spider/
python BiliWeekly-Target.py
```

**说明：**
- 获取B站官方最新的每周必看期数列表
- 对比本地文件，只下载缺失的期数（支持增量更新）
- 输出目录：`../data/周必看/` 
- 输出文件：`week_{number}.json`（按期数编号）
- 触发风控时会自动暂停并提示重试

**输出特征：**
```json
{
  "title": "视频标题",
  "bvid": "BV1234567890",
  "tname": "分类",
  "owner": {"name": "UP主名", "mid": 123456},
  "stat": {"view": 10000, "danmaku": 100, ...},
  "week_name": "第123期",
  "data_source": "weekly"
}
```

### 1.2 采集负样本数据（普通视频）

```bash
python BiliMass-Random-Negative.py
```

**说明：**
- 从B站全站70+个细分分区采集普通视频
- 覆盖动画、音乐、舞蹈、游戏、知识、科技、生活、美食、汽车、时尚等所有分类
- 每个分区采集最新的15页视频，确保高质量和多样性
- 采用字典结构边爬取边去重，不会产生重复数据
- 输出目录：`../data/负样本/`
- 输出文件：`负样本数据集_普通视频.json`

**采集速度：**
- 每个分区的15页采集，共70+个分区
- 每个请求间隔1秒，预计采集时间约 1-2 小时
- 可以随时中断重新运行，会自动跳过已采集的数据

---

## 第2步：数据处理 (data_process/)

### 2.1 一键执行完整流程

```bash
cd ../data_process/
python BiliData-Merge-Clean.py
```

**自动执行的9个步骤：**

| 步骤 | 操作               | 输入                 | 输出                     |
| ---- | ------------------ | -------------------- | ------------------------ |
| 1-3  | 提取并合并正样本   | `data/周必看/*.json` | `data/正样本/*.json`     |
| 4-5  | 正负样本合并去重   | 正负样本JSON         | `data/数据集合并版.json` |
| 6-8  | 扁平化、清洗、过滤 | 合并的JSON           | DataFrame                |
| 9    | 导出TSV格式        | DataFrame            | `data/bilibili.txt`      |

**输出示例：**
```
data/bilibili.txt (无表头TSV格式)
-----------
up_name    week_name    title    desc    view    danmaku    ...    label
某UP主    第123期    视频标题    视频简介    10000    100    ...    1
```

**处理统计：**
```
第一步：合并多个榜单的正样本数据
  [1.1] 《每周必看》合并完成，共 XXX 条
  [1.2] 《热门排行榜》合并完成，共 XXX 条
  [1.3] 《入站必刷》合并完成，共 XXX 条

第二步：合并正负样本并进行去重
  ✓ 加载各正样本文件
  ✓ 加载负样本：XXX 条
  ✓ 去重前: XXXX 条，去重后: XXXX 条

第三步：数据扁平化与清洗
  [3.2] 进行数据扁平化与标签映射
  [3.3] 去重处理
  [3.4] 异常值过滤
  [3.5] 文本规范化
  [3.6] 导出为TSV格式
```

---

## 第3步：Spark分析 (spark_analysis/)

### 3.1 业务指标统计与文本分析

```bash
cd ../spark_analysis/
python data_analysize1.py
```

**输出：** `output/` 目录下的CSV文件，包括：
- UP主排行、分区分布、互动率排行等
- 词频统计、推荐理由高频词等

### 3.2 机器学习预测

```bash
python data_analysize2.py
```

**输出：** `output/` 和 `static/` 目录下的分析结果和模型指标

---

## 数据格式说明

### TSV文件格式 (bilibili.txt)

**16个特征列（制表符分隔）：**

1. `up_name` - UP主名称
2. `week_name` - 所属榜单/期数
3. `title` - 视频标题
4. `desc` - 视频简介
5. `view` - 播放量
6. `danmaku` - 弹幕数
7. `reply` - 评论数
8. `favorite` - 收藏数
9. `coin` - 投币数
10. `share` - 分享数
11. `like` - 点赞数
12. `rcmd_reason` - 推荐理由
13. `tname` - 分类
14. `his_rank` - 历史排名
15. `dislike` - 不喜欢数
16. `label` - **目标变量（1=正样本，0=负样本）**

### JSON文件格式 (各阶段输出)

```json
{
  "title": "视频标题",
  "bvid": "BV1234567890",
  "tname": "分类",
  "owner": {
    "name": "UP主名",
    "mid": 123456
  },
  "stat": {
    "view": 10000,
    "danmaku": 100,
    "reply": 50,
    "favorite": 20,
    "coin": 15,
    "share": 8,
    "like": 200,
    "his_rank": 1,
    "dislike": 0
  },
  "pubdate": 1609459200,
  "desc": "视频简介",
  "rcmd_reason": "推荐理由",
  "week_name": "第123期",
  "data_source": "weekly" (或 "negative_sample")
}
```

---

## 常见问题

### Q1: 爬虫被限制了怎么办？

**症状：** 收到 `-352` 错误代码

**解决方案：**
1. 脚本会自动提示：请等待15分钟后重新运行
2. 重新运行脚本会自动跳过已下载的文件继续爬
3. 下次会从缺失的期数继续

### Q2: 数据处理失败了怎么办？

**常见原因：**
- 爬虫脚本还没有运行完，或输出目录不存在
- 解决：确保先完成第1步的爬虫采集

**检查清单：**
```
✓ data/周必看/ 目录存在且有 week_*.json 文件
✓ data/正样本/ 目录存在（会自动创建）
✓ data/负样本/ 目录存在且有 JSON 文件
```

### Q3: 如何只重新处理数据而不重新爬虫？

直接运行：
```bash
python data_process/BiliData-Merge-Clean.py
```

这个脚本会自动从 `data/` 目录读取已有的爬虫输出。

### Q4: 能否修改采集的数据量？

**修改负样本采集量：**
- 编辑 `spider/BiliMass-Random-Negative.py`
- 修改 `PAGES_PER_RID` 参数（默认15页）

**修改每周必看采集范围：**
- 编辑 `spider/BiliWeekly-Target.py`
- 修改 `target_numbers` 的筛选条件

---

## 文件组织结构

```
bilibili_project/
├── spider/                        # 爬虫脚本
│   ├── BiliWeekly-Target.py      # ✓ 每周必看爬虫
│   ├── BiliMass-Random.py        # 随机视频爬虫（可选）
│   └── BiliMass-Random-Negative.py # ✓ 负样本爬虫
│
├── data_process/                  # 数据处理脚本
│   ├── BiliData-Engine.py        # 原有分析引擎
│   └── BiliData-Merge-Clean.py   # ✓ 合并清洗综合脚本
│
├── spark_analysis/                # Spark分析脚本
│   ├── data_analysize1.py        # 多维指标统计
│   └── data_analysize2.py        # 机器学习预测
│
├── visualization/                 # 可视化脚本
│   ├── pyecharts_render.py       # HTML大屏生成
│   └── Bilibili_BigData_Dashboard.html
│
└── data/                          # 数据目录
    ├── 周必看/                    # 爬虫输出
    ├── 正样本/                    # 合并的正样本
    ├── 负样本/                    # 合并的负样本
    ├── 数据集合并版.json          # 合并后的完整数据
    └── bilibili.txt               # ✓ 最终TSV文件（Spark输入）
```

---

## 性能指标

| 操作         | 耗时     | 数据量       |
| ------------ | -------- | ------------ |
| 爬取每周必看 | 5-10分钟 | 200-500条    |
| 爬取负样本   | 1-2小时  | 3000-5000条  |
| 数据合并清洗 | < 1分钟  | 3000-6000条  |
| Spark分析    | 2-5分钟  | 取决于数据量 |

---

## 版本历史

- **v2.0** (2024-XX-XX) - 整理后的版本
  - ✨ 新增 BiliMass-Random-Negative.py 负样本爬虫
  - ✨ 新增 BiliData-Merge-Clean.py 综合处理脚本
  - 📝 更新实验报告中的代码示例
  - 🔧 优化代码注释和文档

- **v1.0** - 原始版本
  - 代码分散在 `1/` 文件夹中

---

**祝你数据分析顺利！** 🎉
