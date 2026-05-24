from scrapers.base import SubprocessScraper


class BilibiliScraper(SubprocessScraper):
    platform = "bilibili"
    worker_script = "_bilibili_worker.py"
    worker_timeout = 300
