import json
from pathlib import Path

CONFIG_PATH = Path("config/config.json")

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"items": [], "n_days": 7}

def save_config(config: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def load_name_map(path="config/name_map_spaces.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_item_id_by_chinese_name(name_map, input_name):
    for en_id, zh in name_map.items():
        if zh == input_name:
            return en_id
    return input_name  # 若输入的是英文则直接返回