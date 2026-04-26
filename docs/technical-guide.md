# Python 脚本调用指南

## helper.py 函数说明

### append_to_jsonl 函数

**用途**：将 JSON 对象追加到 JSONL 文件

**函数签名**：
```python
append_to_jsonl(file_path, data)
```

**参数说明**：
- `file_path`：JSONL 文件路径（字符串）
- `data`：要追加的 JSON 对象（字典）

**返回值**：无

**使用场景**：
- 保存抓取结果到 `.temp/fetch_{timestamp}.jsonl`
- 保存汇总结果到 `.temp/summaries_{timestamp}.jsonl`

**调用示例**：
```python
from scripts.helper import append_to_jsonl

# 保存抓取结果
data = {
    'url': 'https://example.com',
    'title': '示例标题',
    'snippet': '示例摘要',
    'full_text': '完整文本'
}
append_to_jsonl('.temp/fetch_20260426_163822.jsonl', data)

# 保存汇总结果
summary = {
    'dep': '示例学院',
    'url': 'https://example.com',
    'abstract': '核心摘要',
    'diff': '差异点',
    'special': '独特信息'
}
append_to_jsonl('.temp/summaries_20260426_163822.jsonl', summary)
```

**注意事项**：
- 文件不存在时会自动创建
- 每次调用都会追加一行（JSON 对象 + 换行符）
- 确保 `data` 是字典类型
- 确保 `file_path` 目录存在

## generate_xlsx.py 函数说明

### jsonl_to_xlsx 函数

**用途**：将 JSONL 文件转换为 EXCEL 文件

**函数签名**：
```python
jsonl_to_xlsx(jsonl_path, xlsx_path, other_msgs)
```

**参数说明**：
- `jsonl_path`：汇总结果 JSONL 文件路径（字符串）
  - 格式：`.temp/summaries_{timestamp}.jsonl`
  - 内容：每行一个 JSON 对象，包含学院对比信息

- `xlsx_path`：输出 EXCEL 文件路径（字符串）
  - 格式：`comparison_{timestamp}.xlsx`
  - 位置：当前skill目录根目录

- `other_msgs`：补充的重要对比发现（字符串数组）
  - 格式：列表，包含3-5个字符串
  - 内容：最重要的对比发现、趋势、特点等

**返回值**：无（直接生成 EXCEL 文件）

**调用示例**：
```python
from scripts.generate_xlsx import jsonl_to_xlsx

jsonl_to_xlsx(
    '.temp/summaries_20260426_163822.jsonl',
    'comparison_20260426_163822.xlsx',
    [
        '发现1：三个学院均重视人才培养',
        '发现2：海外优青项目成为重要人才引进渠道',
        '发现3：产教融合在工科学院表现突出'
    ]
)
```

**生成的 EXCEL 文件特性**：
- 自动调整列宽
- 单元格自动换行
- 首行冻结
- 粗体表头
- 附加发现内容合并为一行

**注意事项**：
- 确保 `jsonl_path` 文件存在且格式正确
- 确保 `other_msgs` 是列表类型，包含3-5个字符串
- 输出文件会覆盖已存在的同名文件
- 依赖 openpyxl 库（如未安装会提示错误）

## 常见问题

### Q1：如何导入这些函数？

**A**：
```python
import sys
sys.path.append('scripts')

from helper import append_to_jsonl
from generate_xlsx import jsonl_to_xlsx
```

### Q2：JSONL 文件格式错误怎么办？

**A**：检查以下几点：
- 每行是否为一个有效的 JSON 对象
- 字段名称是否与规范一致
- 是否有多余的逗号或语法错误

### Q3：如何处理中文字符？

**A**：
- 确保文件使用 UTF-8 编码
- 在 Python 中使用 `encoding='utf-8'` 参数
- JSON 对象中的字符串使用 `ensure_ascii=False`

### Q4：EXCEL 文件打不开怎么办？

**A**：
- 检查 openpyxl 库是否安装：`pip install openpyxl`
- 检查文件是否完整生成
- 检查是否有权限访问该文件

### Q5：如何调试生成过程？

**A**：
- 检查 JSONL 文件内容是否正确
- 检查函数调用参数是否正确
- 查看函数输出错误信息
- 逐行检查 JSON 对象格式

## 错误处理

### 常见错误及解决方法

**错误1：FileNotFoundError**
- 原因：文件或目录不存在
- 解决：检查路径是否正确，确保目录存在

**错误2：JSONDecodeError**
- 原因：JSON 格式错误
- 解决：检查 JSONL 文件每行格式是否正确

**错误3：ImportError**
- 原因：缺少依赖库
- 解决：安装 openpyxl：`pip install openpyxl`

**错误4：PermissionError**
- 原因：没有文件写入权限
- 解决：检查文件权限，确保有写入权限
