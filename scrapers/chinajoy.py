from scrapers.base import SubprocessScraper


class ChinajoyScraper(SubprocessScraper):
    platform = "chinajoy"
    worker_script = "_playwright_worker.py"
    worker_args = ["chinajoy"]
    worker_timeout = 120
