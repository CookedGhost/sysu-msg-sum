#!/usr/bin/env python3
import json
import os
import argparse
from datetime import datetime

def get_timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def append_to_jsonl(filepath, data):
    with open(filepath, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')

def read_jsonl(filepath):
    records = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
    return records

"""
当需要使用该脚本将JSON对象追加到JSONL文件时，可以先修改以下的 input_json_data，再执行该脚本：
"""
input_json_data = {
    "学院": "此处填写学院的名称如 计算机学院",
    "原始链接": "此处填写原始信息的链接如 https://example.com/article/123",
    "标题": "此处填写信息的标题",
    "核心摘要": "此处填写信息梗概，要求包含关键信息，字数控制在200字以内。"
}

if __name__ == "__main__":
    # 简单测试：生成时间戳
    parser = argparse.ArgumentParser(description="Helper functions for web fetching and JSONL handling")
    parser.add_argument("file", help="Path to JSONL file")
    parser.add_argument("--append", action="store_true", help="JSON object to append to the file")

    args = parser.parse_args()
    if args.append:
        try:
            append_to_jsonl(args.file, input_json_data)
            print(f"Successfully appended to {args.file}")
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
    else:
        records = read_jsonl(args.file)
        print(records)
