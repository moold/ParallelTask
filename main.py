#!/usr/bin/env python

import sys
import os
import re
import signal
import shutil
import argparse

SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(SCRIPT_PATH)
from kit import *

log = ''

class HelpFormatter(argparse.RawDescriptionHelpFormatter,argparse.ArgumentDefaultsHelpFormatter):
	pass

def set_tasktag(task):
	if not os.path.exists(task):
		log.error('Error, can not find %s' % (task))
		sys.exit(1)
	else:
		tasktag = os.path.basename(task)
		return tasktag[:-3] if tasktag.endswith('.sh') else tasktag

def set_workdir(args):
	workdir = args[1][0] + '.work'
	log.info('work directory: %s' % (workdir))
	if os.path.exists(workdir):
		if not args[0].rewrite:
			for i in range(100):
				e = workdir + '.backup' + str(i)
				if not os.path.exists(e):
					shutil.move(workdir, e)
					log.warning('mv ' + workdir + ' to ' + e)
	if not pmkdir(workdir):
		log.info('skip mkdir: ' + workdir)
	else:
		log.info('mkdir: ' + workdir)
	return workdir

def main(args):
	if not args[1]:
		parser.print_help()
		sys.exit(1)

	global log
	log_file = 'pid' + str(os.getpid()) + '.' + args[0].log
	log = plog(log_file)
	from task_control import Task, Run

	signal.signal(signal.SIGINT, Run.kill)
	signal.signal(signal.SIGTERM, Run.kill)

	log.info('start...')
	log.info('logfile: ' + log_file)
	log.info('options: ')

	task = args[1][0]
	tasktag = set_tasktag(task)
	workdir = set_workdir(args)

	task = Task(task, prefix = args[0].jobprefix, convertpath = args[0].convertpath, group = args[0].lines)
	if not task.check():
		task.set_subtasks()
		task.set_run(max_pa_jobs = args[0].maxjob , bash = '/bin/bash', job_type = args[0].jobtype, \
			sge_options = args[0].clusteroption, vf = '3G', cpu = 1)
		task.run.start()
		if task.run.check():
			task.set_task_done()
			log.info('%s done' % (tasktag))
		else:
			log.error('%s failed: please check the following logs:' % (tasktag))
			for subtask in task.run.unfinished_tasks:
				log.error(subtask + '.e')
			sys.exit(1)
	else:
		log.info('skip step: %s' % (tasktag))
	log.info('%s finished' % (tasktag))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(
		formatter_class = HelpFormatter,
		description = '''
parallelTask:
	A simple and lightweight parallel task engine

exmples: 
	%(prog)s test.sh
'''
	)
	parser.add_argument('-t','--jobtype',metavar = 'STR',default = 'local',
			choices = ['local', 'sge', 'pbs', 'slurm', 'lsf'],
			help = 'set the type (%(choices)s) for the submission and control of subtasks.')
	parser.add_argument('-c','--clusteroption', metavar = 'STR', nargs='*',
			help = 'a template to define the resource requirements for each subtask,' 
			' which will pass to DRMAA as the nativeSpecification field.')
	parser.add_argument('-i','--interval',metavar = 'INT',type = int,default = 30,
			help = 'set the interval time of checking status or submiting.')
	parser.add_argument ('-l','--lines',metavar = 'INT',type = int,default = 1,
			help = 'set the number of lines to form a subtask.')
	parser.add_argument('-m','--maxjob',metavar = 'INT',type = int,default = 30, 
			help = 'set the maximum number of subtasks to run in parallel.' )
	parser.add_argument('-r','--rerun', metavar = 'INT', type = int, default = 3, 
			help = 'rerun unfinished subtasks with the maximum RERUN of cycles.')
	parser.add_argument('--convertpath',action = 'store_false',
			help = 'convert local path to absolute path for subtasks.')
	parser.add_argument('--rewrite',action = 'store_false',
			help = 'overwrite existed work directory.')
	parser.add_argument('--jobprefix',metavar = 'STR',default = 'subtask',
			help = 'set the prefix tag for subtasks.')
	parser.add_argument ('--log',metavar = 'FILE',type = str, default = 'log.info',
		help = 'log file')
	args = parser.parse_known_args()
	main(args)
