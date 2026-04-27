---
name: sysu-msg-sum
description: 批量抓取中山大学各学院网站的通知公告（支持深度探索），汇总信息并生成对比 Excel 表格。
inputs:
  - topic: 用户输入的主题（例如：“奖学金评选”、“学科竞赛”、“学术讲座”）
  - urls_file: 可选，默认为当前 skill 目录下的 `assets/urls.json`，JSON 数组格式，包含各学院信息板块 URL。
outputs:
  - excel_file: 生成的 Excel 文件路径（带时间戳）
  - jsonl_file: 中间汇总文件（带时间戳），包含所有抓取到的通知信息。
---

# 中山大学通知公告批量抓取与对比技能

## 角色定义

你是一名信息收集与分析专家。用户会提供一个主题（如“奖学金评选”）。你需要：

1. 从 `assets/urls.json` 读取中山大学各学院的信息板块 URL。
2. 对每个信息板块 URL 进行网页探索，抓取与主题相关的通知内容。
3. 将每条有效通知按照固定格式写入临时 JSONL 文件。
4. 完成所有抓取后，分析各学院在主题上的差异，生成对比 Excel 表格。

## 准备工作

- 确保 `scripts/` 目录下已包含：`web-fetch.py`、`helper.py`、`generate_xlsx.py`。
- 确保已安装 Python 依赖：`beautifulsoup4`、`openpyxl`（若无则提示用户安装）。
- Skill 目录结构示例：
  sysu-msg-sum/
  ├── SKILL.md
  ├── assets/
  │ └── urls.json # 学院根 URL 列表
  └── scripts/
  ├── web-fetch.py
  ├── helper.py
  └── generate_xlsx.py

## 执行步骤

### 第一阶段：读取 URL 列表并初始化

1. 读取 `assets/urls.json`，获得信息板块 URL 数组。格式如：

```json
[
  "https://cse.sysu.edu.cn/graduate/inform",
  "https://sese.sysu.edu.cn/taxonomy/term/154",
  ...
]
```

2. 生成当前任务的时间戳 timestamp = YYYYMMDD_HHMMSS。

3. 创建临时目录 .temp（若不存在），并在其中创建两个文件：
  - `.temp/notices_{timestamp}.jsonl` 用于存储抓取到的通知。
  - 记录进度文件（可选，用于断点续传，本 Skill 暂不强制）。

### 第二阶段：对每个信息板块 URL 执行文章抓取

对每个 `info_url` 执行以下子流程（注意：每个信息板块 URL 独立处理，抓取完成后可从上下文中清除该站点的详细信息以节省 token）：

#### 2.1 获取信息板块页面内容

你需要先使用 `web-fetch.py` 执行以下命令，获取信息板块页面的多个文章导航链接：
```bash
python scripts/web-fetch.py <info_url> --output <临时文件名>
```

#### 2.2 查找所有相关文章链接

你需要从 2.1 的输出中解析出所有链接文本和 URL，判断哪些链接可能与用户输入的主题相关。相关性判断标准如下：
- 链接文本包含主题词（例如“奖学金”、“竞赛”等）。

将相关链接的 URL 记录下来，并对记录下来的每个 URL 进行下一步抓取；若没有相关文章，则跳过。

#### 2.3 获取相关文章的详细内容

对于每个相关链接，你需要再次使用 `web-fetch.py` 获取该链接的详细内容：
```bash
python scripts/web-fetch.py <article_url> --detail --output <临时文件名>
```

#### 2.4 提取核心摘要并写入 JSONL
将 2.3 获取的详细内容总结为一个核心摘要（200字左右），要求包含关键信息（如时间、地点、人物等），并将这些信息整理成 JSON 格式记录，写入 `.temp/notices_{timestamp}.jsonl` 文件中。每条记录需要包含以下字段：
- 学院名称（可从 URL 或链接文本中提取）
- 原始文章链接 URL
- 标题（如果能从链接文本或页面内容提取）
- 核心摘要（从详细内容中提取的关键信息）
- 发布日期（如果能提取）

例如：
```json
{
  "学院": "计算机学院",
  "原始链接": "https://cse.sysu.edu.cn/notice/123",
  "标题": "2025年研究生奖学金评选通知",
  "核心摘要": "申请截止日期为2025年5月30日，需提交成绩单和项目经历。",
  "发布日期": "2025-04-20"
}
```

将每条记录整理成 JSON 格式，**立即追加写入** JSONL 文件。

**首选方式（使用 echo 进行追加写入）：**

每处理完一条记录后，立即使用 echo 将该 JSON 对象追加到文件末尾。例如，在提取完一条记录后：

```
{"学院":"计算机学院","原始链接":"https://...","标题":"...","核心摘要":"...","发布日期":"2025-11-17"}
```

立即执行**追加模式**的写入操作，将此 JSON 对象追加到 `.temp/notices_{timestamp}.jsonl` 文件：
```bash
echo '{"学院":"计算机学院","原始链接":"https://...","标题":"...","核心摘要":"...","发布日期":"2025-11-17"}' >> .temp/notices_{timestamp}.jsonl
```

