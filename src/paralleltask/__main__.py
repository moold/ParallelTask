#!/usr/bin/env python

import sys
import os
import re
import shutil
import argparse

try:
	from task_control import Task
	from kit import plog, pmkdir
except ImportError:
	from paralleltask import Task, plog
	from paralleltask.kit import pmkdir

log = ''

class HelpFormatter(argparse.RawDescriptionHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
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

def run(args):
	global log
	log_file = args[0].log if '/' in args[0].log else 'pid' + str(os.getpid()) + '.' + args[0].log
	log = plog(log_file)
	
	log.info('start...')
	log.info('logfile: ' + log_file)
	log.info('options: ')

	task = args[1][0]
	tasktag = set_tasktag(task)
	workdir = set_workdir(args)

	task = Task(task, job_prefix=args[0].job_prefix, convert_path=False if args[0].disable_convert_path else True, \
		shell=args[0].shell, group=args[0].lines)
	if not task.is_finished():
		task.set_run(max_parallel_job=args[0].maxjob, job_type=args[0].job_type, \
			interval_time=args[0].interval, cpu=args[0].cpu, mem=args[0].memory, \
			use_drmaa=args[0].use_drmaa, cfg_file=args[0].config, submit=args[0].submit,\
			kill=args[0].kill, check_alive=args[0].check_alive, job_id_regex=args[0].job_id_regex )
		total_jobs = len(task.run.unfinished_jobs)
		task.run.start()
		while (not task.run.is_finished()):
			if len(task.run.unfinished_jobs) == total_jobs or not args[0].rerun:
				log.error('%s failed: please check the following logs:' % (tasktag))
				for job in task.run.unfinished_jobs:
					log.error(job.err)
				sys.exit(1)
			else:
				log.info(str(len(task.run.unfinished_jobs)) + ' subtask(s) failed,' 
				' and rerun for the '+ str(args[0].rerun) + ' time')
				task.run.rerun()
				args[0].rerun -= 1
		else:
			task.set_task_finished()
			log.info('%s done' % (tasktag))
	else:
		log.info('skip step: %s' % (tasktag))
	log.info('%s finished' % (tasktag))

def main():
	parser = argparse.ArgumentParser(
		formatter_class = HelpFormatter,
		description = '''
parallelTask:
	A simple and lightweight parallel task engine

exmples: 
	%(prog)s [options] test.sh
'''
	)
	parser.add_argument('-t','--job_type',metavar = 'STR',default = 'local',
			choices = ['local', 'sge', 'pbs', 'slurm', 'lsf'],
			help = 'the type (%(choices)s) for the submission and control of jobs.')
	parser.add_argument('-d', '--use_drmaa', action = 'store_true',
			help = 'use drmaa to submit and control jobs.')
	parser.add_argument('-i','--interval',metavar = 'INT',type = int,default = 5,
			help = 'the interval time (second) of checking status or submiting.')
	parser.add_argument ('-l','--lines',metavar = 'INT',type = int,default = 1,
			help = 'the number of lines to form a subtask.')
	parser.add_argument('-p','--cpu', metavar = 'INT', type = int, default = 1, 
			help = 'the required CPU for each subtask.')
	parser.add_argument('-M','--memory', metavar = 'STR', type = str, default = '3G', 
			help = 'the required memory for each subtask.')
	parser.add_argument('-m','--maxjob',metavar = 'INT',type = int,default = 10, 
			help = 'the maximum number of jobs to run in parallel.' )
	parser.add_argument('-r','--rerun', metavar = 'INT', type = int, default = 3, 
			help = 'rerun unfinished subtasks with the maximum INT of cycles.')
	parser.add_argument('--disable_convert_path', action = 'store_true',
			help = 'don\'t convert local path to absolute path for subtasks.')
	parser.add_argument('--rewrite',action = 'store_false',
			help = 'overwrite existed work directory.')
	parser.add_argument('--job_prefix',metavar = 'STR',default = 'subtask',
			help = 'the prefix tag for subtasks.')
	parser.add_argument ('--log',metavar = 'FILE',type = str, default = 'log.info',
		help = 'log file, set `/dev/null` to disable output to a file.')

	parser.add_argument('--shell', metavar = 'STR', type = str, default = '/bin/bash', 
			help = 'the shell command language.')
	parser.add_argument('--submit', metavar = '"STR"', type = str, default=argparse.SUPPRESS,
			help = 'command to submit a job, overwrite --config, read from --config by default.')
	parser.add_argument('--kill', metavar = '"STR"', type = str, default=argparse.SUPPRESS,
			help = 'command to kill a job, overwrite --config, read from --config by default.')
	parser.add_argument('--check_alive', metavar = '"STR"', type = str, default=argparse.SUPPRESS,
			help = 'command to check a job status, overwrite --config, read from --config by default.')
	parser.add_argument('--job_id_regex', metavar = '"STR"', type = str, default=argparse.SUPPRESS,
			help = 'the job-id-regex to parse the job id from the out of --submit, overwrite --config' \
			', read from --config by default.')
	parser.add_argument('--config', metavar = 'FILE', type = str, default = os.path.dirname(os.path.realpath(__file__)) + \
			'/cluster.cfg', help = 'the config file to load --submit,--kill,--check_alive,--job_id_regex value.')	
	args = parser.parse_known_args()
	if 'submit' not in args[0]:
		args[0].submit = None
	if 'kill' not in args[0]:
		args[0].kill = None
	if 'check_alive' not in args[0]:
		args[0].check_alive = None
	if 'job_id_regex' not in args[0]:
		args[0].job_id_regex = None

	if not args[1]:
		parser.print_help()
		sys.exit(1)
	run(args)

if __name__ == '__main__':
	main()
