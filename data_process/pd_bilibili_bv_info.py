
import json
import pandas as pd

from crawl_bilibili_bv_info_type import MediaInfo
from pd_bilibili_bv_info_type import PdBvInfo, TidInfo


# media_id = 280831838
media_id = 1041916838
data_base_dir = "data"


def map_media_info_to_pd_bv_info(media_info: MediaInfo) -> PdBvInfo:
    """
    Optimized mapping from MediaInfo to PdBvInfo.
    """
    base_fields = [
        'bvid', 'title', 'intro', 'duration', 'ctime', 'pubtime', 'fav_time'
    ]
    data = {key: media_info.get(key) for key in base_fields}
    upper = media_info.get('upper', {})
    data.update({
        'upper_mid': upper.get('mid'),
        'upper_name': upper.get('name')
    })
    view = media_info.get('view', {})
    stat = view.get('stat', {})
    cnt_info = media_info.get('cnt_info', {})
    data['danmaku'] = cnt_info.get('danmaku') or stat.get('danmaku')
    stat_fields = [
        'view', 'reply', 'favorite', 'coin', 'share',
        'his_rank', 'like', 'dislike', 'evaluation'
    ]
    data.update({key: stat.get(key) for key in stat_fields})
    data.update({
        'dynamic': view.get('dynamic'),
        'is_upower_exclusive': view.get('is_upower_exclusive'),
        'tname': view.get('tname_v2') or view.get('tname'),
        'tid': view.get('tid'),
    })
    with open(f"./assets/tinfo.json", 'r', encoding='utf-8') as f:
        tinfo: dict[str, TidInfo] = json.load(f)
    tid_info: TidInfo = tinfo.get(str(data['tid']), {})
    data['ptname'] = tid_info.get('ptname', None)
    tags = media_info.get('tags', [])
    data['tags'] = [tag.get('tag_name') for tag in tags]
    return PdBvInfo(data)


def main():
    """
    Main function to get the favorite list.
    """
    # Load the media list from a file
    media_list_dir = f"{data_base_dir}/media_info_list"
    media_list_file = f"{media_list_dir}/{media_id}.json"
    with open(media_list_file, 'r', encoding='utf-8') as f:
        media_list = json.load(f)
    print(f"Media list loaded from: {media_list_file}")

    # Map the MediaInfo to PdBvInfo
    pd_bv_info_list = [map_media_info_to_pd_bv_info(media) for media in media_list]
    pd_bv_info_df = pd.DataFrame(pd_bv_info_list)
    print(f"PdBvInfo DataFrame created with {len(pd_bv_info_df)} rows")
    # 删除掉具有空值的行
    pd_bv_info_df.dropna(how='any', axis=0, inplace=True)
    print(f"PdBvInfo DataFrame after dropping rows with NaN values: {len(pd_bv_info_df)} rows")
    # 删除重复数据，dvid 相同视为重复
    pd_bv_info_df = pd_bv_info_df.drop_duplicates(subset=['bvid'], keep='first')
    print(f"PdBvInfo DataFrame after dropping duplicate rows: {len(pd_bv_info_df)} rows")

    # Save the DataFrame to a CSV file
    output_file = f"{media_list_dir}/{media_id}.csv"
    output_file_without_header = f"{media_list_dir}/{media_id}_no_header.txt"
    output_file_json = f"{media_list_dir}/{media_id}_simplified.json"
    output_file_json_line = f"{media_list_dir}/{media_id}_simplified_line.json"
    pd_bv_info_df.to_csv(output_file, header=True, index=False, encoding='utf-8') # 不输出表头，不输出序号
    pd_bv_info_df.to_csv(output_file_without_header, header=False, index=False, encoding='utf-8')
    pd_bv_info_df.to_json(output_file_json, orient='records', indent=2, force_ascii=False)
    pd_bv_info_df.to_json(output_file_json_line, orient='records', lines=True, force_ascii=False)
    print(f"PdBvInfo DataFrame saved to: {output_file}")
    print(f"PdBvInfo DataFrame saved to: {output_file_without_header}")
    print(f"PdBvInfo DataFrame saved to: {output_file_json}")
    print(f"PdBvInfo DataFrame saved to: {output_file_json_line}")


if __name__ == "__main__":
    main()