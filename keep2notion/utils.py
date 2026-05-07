import calendar
from datetime import datetime
from datetime import timedelta
import hashlib
import os
import requests
from keep2notion.config import (
    RICH_TEXT,
    URL,
    RELATION,
    NUMBER,
    DATE,
    FILES,
    STATUS,
    TITLE,
    SELECT,
    MULTI_SELECT,
    get_image_base_url,
    get_image_upload_url,
)
import pendulum

MAX_LENGTH = (
    1024  # NOTION 2000个字符限制https://developers.notion.com/reference/request-limits
)


def get_heading(level, content):
    if level == 1:
        heading = "heading_1"
    elif level == 2:
        heading = "heading_2"
    else:
        heading = "heading_3"
    return {
        "type": heading,
        heading: {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": content[:MAX_LENGTH],
                    },
                }
            ],
            "color": "default",
            "is_toggleable": False,
        },
    }


def get_table_of_contents():
    """获取目录"""
    return {"type": "table_of_contents", "table_of_contents": {"color": "default"}}


def get_title(content):
    return {"title": [{"type": "text", "text": {"content": content[:MAX_LENGTH]}}]}


def get_rich_text(content):
    return {"rich_text": [{"type": "text", "text": {"content": content[:MAX_LENGTH]}}]}


def get_url(url):
    return {"url": url}


def get_file(url):
    return {"files": [{"type": "external", "name": "Cover", "external": {"url": url}}]}


def get_multi_select(names):
    return {"multi_select": [{"name": name} for name in names]}


def get_relation(ids):
    return {"relation": [{"id": id} for id in ids]}


def get_date(start, end=None):
    return {
        "date": {
            "start": start,
            "end": end,
            "time_zone": "Asia/Shanghai",
        }
    }


def get_icon(url):
    return {"type": "external", "external": {"url": url}}


def get_select(name):
    return {"select": {"name": name}}


def get_number(number):
    return {"number": number}


def get_quote(content):
    return {
        "type": "quote",
        "quote": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": content[:MAX_LENGTH]},
                }
            ],
            "color": "default",
        },
    }


def get_callout(content, style, colorStyle, reviewId):
    # 根据不同的划线样式设置不同的emoji 直线type=0 背景颜色是1 波浪线是2
    emoji = "〰️"
    if style == 0:
        emoji = "💡"
    elif style == 1:
        emoji = "⭐"
    # 如果reviewId不是空说明是笔记
    if reviewId != None:
        emoji = "✍️"
    color = "default"
    # 根据划线颜色设置文字的颜色
    if colorStyle == 1:
        color = "red"
    elif colorStyle == 2:
        color = "purple"
    elif colorStyle == 3:
        color = "blue"
    elif colorStyle == 4:
        color = "green"
    elif colorStyle == 5:
        color = "yellow"
    return {
        "type": "callout",
        "callout": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": content[:MAX_LENGTH],
                    },
                }
            ],
            "icon": {"emoji": emoji},
            "color": color,
        },
    }


def get_rich_text_from_result(result, name):
    return result.get("properties").get(name).get("rich_text")[0].get("plain_text")


def get_number_from_result(result, name):
    return result.get("properties").get(name).get("number")


def format_time(time):
    """将秒格式化为 xx时xx分格式"""
    result = ""
    hour = time // 3600
    if hour > 0:
        result += f"{hour}时"
    minutes = time % 3600 // 60
    if minutes > 0:
        result += f"{minutes}分"
    return result


def format_date(date, format="%Y-%m-%d %H:%M:%S"):
    return date.strftime(format)


def timestamp_to_date(timestamp):
    """时间戳转化为date"""
    return datetime.utcfromtimestamp(timestamp) + timedelta(hours=8)


def get_first_and_last_day_of_month(date):
    # 获取给定日期所在月的第一天
    first_day = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 获取给定日期所在月的最后一天
    _, last_day_of_month = calendar.monthrange(date.year, date.month)
    last_day = date.replace(
        day=last_day_of_month, hour=0, minute=0, second=0, microsecond=0
    )+ timedelta(days=1)

    return first_day, last_day


