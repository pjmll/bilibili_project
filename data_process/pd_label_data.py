import json
import os
import pandas as pd


data_base_dir = "data"
media_info_list_dir = f"{data_base_dir}/media_info_list"

dfs = []
media_ids = [280831838, 1041916838]

for index in range(len(media_ids)):
    media_id = media_ids[index]
    # Load the media list from a file
    media_list_dir = f"{data_base_dir}/media_info_list"
    if not os.path.exists(media_list_dir):
        os.makedirs(media_list_dir)
    csv_file = f"{data_base_dir}/media_info_list/{media_id}.csv"
    df = pd.read_csv(csv_file)
    df['label'] = index
    dfs.append(df)
# Save the media list to a file
media_label_dir = f"{data_base_dir}/media_label"
if not os.path.exists(media_label_dir):
    os.makedirs(media_label_dir)
media_label_file = f"{media_label_dir}/{'_'.join([str(mid) for mid in media_ids])}"
pd.concat(dfs).to_json(media_label_file+'.json', orient='records', lines=True, force_ascii=False)
pd.concat(dfs).to_csv(media_label_file+'.csv', index=False)
print(f"Media list saved to: {media_label_file}.csv")
