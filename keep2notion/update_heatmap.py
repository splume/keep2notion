import hashlib
import os
import shutil
import subprocess
import uuid
from datetime import datetime

from keep2notion.utils import (
    get_property_value,
)
from keep2notion.notion_helper import NotionHelper
from keep2notion.config import get_heatmap_embed_url


def get_file(dir):
    dir = f"./{dir}"
    if os.path.exists(dir) and os.path.isdir(dir):
        entries = os.listdir(dir)
        file_name = entries[0] if entries else None
        return file_name
    else:
        print("OUT_FOLDER does not exist.")
        return None


def run_command(command):
    """执行命令行命令并返回结果"""
    try:
        result = subprocess.run(command, shell=True, check=True, text=True, capture_output=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败: {e}")
        print(f"错误输出: {e.stderr}")
        return None


def main():
    year = os.getenv("YEAR") or str(datetime.now().year)
    mode = os.getenv("HEATMAP_MODE", "all")

    if mode in ("all", "update"):
        update_heatmap("OUT_FOLDER", notion_helper.heatmap_block_id)
    if mode == "update":
        update_type_heatmaps()
        return

    generate_type_heatmaps(year, update_notion=mode == "all")


def get_title_dir(title):
    hash_object = hashlib.sha256(title.encode("utf-8"))
    hashed_name = hash_object.hexdigest()[:10]  # 使用前10个字符以减少长度
    return f"heatmap/{hashed_name}"


def generate_type_heatmaps(year, update_notion=True):
    types = notion_helper.query_all(notion_helper.type_database_id)
    for type in types:
        page_id = type.get("id")
        notion_token = os.getenv("NOTION_TOKEN")
        title = get_property_value(type.get("properties").get("标题"))
        unit = get_property_value(type.get("properties").get("单位"))
        print(unit)
        database_filter = f'{{"property": "运动类型", "relation": {{"contains": "{page_id}"}}}}'
        command = f'github_heatmap notion --notion_token {notion_token} --database_id {notion_helper.workout_database_id} --database_filter \'{database_filter}\' --date_prop_name 开始时间 --value_prop_name 值 --unit {unit} --year {year} --me {title} --without-type-name --background-color=#FFFFFF --track-color=#ACE7AE --special-color1=#69C16E --special-color2=#549F57 --dom-color=#EBEDF0 --text-color=#000000'
        run_command(command)
        # 创建以title命名的文件夹
        title_dir = get_title_dir(title)
        # 如果目录存在则删除
        if os.path.exists(title_dir):
            shutil.rmtree(title_dir)
        os.makedirs(title_dir)
        # 将OUT_FOLDER中的notion.svg移动到title文件夹
        source_file = "OUT_FOLDER/notion.svg"
        if os.path.exists(source_file):
            destination_file = f"{title_dir}/{uuid.uuid4()}.svg"
            os.rename(source_file, destination_file)
            if update_notion:
                heatmap_block_id = notion_helper.search_heatmap(page_id)
                if heatmap_block_id:
                    update_heatmap(title_dir, heatmap_block_id)


def update_type_heatmaps():
    types = notion_helper.query_all(notion_helper.type_database_id)
    for type in types:
        page_id = type.get("id")
        title = get_property_value(type.get("properties").get("标题"))
        title_dir = get_title_dir(title)
        heatmap_block_id = notion_helper.search_heatmap(page_id)
        if heatmap_block_id:
            update_heatmap(title_dir, heatmap_block_id)


def update_heatmap(dir, block_id):
    image_file = get_file(dir)
    if image_file:
        ref = (os.getenv("REF") or "").split("/")[-1]
        repository = os.getenv("REPOSITORY")
        if repository and ref:
            image_url = f"https://raw.githubusercontent.com/{repository}/{ref}/{dir}/{image_file}"
        else:
            image_url = None
        if block_id and image_url:
            heatmap_url = get_heatmap_embed_url(image_url)
            notion_helper.update_heatmap(block_id=block_id, url=heatmap_url)

notion_helper = NotionHelper()

if __name__ == "__main__":
    main()