def get_first_and_last_day_of_year(date):
    # 获取给定日期所在年的第一天
    first_day = date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    # 获取给定日期所在年的最后一天
    last_day = date.replace(month=12, day=31, hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    return first_day, last_day


def get_first_and_last_day_of_week(date):
    # 获取给定日期所在周的第一天（星期一）
    first_day_of_week = (date - timedelta(days=date.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # 获取给定日期所在周的最后一天（星期日）
    last_day_of_week = first_day_of_week + timedelta(days=7)

    return first_day_of_week, last_day_of_week


def get_properties(dict1, dict2):
    properties = {}
    for key, value in dict1.items():
        type = dict2.get(key)
        if value == None:
            continue
        property = None
        if type == TITLE:
            property = {
                "title": [
                    {"type": "text", "text": {"content": value[:MAX_LENGTH]}}
                ]
            }
        elif type == RICH_TEXT:
            property = {
                "rich_text": [
                    {"type": "text", "text": {"content": value[:MAX_LENGTH]}}
                ]
            }
        elif type == NUMBER:
            property = {"number": value}
        elif type == STATUS:
            property = {"status": {"name": value}}
        elif type == FILES:
            property = {"files": [{"type": "external", "name": "Cover", "external": {"url": value}}]}
        elif type == DATE:
            property = {
                "date": {
                    "start": pendulum.from_timestamp(
                        value, tz="Asia/Shanghai"
                    ).to_datetime_string(),
                    "time_zone": "Asia/Shanghai",
                }
            }
        elif type==URL:
            property = {"url": value}        
        elif type==SELECT:
            property = {"select": {"name": value}}        
        elif type==MULTI_SELECT:
            property = {"multi_select": [{"name": name} for name in value]}
        elif type == RELATION:
            property = {"relation": [{"id": id} for id in value]}
        if property:
            properties[key] = property
    return properties


def get_property_value(property):
    """从Property中获取值"""
    type = property.get("type")
    print(type)
    content = property.get(type)
    if content is None:
        return None
    if type == "title" or type == "rich_text":
        if(len(content)>0):
            return content[0].get("plain_text")
        else:
            return None
    elif type == "status" or type == "select":
        return content.get("name")
    elif type == "files":
        # 不考虑多文件情况
        if len(content) > 0 and content[0].get("type") == "external":
            return content[0].get("external").get("url")
        else:
            return None
    elif type == "date":
        return str_to_timestamp(content.get("start"))
    elif type == "formula":
        return content.get(content.get("type"))
    else:
        return content


def str_to_timestamp(date):
    if date == None:
        return 0
    dt = pendulum.parse(date)
    # 获取时间戳
    return int(dt.timestamp())

def upload_image(file_path):
    upload_url = get_image_upload_url()
    image_base_url = get_image_base_url()
    if not upload_url or not image_base_url:
        return None

    with open(file_path, 'rb') as file:
        files = {'file': file}
        response = requests.post(upload_url, files=files)
        print(response.text)
        if response.status_code == 200:
            src = response.json()[0].get("src")
            url = image_base_url.rstrip('/') + "/" + src.lstrip("/")
            return url
        else:
            print("File upload failed")
            return None

def url_to_md5(url):
    # 创建一个md5哈希对象
    md5_hash = hashlib.md5()

    # 对URL进行编码，准备进行哈希处理
    # 默认使用utf-8编码
    encoded_url = url.encode('utf-8')

    # 更新哈希对象的状态
    md5_hash.update(encoded_url)

    # 获取十六进制的哈希表示
    hex_digest = md5_hash.hexdigest()

    return hex_digest

def download_image(url, save_dir="cover"):
    # 确保目录存在，如果不存在则创建
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    file_name = url_to_md5(url) + ".jpg"
    save_path = os.path.join(save_dir, file_name)

    # 检查文件是否已经存在，如果存在则不进行下载
    if os.path.exists(save_path):
        print(f"File {file_name} already exists. Skipping download.")
        return save_path

    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=128):
                file.write(chunk)
        print(f"Image downloaded successfully to {save_path}")
    else:
        print(f"Failed to download image. Status code: {response.status_code}")
    return save_path

def upload_cover(url):
    cover_file = download_image(url)
    return f"https://raw.githubusercontent.com/{os.getenv('REPOSITORY')}/{os.getenv('REF').split('/')[-1]}/{cover_file}"
#     return upload_image(cover_file)

def get_embed(url):
    return {"type": "embed", "embed": {"url": url}}
