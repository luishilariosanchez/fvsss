import datetime
import random
import requests
import re
import threading
import time
from hashlib import md5
from time import time as T
import secrets
from concurrent.futures import ThreadPoolExecutor, as_completed

TOTAL_REQUESTS = 100000
MAX_WORKERS = 50

def hash_data(data: str) -> str:
    return md5(data.encode()).hexdigest()

def calc_gorgon(params: str, data: str, cookies: str) -> str:
    gorgon = hash_data(params)

    if data:
        gorgon += hash_data(data)
    else:
        gorgon += "0" * 32

    if cookies:
        gorgon += hash_data(cookies)
    else:
        gorgon += "0" * 32

    gorgon += "0" * 32
    return gorgon

def reverse_hex(num: int) -> int:
    tmp = hex(num)[2:]
    if len(tmp) < 2:
        tmp = "0" + tmp
    return int(tmp[1:] + tmp[:1], 16)

def rbit(num: int) -> int:
    binary = bin(num)[2:].zfill(8)
    return int(binary[::-1], 2)

def hex_string(num: int) -> str:
    tmp = hex(num)[2:]
    return tmp.zfill(2)

def encrypt_gorgon(data: str) -> dict:
    unix = int(T())
    key = [
        0xDF, 0x77, 0xB9, 0x40, 0xB9, 0x9B, 0x84, 0x83,
        0xD1, 0xB9, 0xCB, 0xD1, 0xF7, 0xC2, 0xB9, 0x85,
        0xC3, 0xD0, 0xFB, 0xC3,
    ]

    param_list = []

    for i in range(0, 12, 4):
        temp = data[8 * i: 8 * (i + 1)]
        for j in range(4):
            H = int(temp[j * 2: (j + 1) * 2], 16)
            param_list.append(H)

    param_list.extend([0x0, 0x6, 0xB, 0x1C])

    param_list.append((unix & 0xFF000000) >> 24)
    param_list.append((unix & 0x00FF0000) >> 16)
    param_list.append((unix & 0x0000FF00) >> 8)
    param_list.append((unix & 0x000000FF) >> 0)

    eor_result_list = [a ^ b for a, b in zip(param_list, key)]

    length = 0x14
    for i in range(length):
        C = reverse_hex(eor_result_list[i])
        D = eor_result_list[(i + 1) % length]
        E = C ^ D
        F = rbit(E)
        H = ((F ^ 0xFFFFFFFF) ^ length) & 0xFF
        eor_result_list[i] = H

    result = "".join(hex_string(param) for param in eor_result_list)
    return {"X-Gorgon": "840280416000" + result, "X-Khronos": str(unix)}

def get_signature(params: str = "", data: str = "", cookies: str = "") -> dict:
    gorgon = calc_gorgon(params, data, cookies)
    return encrypt_gorgon(gorgon)

def get_video_id(link: str) -> str:
    headers = {
        'Connection': 'close',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html'
    }

    try:
        response = requests.get(link, headers=headers, timeout=5)
        page = response.text
        match = re.search(r'"video":\{"id":"(\d+)"', page)
        if match:
            video_id = match.group(1)
            print(f'[+] Video ID: {video_id}')
            return video_id
        else:
            video_id = "7611127276008361224"
            print('[-] No video ID found, using demo ID.')
            return video_id
    except Exception as e:
        video_id = "7611127276008361224"
        print(f'[-] Error getting video ID: {e} — using demo ID.')
        return video_id

def handle_response(resp: dict):
    first_key = next(iter(resp), None)
    if first_key == 'status_code' and resp.get('status_code') == 0:
        extra = resp.get('extra', {})
        log_pb = resp.get('log_pb', {})
        if 'now' in extra and 'impr_id' in log_pb:
            return True
    return False

