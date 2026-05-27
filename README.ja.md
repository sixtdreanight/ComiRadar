**言語 / Language:** [English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-Hant.md) | [日本語](README.ja.md)

# ComiRadar

[![Tests](https://img.shields.io/badge/tests-46%20passed-green)](https://github.com/sixtdreanight/ComiRadar/actions)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**中国全土のアニメコンベンション、同人誌即売会、ACG コンサートを今後 90 日間自動検出します。**

Bilibili、Damai、Showstart、Maoyan、Piaoxingqiu、Yongle など 9 つのチケットプラットフォームに加え、Weibo、Bilibili フィード、Xiaohongshu をスクレイピングし、正規化されたイベントスキーマに統合します。

---

> 日本語翻訳は準備中です。完全な内容は [English](README.md) または [简体中文](README.zh-CN.md) をご参照ください。
>
> Japanese translation in progress. Please refer to [English](README.md) or [简体中文](README.zh-CN.md) for complete content.

---

## 使用方法

```bash
pip install -r requirements.txt
python main.py scrape   # 全プラットフォームをスクレイピング
python main.py export   # events.json をエクスポート
python main.py notify   # 通知をプッシュ
python main.py run      # 3 ステップ一括実行
```

## ライセンス

MIT

---

<div align="center">

**Language / 语言 / 言語**

[**English**](README.md) | [**简体中文**](README.zh-CN.md) | [**繁體中文**](README.zh-Hant.md) | [**日本語**](README.ja.md)

</div>
