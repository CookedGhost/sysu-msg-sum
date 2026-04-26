---
name: sysu-msg-sum
description: 批量抓取中山大学各学院网站的通知公告（支持深度探索），汇总信息并生成对比 Excel 表格。
inputs:
  - topic: 用户输入的主题（例如：“奖学金评选”、“学科竞赛”、“学术讲座”）
  - urls_file: 可选，默认为当前 skill 目录下的 `assets/urls.json`，JSON 数组格式，包含各学院根 URL。
outputs:
  - excel_file: 生成的 Excel 文件路径（带时间戳）
  - jsonl_file: 中间汇总文件（带时间戳），包含所有抓取到的通知信息。
---

# 中山大学通知公告批量抓取与对比技能

## 角色定义

你是一名信息收集与分析专家。用户会提供一个主题（如“奖学金评选”）。你需要：

1. 从 `assets/urls.json` 读取中山大学各学院的根 URL（约 70 个）。
2. 对每个根 URL，进行深度最多 3 层的网页探索，抓取与主题相关的通知内容。
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

1. 读取 `assets/urls.json`，获得根 URL 数组。格式如：

```json
[
  "https://cse.sysu.edu.cn/",
  "https://sog.sysu.edu.cn/",
  ...
]
```

2. 生成当前任务的时间戳 timestamp = YYYYMMDD_HHMMSS。

3. 创建临时目录 .temp（若不存在），并在其中创建两个文件：
  - `.temp/notices_{timestamp}.jsonl` 用于存储抓取到的通知。
  - 记录进度文件（可选，用于断点续传，本 Skill 暂不强制）。

### 第二阶段：对每个根 URL 执行深度抓取

对每个 `root_url` 执行以下子流程（注意：每个根 URL 独立处理，抓取完成后可从上下文中清除该站点的详细信息以节省 token）：

#### 2.1 定义抓取函数（逻辑描述）

为完成深度最多 3 层的探索，你需要编写一个内部递归逻辑（可以由 AI 自己控制循环），但更简单的方式是：对于每个页面，先调用 `web-fetch.py --detail` 获得详细文本，判断是否与 `topic` 相关；如果相关性不足，则调用 `web-fetch.py`（不带 --detail）获得导航链接列表，从中选取最相关的子链接继续抓取。

#### 2.2 判断相关性标准

满足下面任意一条即认为 相关：
  - 页面标题或正文中包含主题词（例如“奖学金”、“竞赛”等）且至少包含一段具体描述（超过 100 字）。
  - 页面明显是通知公告详情页（有标题、发布日期、正文内容）。

若不相关，则进入下一层探索。

#### 2.3 使用 `web-fetch.py` 的具体命令

- **获取详细内容**（适合详情页）：
  
  ```bash
  python scripts/web-fetch.py <URL> --detail --output <临时文件名>
  ```
  
  该命令会生成一个 `.txt` 文件到 `WEB_TMP_DIR`（默认为 `~/.web-tmp/`），并打印文件路径。你需要读取该文本文件的内容。
- **获取导航链接**（适合列表页/首页）：
  
  ```bash
  python scripts/web-fetch.py <URL> --output <临时文件名>
  ```
  
  输出内容为各链接的“链接文本 (URL)”格式，每行一个。你可以解析这个输出获得候选子链接。

**注意**：为避免磁盘文件过多，你可以只读取最近生成的文件内容，然后立即删除（可选）。但保留也可。

#### 2.4 深度探索流程（伪代码）
```text
def explore_page(url, depth=0, max_depth=3, root_url=None):
    # 1. 获取详细内容
    detail_txt = run_web_fetch(url, detail=True)
    if is_relevant(detail_txt, topic):
        # 构造 JSON 记录
        record = {
            "学院": extract_college_name_from_url(root_url or url),
            "原始链接": url,
            "标题": extract_title(detail_txt),
            "核心摘要": summarize(detail_txt, max_len=200),
            "详细内容": detail_txt[:1000],   # 可选
            "发布日期": extract_date(detail_txt),
            "抓取深度": depth
        }
        # 使用 helper.py 追加到 JSONL
        run_helper_append(record, jsonl_path)
        return  # 该分支已收获信息，不再向下（可根据需要继续探索其他链接，但通常详情页已够）

    # 2. 若深度已到最大，不再探索
    if depth >= max_depth:
        return

    # 3. 获取导航链接
    nav_output = run_web_fetch(url, detail=False)
    links = parse_nav_links(nav_output)   # 解析出 (text, url) 列表
    # 4. 筛选最相关的 2 个子链接（根据链接文本中是否包含主题词、或常见栏目名如“通知公告”）
    candidates = rank_links(links, topic)[:2]
    for link_url in candidates:
        explore_page(link_url, depth+1, max_depth, root_url=root_url or url)
```
**关键点**：
- 使用 `run_web_fetch` 和 `run_helper_append` 是指导 AI 通过 subprocess 执行命令行。
- 每个根 URL 的探索结果都追加到 同一个 JSONL 文件（`.temp/notices_{timestamp}.jsonl`）。
- 为了避免一次性加载 70 个站点的全部细节，每处理完一个根 URL 后，可以主动清除该站点相关的中间变量（AI 上下文管理自然支持）。

### 第三阶段：汇总与对比分析
所有根 URL 处理完毕后，执行以下步骤：

1. 读取整个 JSONL 文件 `notices_{timestamp}.jsonl`，获得所有记录列表。

2. 分析每条记录的“核心摘要”和“详细内容”，找出不同学院之间的 **共同点** 和 **差异点**。
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
- Excel 表头为：["学院", "原始链接", "标题", "核心摘要", "详细内容", "发布日期", "抓取深度"]（实际字段以 JSONL 中为准）。
- 表头自动加粗居中，长文本自动换行，列宽自适应。
- 额外的对比消息会以合并单元格的形式追加在数据下方。

### 脚本调用规范
#### `web-fetch.py` 使用示例
```bash
# 获取详细内容
python scripts/web-fetch.py https://cse.sysu.edu.cn/notice/123 --detail --output temp_cse

# 获取导航链接
python scripts/web-fetch.py https://cse.sysu.edu.cn/ --output temp_nav
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
- 对于某个根 URL 的首次请求（`web-fetch`）失败（超时、403、404），记录错误并跳过该站点，继续下一个。
- 若子链接抓取失败，记录该链接 URL 并跳过，不影响同一站点的其他链接。
- 所有失败信息可记录到一个单独的 `error_{timestamp}.log` 文件中。

### 性能与深度控制
- 每个根 URL 最多访问 10 个页面（包括首页和子链接），防止无限循环。
- 每一层选择最多 2 个子链接（因为首页通常栏目较多，但 2 个足够覆盖主要通知板块）。
- 70 个学院 × 平均 5 个页面 ≈ 350 次请求，预计可在合理时间内完成。如果部分站点响应慢，适当增加延迟（time.sleep(1)）。

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

### 自定义修改
如果需要更改最大深度、每层子链接数量等参数，可以在 Skill 开头定义可配置变量：

- MAX_DEPTH = 3
- SUBLINKS_PER_LEVEL = 2
- REQUEST_DELAY = 0.5

AI 在执行时应遵循这些变量。
