#!/usr/bin/env python3
import json
import os
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

if __name__ == "__main__":
    # 简单测试：生成时间戳
    print(get_timestamp())