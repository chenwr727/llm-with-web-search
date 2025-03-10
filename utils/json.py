import json
import re
from typing import Dict, Union


def parse_result_to_json(result: str) -> Union[Dict[str, any], str, None]:
    """
    解析结果字符串为JSON格式。

    参数:
    - result (str): 结果字符串，可能包含JSON格式的数据。

    返回:
    - Union[Dict[str, any], str, None]: 解析后的JSON数据，如果解析失败则返回字符串。
    """
    text = remove_trailing_commas(result)
    json_data = extract_json_from_text(text)

    if json_data is None:
        return None

    try:
        parsed_json = json.loads(json_data)
        return parsed_json
    except json.JSONDecodeError:
        return None


def remove_trailing_commas(text: str) -> str:
    """
    去除 JSON 字符串中的尾随逗号。

    参数:
    - text (str): 待处理的文本字符串。

    返回:
    - str: 去除尾随逗号后的文本字符串。
    """
    return re.sub(r",\s*(?=\]|\})", "", text)


def extract_json_from_text(text: str) -> str:
    """
    使用正则表达式提取文本中的最外层 JSON 对象或数组。
    - 匹配 {} 或 [] 包围的部分

    参数:
    - text (str): 待处理的文本字符串。

    返回:
    - str: 提取到的最外层 JSON 对象或数组，如果没有找到则返回 None。
    """
    json_pattern = r"(\{.*\}|\[.*\])"
    match = re.search(json_pattern, text, re.DOTALL)
    if match:
        return match.group(0).strip()
    return None
