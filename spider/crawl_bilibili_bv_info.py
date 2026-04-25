import json
import os

from crawl_bilibili_fav_type import FavMedia
from utils.request_bv import get_bv_view, get_bv_tags
from crawl_bilibili_bv_info_type import MediaInfo


# media_id = 280831838
media_id = 1041916838
data_base_dir = "data"


def main():
    """
    Main function to get the favorite list.
    """
    # Load the media list from the JSON file
    media_list_dir = f"{data_base_dir}/media_list"
    if not os.path.exists(media_list_dir):
        os.makedirs(media_list_dir)
    with open(f"{media_list_dir}/{media_id}.json", "r", encoding="utf-8") as f:
        media_list: list[FavMedia] = json.load(f)
        media_info_list: list[MediaInfo] = []
        for media in media_list:
            bvid = media["bvid"]
            title = media["title"]
            print(f"Title: {title}, BVID: {bvid}")
            # Here you can add the code to fetch the view count and tags using the bvid
            print(f"Fetching view count and tags for BVID: {bvid}")
            view_response = get_bv_view(bvid)
            tags_response = get_bv_tags(bvid)
            view = {}
            tags = []
            try:
                view = view_response["data"]
                tags = tags_response["data"]
            except KeyError as e:
                print(f"Error fetching data for BVID: {bvid}, missing key: {e}")
            media_info = MediaInfo(
                **media,
                view=view,
                tags=tags
            )
            media_info_list.append(media_info)
        # Save the media info to a file
        media_info_dir = f"{data_base_dir}/media_info_list"
        if not os.path.exists(media_info_dir):
            os.makedirs(media_info_dir)
        media_info_file = f"{media_info_dir}/{media_id}.json"
        with open(media_info_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(media_info_list, indent=2, ensure_ascii=False))
        print(f"Media info list saved to: {media_info_file}")
        print(f"Total media info fetched: {len(media_info_list)}")


if __name__ == "__main__":
    main()