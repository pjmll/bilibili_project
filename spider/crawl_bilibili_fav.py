import json
import os

import requests
from retry import retry
from fake_useragent import UserAgent

from crawl_bilibili_fav_type import FavRequestParams, FavResponse

cookie = "browser_resolution=1470-839; b_lsid=F8A755C8_1968FC8FBB8; home_feed_column=5; CURRENT_FNVAL=4048; bp_t_offset_383882738=1061910954331078656; bili_ticket=eyJhbGciOiJIUzI1NiIsImtpZCI6InMwMyIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NDYyNzc3MDcsImlhdCI6MTc0NjAxODQ0NywicGx0IjotMX0.9CLb5CQ1QBJWUmmxHM0EyQem1EsVPMOPubCtEIYBuRA; bili_ticket_expires=1746277647; buvid4=4C9A1DD9-5C64-E62F-10D3-755E5D6ACB4B39057-024102923-JCm%2FOCHxuN3uFT1IC5OxHQ%3D%3D; DedeUserID=383882738; DedeUserID__ckMd5=02fade6134ceefcf; SESSDATA=5a6f9c04%2C1761556533%2Cfa6d1%2A42CjCS7wLo4X2ZCZjh6wbB9OBcUIclZAQ-4rKd0pZ7mdPAJwXWFSdbD273WgdjbykY9z4SVmREVmZ1NVE0R3RCQUlPSVNQU2RIVVVubkRFYnhla2NNcV9aZmlVT1ZCRU9aZjQ1d1c1ZzZMcUpkMHZhYll1RENSVmFWUGFDd3hNTF9SWDlEaUYxODhRIIEC; bili_jct=4a0ae1f010d80f08a76cb63ca203db12; sid=5575758l; enable_feed_channel=ENABLE; enable_web_push=DISABLE; header_theme_version=CLOSE; CURRENT_QUALITY=120; buvid_fp=c607d939df9ee9460cbd93e910879fed; buvid_fp_plain=undefined; fingerprint=c607d939df9ee9460cbd93e910879fed; PVID=2; LIVE_BUVID=AUTO2517306380199102; hit-dyn-v2=1; rpdid=|(u))kummuJu0J'u~J|kRllR|; _uuid=2CD765E6-F9B3-349F-61018-486F887CC10AE38885infoc; b_nut=1730236994; buvid3=5D411042-5765-264D-51FF-6DC64D5F966D94021infoc"
# media_id = 280831838
media_id = 1041916838
web_location = "333.1387"
data_base_dir = "data"


@retry()
def get_fav_json(url: str, params: FavRequestParams, cookie: str):
    """
    Get the favorite list from the given URL.
    """
    random_UA = UserAgent().random
    headers = {
        "User-Agent": random_UA,
        "Cookie": cookie,
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

def main():
    """
    Main function to get the favorite list.
    """
    url = "https://api.bilibili.com/x/v3/fav/resource/list"
    basic_params = {
        "pn": 1,
        "ps": 40,
        "order": "mtime",
        "keyword": "",
        "type": 0,
        "tid": 0,
        "platform": "web",
        "web_location": web_location
    }
    pn = 1
    medias = []
    while True:
        params = FavRequestParams(**basic_params)
        params["media_id"] = media_id
        params["pn"] = pn
        fav_json = get_fav_json(url, params, cookie)
        fav_response = FavResponse(**fav_json)
        beautified_json = json.dumps(fav_response, indent=2, ensure_ascii=False)
        # Save the response to a file
        fav_list_dir = f"{data_base_dir}/fav_list"
        if not os.path.exists(fav_list_dir):
            os.makedirs(fav_list_dir)
        fav_list_file = f"{fav_list_dir}/{media_id}-{params['pn']}.json"
        with open(fav_list_file, 'w', encoding='utf-8') as f:
            f.write(beautified_json)
        print(f"Favorite list {pn} saved to: {fav_list_file}")
        # Extend the media list
        medias.extend(fav_response["data"]["medias"])
        print(f"Fetched page: {pn}, total medias: {len(fav_response['data']['medias'])}")
        if not fav_response["data"]["has_more"]:
            break
        pn += 1
    print(f"Total medias fetched: {len(medias)}")
    # Save the media list to a file
    media_list_dir = f"{data_base_dir}/media_list"
    if not os.path.exists(media_list_dir):
        os.makedirs(media_list_dir)
    media_list_file = f"{media_list_dir}/{media_id}.json"
    with open(media_list_file, 'w', encoding='utf-8') as f:
        f.write(json.dumps(medias, indent=2, ensure_ascii=False))
    print(f"Media list saved to: {media_list_file}")


if __name__ == "__main__":
    main()