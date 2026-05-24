from scrapers.base import SubprocessScraper


class NyatoScraper(SubprocessScraper):
    platform = "nyato"
    worker_script = "_playwright_worker.py"
    worker_args = ["nyato"]
    worker_timeout = 180
