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

你（主代理）需要先使用 `web-fetch.py` 执行以下命令，获取信息板块页面的多个文章导航链接：
```bash
python scripts/web-fetch.py <info_url> --output <临时文件名>
```

#### 2.2 筛选相关文章链接

从 2.1 的输出中，根据链接文本是否包含用户主题词（如“奖学金”、“竞赛”）筛选出所有相关文章的 URL。将筛选出的 URL 存入一个列表 `article_urls`。

若没有相关文章，跳过该信息板块。

#### 2.3 为每个相关文章创建子代理抓取详情

对于 `article_urls` 中的每一个 URL，**你（主代理）必须通过 `sessions_spawn()` 创建一个子代理**，并行执行该文章的详细内容抓取、摘要提取和记录写入。具体要求如下：

**子代理的任务指令模板**（你需要填入到 `sessions_spawn` 的 `prompt` 参数中）：
```text
你是一个文章内容提取专家。你的任务是：
1. 访问指定文章链接：{article_url}
2. 使用 `web-fetch.py` 获取该文章的详细内容：
  ```bash
  python scripts/web-fetch.py {article_url} --detail --output temp_article_{随机后缀}
  ```
读取生成的 `.txt` 文件内容作为 `detail_text`。

3. 从 `detail_text` 中提取以下字段，并将它们整理成一个 JSON 对象：

- "学院"：从信息板块根 URL 或链接文本中推断学院名称（例如 “计算机学院”）
- "原始链接"：{`article_url`}
- "标题"：从文章内容或链接文本中提取
- "核心摘要"：与用户主题 `{topic}` 密切相关的关键信息，200 字以内，需包含时间、地点、对象、要求等具体细节
- "发布日期"：从文章内容中提取，格式 YYYY-MM-DD（若无法提取则留空

4. 将上述 JSON 对象追加写入到共享文件 `.temp/notices_{timestamp}.jsonl` 中。
- 使用 `echo` 命令追加，确保不覆盖已有内容：
  ```bash
  echo '{"学院":"...", ...}' >> .temp/notices_{timestamp}.jsonl
  ```

5. 写入完成后，返回一个简短的成功确认消息（例如 “OK”）。
```

**注意**：子代理不需要与用户交互，只需一次性执行上述步骤并结束。请确保 JSON 对象中的双引号正确转义（外层使用单引号包裹 JSON 字符串）。

**主代理行为**：
- 遍历 `article_urls`，对每个 URL 调用一次 `sessions_spawn(command="article_fetcher", prompt=上述模板.format(article_url=url, topic=用户主题, timestamp=当前时间戳))`。
- 尽可能同时创建所有子代理（并行执行），以提高效率。
- 子代理执行过程中，主代理可以进入等待状态，直到**所有子代理返回结果**（OpenClaw 会自动管理子代理的生命周期，主代理无需额外轮询）。

#### 2.4 确认子代理执行结果
所有子代理完成后，临时文件 `.temp/notices_{timestamp}.jsonl` 中应已包含所有成功抓取的文章记录。你可以通过读取该文件的行数来验证抓取是否全部成功。

如果某个子代理失败（例如子进程返回非零退出码或超时），主代理应记录错误但**不影响其他子代理**。最终汇总时，只需报告成功抓取的数量和失败的 URL。

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
