---
name: sysu-msg-sum
description: 批量抓取中山大学各学院网站的通知公告（支持深度探索），汇总信息并生成对比 Excel 表格。
inputs:
  - topic: 用户输入的主题（例如："奖学金评选"、"学科竞赛"、"学术讲座"）
  - urls_file: 可选，默认为当前 skill 目录下的 `assets/urls.json`，JSON 数组格式，包含各学院信息板块 URL。
outputs:
  - excel_file: 生成的 Excel 文件路径（带时间戳）
  - jsonl_file: 中间汇总文件（带时间戳），包含所有抓取到的通知信息。
---

# 中山大学通知公告批量抓取与对比技能

## 角色定义

你是一名信息收集与分析专家。用户会提供一个主题（如"奖学金评选"）。你需要：

1. 从 `assets/urls.json` 读取中山大学各学院的信息板块 URL。
2. 对每个信息板块 URL 进行网页探索，抓取与主题相关的通知内容。
3. 将每条有效通知按照固定格式写入临时 JSONL 文件。
4. 完成所有抓取后，分析各学院在主题上的差异，生成对比 Excel 表格。

## 准备工作

- 确保 `scripts/` 目录下已包含：`web-fetch.py`、`helper.py`、`generate_xlsx.py`。
- 确保已安装 Python 依赖：`beautifulsoup4`、`openpyxl`（若无则提示用户安装）。
- Skill 目录结构示例：
```
  sysu-msg-sum/
  ├── SKILL.md
  ├── assets/
  │ └── urls.json # 学院根 URL 列表
  └── scripts/
  ├── web-fetch.py
  ├── helper.py
  └── generate_xlsx.py
```

## 执行步骤

### 第一阶段：读取 URL 列表并初始化

1. 读取 `assets/urls.json`，获得信息板块 URL 数组。格式如：

```json
[
  {
    "url": "https://civil.sysu.edu.cn/graduate-education",
    "dep": "土木工程学院",
    "description": "研究生教务信息板块"
  },
  {
    "url": "https://sges.sysu.edu.cn/teach/graduate/inform",
    "dep": "遥感科学与技术学院",
    "description": "研究生教务信息板块"
  },
  {
    "url": "https://sir.sysu.edu.cn/zh-hans/edu_notice/postgraduate",
    "dep": "国际关系学院",
    "description": "研究生教务信息板块"
  },
  ...
]
```

2. 生成当前任务的时间戳 timestamp = YYYYMMDD_HHMMSS。

3. 创建临时目录 .temp（若不存在），并在其中创建两个文件：
  - `.temp/notices_{timestamp}.jsonl` 用于存储抓取到的通知。
  - 记录进度文件（可选，用于断点续传，本 Skill 暂不强制）。

### 第二阶段：批量抓取所有学院的相关通知

为提高任务执行质量和简化协调工作，创建一个专门的子代理来处理整个抓取流程。这个子代理将负责所有学院的数据抓取、筛选、提取和记录工作。

#### 创建子代理执行完整抓取任务

使用 `sessions_spawn()` 创建一个子代理，传入以下完整任务指令：

