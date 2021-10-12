#!/usr/bin/env python
from __future__ import print_function

import os
import logging

import sys
if sys.version_info[0] == 2:
	PYTHON_VERSION = 2 
elif sys.version_info[0] == 3:
	PYTHON_VERSION = 3
else:
	raise Exception("Unknown Python version")

__all__ = ['plog', 'pmkdir', 'which', 'parse_num_unit', 'byte2str']

class ExitOnCritical(logging.StreamHandler):
	def emit(self, record):
		if isinstance(record.msg, list):
			record.msg = ' '.join(record.msg)
		elif isinstance(record.msg, dict):
			record.msg ="\n" +  "\n".join(("%-30s%s" % (str(k).strip() + ':', str(v).strip()) for k, v in \
				sorted(record.msg.items(), key = lambda x: len(str(x[0]) + str(x[1])))))
		elif hasattr(record.msg, '__dict__'):
			record.msg ="\n" + "\n".join(("%-30s%s" % (str(k).strip() + ':', str(v).strip()) for k, v in \
				sorted(vars(record.msg).items(), key = lambda x: len(str(x[0]) + str(x[1])))))

		if record.levelno >= logging.ERROR:
			msg = record.msg
			record.msg = '\033[35m%s\033[0m' % msg
			super(ExitOnCritical, self).emit(record)
			record.msg = msg
		else:
			super(ExitOnCritical, self).emit(record)
		if record.levelno >= logging.CRITICAL:
			need_emit = False
			for handler in logging.getLogger().handlers:
				if need_emit:
					handler.emit(record)
				elif handler == self:
					need_emit = True
			raise Exception(record.msg)

def plog(path=None):
	formatter = logging.Formatter('[%(process)d %(levelname)s] %(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
	log = logging.getLogger()

	if not log.handlers:
		log.setLevel(logging.INFO)
		# console_handler = logging.StreamHandler()
		console_handler = ExitOnCritical()
		console_handler.setFormatter(formatter)
		log.addHandler(console_handler)

	if path:
		has_path_logger = False
		for logger in log.handlers:
			if isinstance(logger, logging.FileHandler) and logger.baseFilename == path:
				has_path_logger = True
				break

		if not has_path_logger:
			fileHandler = logging.FileHandler(path, mode='w')
			fileHandler.setFormatter(formatter)
			log.addHandler(fileHandler)
	return log

def which(program):
	def is_exe(fpath):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)
	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			exe_file = os.path.join(path, program)
			if is_exe(exe_file):
				return exe_file
	return None

def parse_num_unit(content, base=1000):
	'''2Gb 2kb 2.3 kb 3.5g'''
	def parse_unit(unit, base=1000):
		if unit[0] in ['k', 'K']:
			return base
		elif unit[0] in ['m', 'M']:
			return base * base
		elif unit[0] in ['g', 'G']:
			return base * base * base

	if str(content)[-1].isdigit():
		return int(content)
	value, unit = 1, 1
	contents = str(content).strip().split()
	if len(contents) != 1:
		value = float(contents[0])
		unit = parse_unit(contents[1], base)
	else:
		if contents[0][-2].isdigit():
			value = float(contents[0][:-1])
			unit = parse_unit(contents[0][-1], base)
		else:
			value = float(contents[0][:-2])
			unit = parse_unit(contents[0][-2:], base)
	return int(value * unit + .499)

def pmkdir(path):
	if not os.path.exists(path):
		os.makedirs(path)
		return True
	else:
		return False

def byte2str(byte, ignore=True):
	if ignore:
		try:
			byte = byte.decode("UTF-8")
		except Exception:
			pass
		finally:
			return byte
	else:
		return byte.decode("UTF-8")
