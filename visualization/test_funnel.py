from pyecharts import options as opts
from pyecharts.charts import Funnel
import pandas as pd
import math

df = pd.read_csv("bilibili_project/output/popular_up.csv")
df = df[df['up'].notnull() & (df['up'] != '') & (df['up'] != ' ')]
df = df.head(8)
max_val = int(df['count'].max())
data = [(str(w), int(c)) for w, c in zip(df['up'], df['count'])]
funnel = (
    Funnel()
    .add("上榜次数", data, sort_="descending", label_opts=opts.LabelOpts(position="inside"), min_=0, max_=max_val)
    .set_global_opts(title_opts=opts.TitleOpts(title="收录次数最多UP主 Top 8"))
)
funnel.render("test_funnel.html")
print("Data:", data)
print("Max val:", max_val)

df_radar = pd.read_csv("bilibili_project/output/label_comparison.csv").fillna(0)
features = ["avg_view", "avg_like", "avg_coin", "avg_favorite", "avg_danmaku"]
max_vals = [math.log10(max(1, df_radar[f].max())) * 1.1 for f in features]
print("Radar Max Logs:", max_vals)