```text
你是中山大学通知信息汇总专家。你的任务是批量抓取并汇总各学院关于"{topic}"的通知信息。

工作目录：/workspace/projects/workspace/skills/sysu-msg-sum

**【最高理念】**
这项任务需要推理、理解和总结通知的能力，而不是简单的关键词匹配任务，因此：
- 这项任务花费的时间可能会超过半个小时，但是你有充足的时间完成这项任务。不要急于求成，确保每个步骤都执行到位。
- **【强制要求】**获取到相关文章的详细信息后，必须**立即**使用 shell 的 echo >> 方式写入记录。
- **【禁止】**在内存中累积大量详细记录。
- **【禁止】**为了加快处理速度而不按照要求执行任务，如通过生成脚本简化处理逻辑。

**【质量要求】**请确保每一步都仔细执行，保证任务完成的高质量：
- 准确提取学院名称、标题、发布日期
- 核心摘要要精炼（200字以内）且与主题密切相关
- JSON 格式必须正确（注意转义双引号）
- 遇到无相关文章的学院，也要明确记录

**执行步骤**：

1. 读取 assets/urls.json 获取所有学院信息板块 URL

2. 对每个学院的 URL **严格**执行以下流程：
  2.1. 使用 web-fetch.py 获取该信息板块的文章导航链接：
    ```bash
    python scripts/web-fetch.py <学院URL> --output temp_<学院代码>_nav
    ```
    读取生成的 .web-tmp/temp_<学院代码>_nav.txt 文件

  2.2. 筛选与"{topic}"相关的文章链接：
    - 搜索标题中包含主题关键词的文章
    - 记录相关文章的 URL、标题、日期

  2.3. 获取详细内容：
    ```bash
    python scripts/web-fetch.py <文章URL> --detail --output temp_<随机后缀>
    ```
    读取生成的详细内容文件，如果原始文本中存在 `"`, `\` 等特殊字符，需要进行转义
    转义后从内容中提取以下 5 个字段：
    - "学院"：从信息板块根 URL 或链接文本中推断学院名称（例如"计算机学院"）
    - "原始链接"：文章的完整 URL
    - "标题"：从文章内容或链接文本中提取的通知标题
    - "核心摘要"：与主题密切相关的关键信息，200字以内，需包含时间、地点、对象、要求等具体细节
    - "发布日期"：从文章内容中提取，格式为 YYYY-MM-DD（若无法提取则留空）

  2.4. **立即**将每条记录以 JSON 格式追加写入 .temp/notices_{timestamp}.jsonl：
    处理完每条文章后立即执行写入（用 >> 追加，**不要用变量累积**）:
    ```bash
    echo '{"学院":"...", "原始链接":"...", "标题":"...", "核心摘要":"...", "发布日期":"..."}' >> .temp/notices_{timestamp}.jsonl
    ```

3. 完成所有学院后，统计：
   - 共抓取了多少条相关通知
   - 涉及哪些学院（列出名称和通知数量）
   - 哪些学院没有相关通知

最后返回一个简洁的报告，包含上述统计信息。如果没有任何相关通知，也请明确说明。
```

**主代理行为**：
- 使用 `sessions_spawn(mode="run", runtime="subagent")` 创建子代理
- 等待子代理完成整个抓取任务
- 子代理完成后，继续执行第三阶段的汇总分析

#### 验证抓取结果

子代理完成后，检查 `.temp/notices_{timestamp}.jsonl` 文件：
- 确认文件存在且不为空
- 读取文件内容，验证 JSON 格式正确，特殊字符被正确转义
- 统计成功抓取的记录数量

如果子代理报告显示没有任何相关通知，也要继续执行后续阶段，以便给用户明确的反馈。

### 第三阶段：汇总与对比分析
所有信息板块 URL 处理完毕后，执行以下步骤：

1. 读取整个 JSONL 文件 `notices_{timestamp}.jsonl`，获得所有记录列表。

2. 分析每条记录的"核心摘要"，找出不同学院之间的 **共同点** 和 **差异点**。
  - 共同点示例：多数学院都提到"申请截止日期为 5 月 30 日"、"需要提交成绩单"。
  - 差异点示例："计算机学院要求有项目经历，管理学院要求有实习证明"。

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
脚本会将内容写入 `.web-tmp/temp_xxx.txt`，你需要读取该文件并解析。

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
| 开始批量抓取中山大学各学院关于"研究生奖学金评选"的通知，预计需要几分钟。完成后将生成对比 Excel 表格。

然后自动执行以上所有步骤，最后提供文件下载或告知保存路径。

===========

### 注意事项
- 本 Skill 依赖 `web-fetch.py` 中的 `BeautifulSoup`，请确保已安装：`pip install beautifulsoup4`。

- 由于部分学院网站可能使用动态加载（JS），`web-fetch.py` 只能获取静态 HTML，对于完全由 JS 渲染的页面可能无法抓取到内容。这种情况下，可以提示用户改用 `browser-tools`，但本 Skill 暂不涉及。

- 为了避免被反爬，建议在每个请求之间加入 0.5~1 秒的随机延迟。
