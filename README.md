# ComiRadar

自动发现未来 90 天内全国漫展、同人展、二次元演唱会等演出信息。

**数据来源**：B站会员购、大麦、秀动、猫眼、票星球、永乐 + 微博、B站动态、小红书

## 使用

```bash
pip install -r requirements.txt
python main.py scrape   # 抓取所有平台
python main.py export   # 导出 events.json
python main.py notify   # 推送通知（需配置密钥）
python main.py run      # 一键三连
```

## 配置

编辑 `config.py` 设置推送密钥：

```python
NOTIFIERS = {
    "serverchan": {"key": "你的SendKey"},
    "bark": {"url": "https://api.day.app/你的Key"},
}
```

## 与博客集成

本仓库通过 git submodule 引入博客 [myBlog](https://github.com/sixtdreanight/myBlog)，由 GitHub Actions 定时运行，数据自动更新到 [演出页面](https://dreamnight.net.cn/anime-events)。