**注意**：
- 使用 echo 进行追加写入，不要覆盖已有内容
- 处理完一条记录后立即写入，不要等到最后批量写入

**备用方式（使用 helper.py 脚本）：**

你也可以修改 `scripts/helper.py` 中的 `input_json_data` 变量，然后运行：
```bash
python scripts/helper.py .temp/notices_{timestamp}.jsonl --append
```

#### 2.5 使用 `web-fetch.py` 的具体命令

- **获取详细内容**（适合文章页）：
  
  ```bash
  python scripts/web-fetch.py <URL> --detail --output <临时文件名>
  ```
  
  该命令会生成一个 `.txt` 文件到 `WEB_TMP_DIR`（默认为 `~/.web-tmp/`），并打印文件路径。你需要读取该文本文件的内容。
- **获取导航链接**（适合信息板块页面）：
  
  ```bash
  python scripts/web-fetch.py <URL> --output <临时文件名>
  ```
  
  输出内容为各链接的“链接文本 (URL)”格式，每行一个。你可以解析这个输出获得候选子链接。

**注意**：为避免磁盘文件过多，你可以只读取最近生成的文件内容，然后立即删除（可选）。但保留也可。

### 第三阶段：汇总与对比分析
所有根 URL 处理完毕后，执行以下步骤：

1. 读取整个 JSONL 文件 `notices_{timestamp}.jsonl`，获得所有记录列表。

2. 分析每条记录的“核心摘要”，找出不同学院之间的 **共同点** 和 **差异点**。
  - 共同点示例：多数学院都提到“申请截止日期为 5 月 30 日”、“需要提交成绩单”。
  - 差异点示例：“计算机学院要求有项目经历，管理学院要求有实习证明”。

3. 将对比分析结果整理为一个字符串列表 `other_msgs`，每一条是一个独立的对比发现。例如：
```python
other_msgs = [
    "共同点：所有学院都要求 GPA 不低于 3.0。",
    "差异点：计算机学院额外要求提交代码仓库链接，管理学院要求提交推荐信。"
]
```

### 第四阶段：生成 Excel 表格
调用 `generate_xlsx.py` 脚本，将 JSONL 文件转换为 Excel，并附加对比信息作为额外行。
```bash
python scripts/generate_xlsx.py .temp/notices_{timestamp}.jsonl output/comparison_{timestamp}.xlsx --other_msgs "共同点：所有学院都要求 GPA 不低于 3.0" "差异点：计算机学院额外要求提交代码仓库链接"
```

- 输出文件将保存在 output/ 目录下（若不存在则创建）。
- Excel 表头为：["学院", "原始链接", "标题", "核心摘要", "发布日期", "抓取深度"]（实际字段以 JSONL 中为准）。
- 表头自动加粗居中，长文本自动换行，列宽自适应。
- 额外的对比消息会以合并单元格的形式追加在数据下方。

### 脚本调用规范
#### `web-fetch.py` 使用示例
```bash
# 获取详细内容
python scripts/web-fetch.py "https://cse.sysu.edu.cn/notice/123" --detail --output temp_cse

# 获取导航链接
python scripts/web-fetch.py "https://cse.sysu.edu.cn/" --output temp_nav
```
脚本会将内容写入 `~/.web-tmp/temp_xxx.txt`，你需要读取该文件并解析。

#### `generate_xlsx.py` 使用示例
```bash
python scripts/generate_xlsx.py .temp/notices_20250427_143022.jsonl output/comparison_20250427_143022.xlsx --other_msgs "共同点：..." "差异点：..."
```

### 输出结果
- 中间文件：`.temp/notices_{timestamp}.jsonl`（保留以便审查）
- 最终报告：`output/comparison_{timestamp}.xlsx`
- 同时在对话中输出一条摘要信息，说明总共抓取到多少条通知、涉及多少学院，并附上 Excel 文件路径。

### 错误处理与重试
- 对于某个信息板块 URL 的首次请求（`web-fetch`）失败（超时、403、404），记录错误并跳过该站点，继续下一个。
- 若子链接抓取失败，记录该链接 URL 并跳过，不影响同一站点的其他链接。
- 所有失败信息可记录到一个单独的 `error_{timestamp}.log` 文件中。

### 示例执行指令
用户输入：
| 主题：研究生奖学金评选

Agent 应回应：
| 开始批量抓取中山大学各学院关于“研究生奖学金评选”的通知，预计需要几分钟。完成后将生成对比 Excel 表格。

然后自动执行以上所有步骤，最后提供文件下载或告知保存路径。

===========

### 注意事项
- 本 Skill 依赖 `web-fetch.py` 中的 `BeautifulSoup`，请确保已安装：`pip install beautifulsoup4`。

- 由于部分学院网站可能使用动态加载（JS），`web-fetch.py` 只能获取静态 HTML，对于完全由 JS 渲染的页面可能无法抓取到内容。这种情况下，可以提示用户改用 `browser-tools`，但本 Skill 暂不涉及。

- 为了避免被反爬，建议在每个请求之间加入 0.5~1 秒的随机延迟。