def send_view(video_id: str, request_num: int):
    url_view = 'https://api16-core-c-alisg.tiktokv.com/aweme/v1/aweme/stats/?ac=WIFI&op_region=VN'
    sig = get_signature()

    random_hex = secrets.token_hex(16)
    headers_view = {
        'Host': 'api16-core-c-alisg.tiktokv.com',
        'Content-Length': '138',
        'Sdk-Version': '2',
        'Passport-Sdk-Version': '5.12.1',
        'X-Tt-Token': f'01{random_hex}0263ef2c096122cc1a97dec9cd12a6c75d81d3994668adfbb3ffca278855dd15c8056ad18161b26379bbf95d25d1f065abd5dd3a812f149ca11cf57e4b85ebac39d - 1.0.0',
        'Content-Type': 'application/x-www-form-urlencoded',
        'User-Agent': 'TikTok 37.0.4 rv:174014 (iPhone; iOS 14.2; ar_SA@calendar=gregorian) Cronet',
        'X-Ss-Stub': '727D102356930EE8C1F61B112F038D96',
        'X-Tt-Store-Idc': 'alisg',
        'X-Tt-Store-Region': 'sa',
        'X-Ss-Dp': '1233',
        'X-Tt-Trace-Id': '00-33c8a619105fd09f13b65546057d04d1-33c8a619105fd09f-01',
        'Accept-Encoding': 'gzip, deflate',
        'X-Khronos': sig['X-Khronos'],
        'X-Gorgon': sig['X-Gorgon'],
        'X-Common-Params-V2': (
            "pass-region=1&pass-route=1"
            "&language=ar"
            "&version_code=17.4.0"
            "&app_name=musical_ly"
            "&vid=0F62BF08-8AD6-4A4D-A870-C098F5538A97"
            "&app_version=17.4.0"
            "&carrier_region=VN"
            "&channel=App%20Store"
            "&mcc_mnc=45201"
            "&device_id=6904193135771207173"
            "&tz_offset=25200"
            "&account_region=VN"
            "&sys_region=VN"
            "&aid=1233"
            "&residence=VN"
            "&screen_width=1125"
            "&uoo=1"
            "&openudid=c0c519b4e8148dec69410df9354e6035aa155095"
            "&os_api=18"
            "&os_version=14.2"
            "&app_language=ar"
            "&tz_name=Asia%2FHo_Chi_Minh"
            "&current_region=VN"
            "&device_platform=iphone"
            "&build_number=174014"
            "&device_type=iPhone14,6"
            "&iid=6958149070179878658"
            "&idfa=00000000-0000-0000-0000-000000000000"
            "&locale=ar"
            "&cdid=D1D404AE-ABDF-4973-983C-CC723EA69906"
            "&content_language="
        ),
    }

    cookie_view = {'sessionid': random_hex}

    start = datetime.datetime(2020, 1, 1, 0, 0, 0)
    end = datetime.datetime(2024, 12, 31, 23, 59, 59)
    delta_seconds = int((end - start).total_seconds())
    random_offset = random.randint(0, delta_seconds)
    random_dt = start + datetime.timedelta(seconds=random_offset)

    data = {
        'action_time': int(time.time()),
        'aweme_type': 0,
        'first_install_time': int(random_dt.timestamp()),
        'item_id': video_id,
        'play_delta': 1,
        'tab_type': 4
    }

    try:
        r = requests.post(url_view, data=data, headers=headers_view, cookies=cookie_view, timeout=0.3)
        if r.status_code == 200:
            print(r.status_code)
    except Exception as e:
        pass

def main():
    link = "https://www.tiktok.com/@heliii90/video/7611128839120424210"
    video_id = get_video_id(link)

    start = time.time()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(send_view, video_id, i) for i in range(TOTAL_REQUESTS)]
        for future in as_completed(futures):
            future.result()

    end = time.time()
    print(f"✅ Completed {TOTAL_REQUESTS} requests in {end-start:.2f} seconds")

if __name__ == "__main__":
    main()
