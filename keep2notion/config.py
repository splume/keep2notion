
import os
from urllib.parse import urlencode

RICH_TEXT = "rich_text"
URL = "url"
RELATION = "relation"
NUMBER = "number"
DATE = "date"
FILES = "files"
STATUS = "status"
TITLE = "title"
SELECT = "select"
MULTI_SELECT = "multi_select"

workout_properties_type_dict = {
    "标题":TITLE,
    "距离":NUMBER,
    "运动时长":NUMBER,
    "平均配速":NUMBER,
    "平均心率":NUMBER,
    "最大心率":NUMBER,
    "消耗热量":NUMBER,
    "开始时间":DATE,
    "结束时间":DATE,
    "Id":RICH_TEXT,
    "名字":RICH_TEXT,
    "运动类型":RELATION,
    "我的装备":RELATION,
}

LEGACY_HEATMAP_EMBED_BASE_URL = "https://heatmap.malinkang.com/"
DEFAULT_HEATMAP_PLACEHOLDER_URL = "https://example.com/keep2notion-heatmap"


def get_env_url(name, default=""):
    return (os.getenv(name) or default).strip()


def get_image_upload_url():
    return get_env_url("IMAGE_UPLOAD_URL")


def get_image_base_url():
    return get_env_url("IMAGE_BASE_URL")


def get_heatmap_embed_base_url():
    return get_env_url("HEATMAP_EMBED_BASE_URL")


def get_heatmap_placeholder_url():
    return get_env_url(
        "HEATMAP_PLACEHOLDER_URL",
        get_heatmap_embed_base_url() or DEFAULT_HEATMAP_PLACEHOLDER_URL,
    )


def get_heatmap_embed_url(image_url):
    base_url = get_heatmap_embed_base_url()
    if not base_url:
        return image_url

    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode({'image': image_url})}"


def get_heatmap_search_prefixes():
    prefixes = [
        LEGACY_HEATMAP_EMBED_BASE_URL,
        get_heatmap_embed_base_url(),
        get_heatmap_placeholder_url(),
    ]
    extra_prefixes = get_env_url("HEATMAP_SEARCH_PREFIXES")
    if extra_prefixes:
        prefixes.extend(prefix.strip() for prefix in extra_prefixes.split(","))

    repository = os.getenv("REPOSITORY")
    ref = (os.getenv("REF") or "").split("/")[-1]
    if repository and ref:
        prefixes.extend(
            [
                f"https://raw.githubusercontent.com/{repository}/{ref}/heatmap/",
                f"https://raw.githubusercontent.com/{repository}/{ref}/OUT_FOLDER/",
            ]
        )

    return tuple(prefix for prefix in prefixes if prefix)


def get_date_icon_url(date, type):
    template = os.getenv("DATE_ICON_URL_TEMPLATE")
    if not template:
        return ""
    return template.format(type=type, date=date.strftime("%Y-%m-%d"))
