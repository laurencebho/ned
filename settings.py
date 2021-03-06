from datetime import date, timedelta
import logging
import colorlog
import vcr
import requests


def setup_logger():
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        '%(log_color)s%(name)s: %(message)s'))

    logger = colorlog.getLogger('NED logger')
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    return logger


class DateHandler:
    def __init__(self):
        today = date.today()
        delta = timedelta(days=365)
        prev = today - delta
        format = '%Y%m%d%H'
        self.end = today.strftime(format)
        self.start = prev.strftime(format)

    @property
    def end(self):
        return self._end

    @end.setter
    def end(self, end):
        self._end = end


    @property
    def start(self):
        return self._start

    @start.setter
    def start(self, start):
        self._start = start


def init(language='en', replaying=False, verbose=False):
    global date_handler
    global logger
    global LANG
    global VCR
    global SESSION
    global REPLAYING
    global PARALLEL
    global VERBOSE

    date_handler = DateHandler()
    logger = setup_logger()
    LANG = language
    VCR = vcr.VCR(
        cassette_library_dir='fixtures/cassettes',
        record_mode='once',
    )
    SESSION = requests.session()
    REPLAYING = replaying
    PARALLEL = False #only set true when parallelising requests
    VERBOSE = verbose