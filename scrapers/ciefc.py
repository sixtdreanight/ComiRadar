from scrapers.base import SubprocessScraper


class CiefcScraper(SubprocessScraper):
    platform = "ciefc"
    worker_script = "_ciefc_worker.py"
    worker_timeout = 120
