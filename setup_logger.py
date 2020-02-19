import colorlog
import logging

handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
	'%(log_color)s%(name)s: %(message)s'))

logger = colorlog.getLogger('NED logger')
logger.addHandler(handler)
logger.setLevel(logging.INFO)