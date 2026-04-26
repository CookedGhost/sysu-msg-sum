# 输出格式说明

## 文件命名格式

### 输出 EXCEL 文件
- **格式**：`comparison_{timestamp}.xlsx`
- **示例**：`comparison_20260426_163822.xlsx`
- **位置**：当前skill目录根目录
- **timestamp 格式**：`YYYYMMDD_HHMMSS`

### 临时 JSONL 文件
- **抓取结果**：`.temp/fetch_{timestamp}.jsonl`
- **汇总结果**：`.temp/summaries_{timestamp}.jsonl`
- **位置**：`.temp/` 目录

## Python 脚本调用参数

### generate_xlsx.py 的 jsonl_to_xlsx 函数

**函数签名**：
```python
jsonl_to_xlsx(jsonl_path, xlsx_path, other_msgs)
```

**参数说明**：
- `jsonl_path`：汇总结果 JSONL 文件路径
  - 格式：`.temp/summaries_{timestamp}.jsonl`
  - 内容：每行一个 JSON 对象，包含学院对比信息

- `xlsx_path`：输出 EXCEL 文件路径
  - 格式：`comparison_{timestamp}.xlsx`
  - 位置：当前skill目录根目录

- `other_msgs`：补充的重要对比发现
  - 格式：字符串数组
  - 内容：最重要的对比发现、趋势、特点等

**调用示例**：
```python
jsonl_to_xlsx(
    '.temp/summaries_20260426_163822.jsonl',
    'comparison_20260426_163822.xlsx',
    [
        '发现1：...',
        '发现2：...',
        '发现3：...'
    ]
)
```

## 输出内容格式

### EXCEL 表格结构

**列结构**（从左到右）：
1. **学院**：学院名称
2. **原始链接**：信息的原始链接
3. **核心摘要**：核心摘要
4. **不同之处**：该学院与其他学院的主要差异
5. **独特亮点**：该学院的独特信息或亮点

**格式要求**：
- 单元格自动换行
- 首行冻结
- 列宽自动调整
- 粗体表头

**附加内容**：
- 表格下方添加 `other_msgs` 的内容
- 每个发现合并为一行

### JSONL 文件结构

#### fetch_{timestamp}.jsonl（抓取结果）

**每行格式**：
```json
{
  "url": "信息的原始链接",
  "title": "信息标题（完整准确）",
  "snippet": "与主题相关的文本片段（不超过 500 字）",
  "details": "详细内容（可选，如信息丰富可扩展到 1000 字）",
  "path": "跳转路径（如：主页 -> 学工通知 -> 具体通知）",
  "publish_date": "发布日期（如能提取，格式：YYYY-MM-DD）",
  "related_urls": "相关链接数组（可选）"
}
```

**错误记录格式**：
```json
{
  "url": "失败的URL",
  "error": "失败原因"
}
```

**字段说明**：
- `url`：信息的原始链接，必填
- `title`：信息标题，必填，从页面 `<title>` 或 h1 提取
- `snippet`：与主题相关的文本片段，不超过 500 字，必填
- `details`：详细内容，可选，如信息丰富可扩展到 1000 字
- `path`：跳转路径，记录从主页到最终信息页面的完整路径，可选
- `publish_date`：发布日期，如能提取则记录，格式为 YYYY-MM-DD，可选
- `related_urls`：相关链接数组，如文中提到的其他相关通知，可选

#### summaries_{timestamp}.jsonl（汇总结果）

**每行格式**：
```json
{
  "dep": "学院名称",
  "url": "信息的原始链接",
  "abstract": "核心摘要",
  "diff": "不同之处",
  "special": "独特信息"
}
```

## 格式约束

### 必须遵守
✅ 输出文件命名格式：`comparison_{timestamp}.xlsx`
✅ JSON 字段名称必须与规范一致
✅ 字符串内容必须使用 UTF-8 编码
✅ 临时文件必须保存到 `.temp/` 目录

### 禁止修改
❌ 输出文件命名格式
❌ Python 脚本调用参数要求
❌ 输出内容的格式结构

## helper.py 函数说明

### append_to_jsonl 函数

**用途**：将 JSON 对象追加到 JSONL 文件

**函数签名**：
```python
append_to_jsonl(file_path, data)
```

**参数说明**：
- `file_path`：JSONL 文件路径
- `data`：要追加的 JSON 对象（字典）

**调用示例**：
```python
append_to_jsonl('.temp/fetch_20260426_163822.jsonl', {
    'url': 'https://example.com',
    'title': '示例标题',
    'snippet': '示例摘要',
    'full_text': '完整文本'
})
```
