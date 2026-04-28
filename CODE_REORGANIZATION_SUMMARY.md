## B站爬虫和数据处理模块整理方案

### 一、代码整理情况

本次整理将文件夹 `1/` 中的爬虫和数据处理代码按功能整合到项目的标准目录结构中。

#### 1. **爬虫脚本整理** (`spider/` 文件夹)

文件夹 `1/` 中的爬虫代码已整理到 `spider/` 目录：

- **BiliWeekly-Target.py** - 《每周必看》爬虫
  - 原始文件：`1/week.py` 
  - 功能：定向爬取B站官方《每周必看》、《热门排行榜》、《入站必刷》等热门榜单的爆款视频（正样本）
  - 输出：JSON格式的视频数据，标记为 `data_source: "weekly"`

- **BiliMass-Random-Negative.py** - 普通视频爬虫（负样本）
  - 原始文件：`1/neigative.py` → 重新编写为 `BiliMass-Random-Negative.py`
  - 功能：从B站全站70+个细分分区采集普通视频作为负样本（对照样本）
  - 输出：JSON格式的视频数据，标记为 `data_source: "negative_sample"`
  - 特点：采用字典结构边爬取边去重，确保采集的视频无重复

#### 2. **数据处理脚本整理** (`data_process/` 文件夹)

文件夹 `1/` 中的数据处理代码已整合到单一综合脚本：

- **BiliData-Merge-Clean.py** - 数据合并与清洗综合脚本
  - 原始文件：`1/merge.py` + `1/preprocess.py` 合并
  - 功能：包含9个核心处理步骤
    1. **提取正样本** - 从各榜单JSON中提取标准化视频列表
    2. **合并每周必看数据** - 整合所有周必看期数的数据
    3. **合并热门排行榜数据** - 整合热门排行榜的数据
    4. **合并入站必刷数据** - 整合入站必刷的数据
    5. **正样本合并** - 将多个正样本源合并为单一JSON
    6. **正负样本合并** - 合并正负样本并进行联合去重
    7. **数据扁平化** - 将嵌套的JSON结构展平为DataFrame
    8. **异常值过滤与文本规范化** - 清洗数据并规范化文本
    9. **TSV格式导出** - 导出为Spark/Hadoop兼容的TSV文件
  - 输出：无表头TSV文件，包含16个特征列

### 二、目录结构变化

**整理前：**
```
bilibili_project/
├── 1/
│   ├── main.py (示例脚本，无实用价值)
│   ├── week.py (爬虫)
│   ├── neigative.py (爬虫)
│   ├── merge.py (合并)
│   ├── preprocess.py (预处理)
│   ├── popular_page.py (统计脚本)
│   └── README.md
├── spider/
│   ├── BiliMass-Random.py
│   └── BiliWeekly-Target.py
└── data_process/
    └── BiliData-Engine.py
```

**整理后：**
```
bilibili_project/
├── spider/
│   ├── BiliWeekly-Target.py (更新的爬虫)
│   ├── BiliMass-Random.py (原有)
│   └── BiliMass-Random-Negative.py (新增，来自1/neigative.py)
├── data_process/
│   ├── BiliData-Engine.py (原有)
│   └── BiliData-Merge-Clean.py (新增，合并1/merge.py + 1/preprocess.py)
├── data/
│   ├── 周必看/ (爬虫输出)
│   ├── 正样本/
│   │   ├── 每周必看数据集.json
│   │   ├── 热门排行榜数据集.json
│   │   ├── 入站必刷数据集.json
│   │   └── 飞桨数据集.json
│   ├── 负样本/
│   │   └── 负样本数据集_普通视频.json
│   ├── 数据集合并版.json (merge输出)
│   └── bilibili.txt (最终TSV文件)
└── 1/ (保留原文件作为参考/备份)
```

### 三、数据处理流程

```
spider/脚本输出 (JSON)
    ↓
    ├─ BiliWeekly-Target.py → 每周必看数据
    ├─ (其他榜单爬虫) → 热门排行榜、入站必刷数据
    └─ BiliMass-Random-Negative.py → 普通视频数据
    ↓
data_process/BiliData-Merge-Clean.py
    ├─ [步骤1-3] 提取并合并正样本 → 正样本/文件夹
    ├─ [步骤4-5] 合并正负样本并去重 → 数据集合并版.json
    ├─ [步骤6-8] 扁平化、过滤、清洗 → DataFrame
    └─ [步骤9] 导出TSV格式 → data/bilibili.txt
    ↓
spark_analysis/脚本输入 (TSV)
    ↓
输出分析结果 (CSV)
```

### 四、代码功能映射表

| 原始文件                     | 新位置        | 新文件名                    | 功能                   |
| ---------------------------- | ------------- | --------------------------- | ---------------------- |
| 1/week.py                    | spider/       | BiliWeekly-Target.py        | 每周必看爬虫           |
| 1/neigative.py               | spider/       | BiliMass-Random-Negative.py | 负样本爬虫             |
| 1/merge.py + 1/preprocess.py | data_process/ | BiliData-Merge-Clean.py     | 数据合并与清洗         |
| 1/popular_page.py            | 废弃          | -                           | 统计脚本（功能已整合） |
| 1/main.py                    | 废弃          | -                           | PyCharm示例脚本        |

### 五、使用说明

#### 1. 数据采集阶段
```bash
# 爬取每周必看数据
python spider/BiliWeekly-Target.py

# 爬取普通视频作为负样本
python spider/BiliMass-Random-Negative.py
```

#### 2. 数据处理阶段
```bash
# 一键完成数据合并、清洗、导出
python data_process/BiliData-Merge-Clean.py
```

#### 3. 数据分析阶段
```bash
# Spark分析（处理data/bilibili.txt）
python spark_analysis/data_analysize1.py
python spark_analysis/data_analysize2.py
```

### 六、实验报告更新

已更新 `WHU_course_Template_LaTeX-main/main.tex` 中的以下部分：

1. **模块说明** - 更新了 spider/ 和 data_process/ 的功能描述
2. **数据获取模块** - 更新了关于 BiliMass-Random-Negative.py 的描述
3. **数据处理模块** - 完整更新了 BiliData-Merge-Clean.py 的功能和代码示例

### 七、特点和优化

- ✅ **模块化设计** - 爬虫和处理逻辑独立分离
- ✅ **功能完整** - 合并脚本包含从多源合并到最终导出的全流程
- ✅ **向后兼容** - 保留原有的spider脚本（BiliMass-Random.py等）
- ✅ **易于维护** - 每个脚本职责单一，注释详细
- ✅ **文档完善** - 更新了实验报告中的所有相关部分
