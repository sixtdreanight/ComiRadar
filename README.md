# ComiRadar

[![Tests](https://img.shields.io/badge/tests-46%20passed-green)](https://github.com/sixtdreanight/ComiRadar/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**Automatically discovers anime cons, doujin fairs, and ACG concerts across China for the next 90 days.**

**自动发现未来 90 天内全国漫展、同人展、二次元演唱会等演出信息。**

Scrapes 9 ticketing platforms (Bilibili, Damai, Showstart, Maoyan, Piaoxingqiu, Yongle, etc.) plus Weibo, Bilibili feeds, and Xiaohongshu. Each platform has its own parser, unified into a normalized event schema.

抓取 B站会员购、大麦、秀动、猫眼、票星球、永乐等九大票务平台及微博、B站动态、小红书，统一规范化输出。

### Data Sources / 数据来源

Bilibili (会员购) · Damai (大麦) · Showstart (秀动) · Maoyan (猫眼) · Piaoxingqiu (票星球) · Yongle (永乐) · Weibo (微博) · Bilibili Dynamics · Xiaohongshu (小红书)

### Deduplication Strategy / 去重策略

Two-layer dedup: SHA256 fingerprint for exact matches + fuzzy merge on city/date/title for near-duplicates. Merged events combine fields from multiple sources.

两层去重：SHA256 指纹精确匹配 + 城市/日期/标题模糊合并，合并缺失字段。

## Usage / 使用

```bash
pip install -r requirements.txt
python main.py scrape   # Scrape all platforms / 抓取所有平台
python main.py export   # Export events.json / 导出 events.json
python main.py notify   # Push notifications / 推送通知（需配置密钥）
python main.py run      # All three steps / 一键三连
```

## Configuration / 配置

Edit `config.py` to set notification keys:

```python
NOTIFIERS = {
    "serverchan": {"key": "your-SendKey"},
    "bark": {"url": "https://api.day.app/your-key"},
}
```

## 环境变量

以下环境变量用于各数据源的身份验证和系统配置：

| 变量名 | 说明 |
|--------|------|
| `BILI_BUVID3` | B站 cookies 中的 `buvid3` |
| `BILI_SESSDATA` | B站 cookies 中的 `SESSDATA` |
| `BILI_BILI_JCT` | B站 cookies 中的 `bili_jct` |
| `DAMAI_M_H5_TK` | 大麦 cookies 中的 `m_h5_tk` |
| `DAMAI_COOKIE2` | 大麦 cookies 中的 `cookie2` |
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥（用于 AI 信息提取） |
| `COMI_EXPORT_PATH` | 导出路径（可选，默认输出到项目目录） |

## Blog Integration / 与博客集成

This repo is included as a git submodule in [myBlog](https://github.com/sixtdreanight/myBlog). GitHub Actions runs the scraper on schedule, and results auto-sync to the [events page](https://dreamnight.net.cn/anime-events).

本仓库通过 git submodule 引入博客，由 GitHub Actions 定时运行，数据自动更新到演出页面。

## Tech Stack / 技术栈

- **Scraping**: Python 3.11+ · Playwright · HTTPX
- **Storage**: SQLite
- **Scheduling**: GitHub Actions (cron)
- **Integration**: Git submodule → Astro blog

## Related / 相关项目

- [chinese-scraper-utils](https://github.com/sixtdreanight/chinese-scraper-utils) — Shared utilities extracted from this project
- [myBlog](https://github.com/sixtdreanight/myBlog) — Events data displayed at dreamnight.net.cn/anime-events

## License

MIT
