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

__all__ = ['plog', 'pmkdir', 'which', 'parse_num_unit']

def pmkdir(path):
	if not os.path.exists(path):
		os.makedirs(path)
		return True
	else:
		return False

def plog(path = False):

	formatter = logging.Formatter('[%(levelname)s] %(asctime)s %(message)s')
	log = logging.getLogger()
	if log.handlers:
		return log

	log.setLevel(logging.DEBUG)
	console_handler = logging.StreamHandler()
	console_handler.setFormatter(formatter)
	log.addHandler(console_handler)

	if path:
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
