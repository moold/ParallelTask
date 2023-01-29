#!/usr/bin/env python
from __future__ import print_function

import sys
import os
import re
import time
import psutil
import signal
import subprocess

try:
	from kit import *
except ImportError:
	from paralleltask.kit import *

__all__ = ['Task']

log = plog()

class Job(object):

	def __init__(self, path):
		self.path = os.path.abspath(path)
		self.id = None
		self.cmd = None
		self.out = self.path + '.o'
		self.err = self.path + '.e'

	def is_finished(self):
		return True if os.path.exists(self.path + '.done') else False

	def set_task_finished(self):
		cmd = 'touch ' + self.path + '.done'
		ret = os.system(cmd)
		if ret != 0:
			log.critical("Command '%s' returned non-zero exit status %d." % (cmd, ret))

class Task(object):

	def __init__(self, path, group=1, max_subtask=300, job_prefix='subjob', dir_prefix='work', \
			shell='/bin/bash', convert_path=True):
		self.job = Job(path)
		self.group = group
		self.max_subtask = max_subtask
		self.job_prefix = job_prefix
		self.dir_prefix = dir_prefix
		self.shell = shell
		self.convert_path = convert_path
		self.run = None
		self._jobs = [] if self.is_finished() else self._write_subtasks(self._init_subtasks(self._read_task()))

	def _read_task(self):
		tasks = []
		with open(self.job.path) as IN:
			for line in IN:
				line = line.strip()
				if not line or line[0].startswith('#'):
					continue
				lines = line.split()
				if self.convert_path:
					for i in range(len(lines)):
						if '/' not in lines[i]:
							if os.path.exists(lines[i]) or (i > 1 and (lines[i - 1] == '>' or lines[i - 1] == '1>' \
									or lines[i - 1] == '2>')):
								lines[i] = os.path.abspath(lines[i])
							elif lines[i].startswith('>') and len(lines[i]) > 1 :
								lines[i] = lines[i][0] + ' ' + os.path.abspath(lines[i][1:])
							elif lines[i].startswith(('1>','2>')) and len(lines[i]) > 2:
								lines[i] = lines[i][:2] + ' ' + os.path.abspath(lines[i][2:])
							elif re.search(r'=',lines[i]):
								paramters = lines[i].split("=")
								lines[i] = paramters[0] + '=' + os.path.abspath(paramters[1]) if \
								paramters[1] and len(paramters) == 2 and os.path.exists(paramters[1]) else lines[i]
						elif '=' in lines[i]:
							paramters = lines[i].split("=")
							lines[i] = paramters[0] + '=' + os.path.abspath(paramters[1]) if \
								paramters[1] and len(paramters) == 2 else lines[i]
						elif '>' in lines[i]:
							paramters = lines[i].split(">")
							lines[i] = paramters[0] + '>' + os.path.abspath(paramters[1]) if \
								paramters[1] and len(paramters) == 2 else lines[i]
						else:
							lines[i] = os.path.abspath(os.path.expanduser(lines[i]))
				tasks.append(" ".join(lines))
		return tasks

	def _init_subtasks(self, tasks):
		group_tasks = []
		if isinstance(self.group, int):
			task = []
			for i in range(len(tasks)):
				if task and i % self.group == 0:
					group_tasks.append(task)
					task = []
				task.append(tasks[i])
			group_tasks.append(task)
		elif isinstance(self.group, list):
			j = 0
			last_i = 0
			task = []
			for i in range(len(tasks)):
				if i - last_i == self.group[j]:
					group_tasks.append(task)
					task = []
					last_i = i
					j += 1
				task.append(tasks[i])
			group_tasks.append(task)
		else:
			log.error('Incorrect allocated task group:%s' % str(self.group))
		return group_tasks

	def _write_subtasks(self, tasks):

		def get_time_exe():
			if which('time'):
				return'time '
			elif which('/usr/bin/time'):
				return "/usr/bin/time -p "
			return ''

		jobs = []
		time = get_time_exe()
		task_count = len(tasks)
		split = 1 if task_count > self.max_subtask else 0
		subtask_file = self.job_prefix + '.sh'
		work_parent_dir = os.path.abspath(self.job.path) + '.work'
		for i in range(task_count):
			if split:
				subtask_dir = '{}/{}{:0>{}}/{}{:0>{}}'.format(work_parent_dir, self.dir_prefix, int(split/self.max_subtask), \
					len(str(int(task_count/self.max_subtask))), self.dir_prefix, i + 1, len(str(task_count)))
				split += 1
			else:
				subtask_dir = '{}/{}{:0>{}}'.format(work_parent_dir, self.dir_prefix, i + 1, len(str(task_count)))

			subtask_finish_lable = subtask_dir + '/' + subtask_file + '.done'
			if not os.path.exists(subtask_finish_lable):
				pmkdir(subtask_dir)
				subtask = "#!%s\nset -xveo pipefail\nhostname\ncd %s\n" % (self.shell, subtask_dir)
				for task in tasks[i]:
					subtask += "( %s %s )\n" % (time, task)
				subtask += "touch %s/%s.done\n" % (subtask_dir, subtask_file)
				with open(subtask_dir + '/' + subtask_file, 'w') as OUT:
					print (subtask, file=OUT)
					os.chmod(subtask_dir + '/' + subtask_file, 0o744)
			jobs.append(Job(subtask_dir + '/' + subtask_file))
		return jobs

	@property
	def jobs(self):
		if not self._jobs:
			self._jobs = self._write_subtasks(self._init_subtasks(self._read_task()))
		return self._jobs

	def is_finished(self):
		return self.job.is_finished()

	def set_task_finished(self):
		self.job.set_task_finished()

	def set_run(self, max_parallel_job=5, job_type='local', interval_time=30, cpu=1, mem=None, \
			use_drmaa=False, cfg_file=None, submit=None, kill=None, check_alive=None, job_id_regex=None):
		if not cfg_file:
			_cfg_file = os.path.dirname(os.path.realpath(__file__)) + '/cluster.cfg'
			if os.path.exists(_cfg_file):
				cfg_file = _cfg_file

		if job_type == 'local':
			self.run = Local(self.jobs, max_parallel_job, self.shell, interval_time)
		elif use_drmaa:
			self.run = Drmaa(self.jobs, max_parallel_job, self.shell, job_type, interval_time, \
				cpu, mem, cfg_file, submit)
		else:
			self.run = Cluster(self.jobs, max_parallel_job, self.shell, job_type, interval_time, \
				cpu, mem, cfg_file, submit, kill, check_alive, job_id_regex)
		return self.run


class Run(object):

	instances = []

	def __init__(self, jobs, max_parallel_job=5, shell='/bin/bash', job_type='local', interval_time=30, cpu=1, mem=None, \
			cfg_file=None, submit=None, kill=None, check_alive=None, job_id_regex=None):
		self.jobs = jobs
		self.unfinished_jobs = []
		self.running_jobs = []
		self.job_type = job_type.lower()
		self.max_parallel_job = int(max_parallel_job)
		self.interval_time = int(str(interval_time).lower().strip('s'))
		self.cpu = str(cpu)
		self.shell = str(shell)
		self._submit = submit
		self._kill = kill
		self._check_alive = check_alive
		self._job_id_regex = job_id_regex
		if cfg_file:
			self._parse_cfg(cfg_file)
		if not mem:
			mem = '%sG' % self.cpu
		self.mem = self._parse_mem(str(mem))
		self.is_finished()
		Run.instances.append(self)

	def _parse_cfg(self, infile):
		with open(infile) as IN:
			section = None
			for line in IN:
				line = line.strip()
				if not line or line[0].startswith('#'):
					continue
				if line.startswith('['):
					if section:
						break
					group = re.search(r'\[\s*(\S+)\s*\]', line)
					if group and self.job_type in group.group(1).lower():
						section = True
					continue
				elif section:				
					group = re.search(r'([^;\s]+)\s*[=:]\s*([^;#\n]+)(\s*|#.*)$', line) # a option = value1 value2 # annotation
					if group:
						name, value = group.group(1).lower(), group.group(2)
						if name == 'submit' and not self._submit:
							self._submit = value
						elif name == 'kill' and not self._kill:
							self._kill = value
						elif name in ['check-alive', 'check_alive'] and not self._check_alive:
							self._check_alive = value
						elif name in ['job-id-regex', 'job_id_regex'] and not self._job_id_regex:
							self._job_id_regex = value

	def _parse_mem(self, mem):

		if self.job_type == 'slurm' and '--mem-per-cpu' in self._submit:
			return int(parse_num_unit(mem, 1024)/1000000/int(self.cpu)) + 1
		if self.job_type == 'lsf' and 'mem' in self._submit:
			unit = 'M'
			unit_cfg_fpath = os.getenv('LSF_ENVDIR') + "/lsf.conf"
			if os.path.exists(unit_cfg_fpath):
				with open(unit_cfg_fpath) as IN:
					g = re.search(r'LSF_UNIT_FOR_LIMITS\s*=\s*(\S+)\s*', IN.read(), re.I)
					if g:
						unit = g.group(1)
			return parse_num_unit(mem) / parse_num_unit("1%s" % (unit))
		return mem

	def submit(self, job):
		assert 'script' in self._submit
		job.cmd = self._submit.format(cpu=self.cpu, mem=self.mem, shell=self.shell, \
			script=job.path, out=job.out, err=job.err)
		_, stdout, _ = self.run(job.cmd)
		job.id = self.parse_id(stdout)
		return job.id

	def kill(self, job):
		assert 'job_id' in self._kill
		cmd = self._kill.format(job_id=job.id)
		return self.run(cmd)

	def check_alive(self, job):#Here we may need to parase job status
		if job.is_finished():
			return False
		
		# if this job has errors, `is_finished()` will always return `False`, so we need to check further.
		assert 'job_id' in self._check_alive
		cmd = self._check_alive.format(job_id=job.id)
		returncode, stdout, stderr = self.run(cmd, check=False)
		if self.job_type == 'slurm':
			return returncode == 0 and job.id in stdout #slurm will save a job info. in 300s by default
		return returncode == 0

	def has_alive(self):
		for job in self.running_jobs:
			if self.check_alive(job):
				return True
		return False

	def parse_id(self, has_id):
		assert '(' in self._job_id_regex and ')' in self._job_id_regex
		group = re.search(r'%s' % self._job_id_regex, has_id)
		if not group:
			log.critical("Failed to parse job id using job-id-regex:%s in log:%s" % (self._job_id_regex, has_id))
		return group.group(1)

	def run(self, cmd, check=True):
		p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = (byte2str(i) for i in p.communicate())
		# log.error("cmd:%s, stdout:%s, stderr:%s" % (cmd, stdout, stderr))
		if check and p.returncode != 0:
			stderr = stderr.replace("\n", "; ")
			log.critical("Command '%s' returned non-zero exit status %d, error info: %s." % (cmd, p.returncode, stderr))
		return p.returncode, stdout, stderr
		
	def rerun(self):
		self.start()

	def is_finished(self):
		self.unfinished_jobs = []
		for job in self.jobs:
			if not job.is_finished():
				self.unfinished_jobs.append(job)
		if self.unfinished_jobs and len(self.unfinished_jobs) < 5: # Avoid delays in generating done files
			time.sleep(5)
			for job in list(self.unfinished_jobs):
				if job.is_finished():
					self.unfinished_jobs.remove(job)
		if self.unfinished_jobs:
			return False
		else:
			if self in Run.instances:
				Run.instances.remove(self)
			return True

	def _clean(self):
		log.warning('Accepted a killed signal and killing all running jobs, please wait...')
		with open(os.devnull, 'w') as devnull:
			pjobs = self.running_jobs[:]
			for job in pjobs:
				ret = subprocess.call(self._kill.format(job_id=job.id), shell=True, stdout=devnull, stderr=devnull)
				if ret == 0:
					self.running_jobs.remove(job)
		if self.has_alive():
			log.error("Failed to kill the running jobs, please check")
		else:
			log.warning('Killed all running jobs done')

	@classmethod
	def clean(cls, signum, frame):
		for self in Run.instances:
			self._clean()
		log.warning('Exit!')
		sys.exit(1)

	@property
	def check_running(self):
		running = 0
		pjobs = self.running_jobs[:]
		for job in pjobs:
			if self.check_alive(job):
				running += 1
			else:
				self.running_jobs.remove(job)
		return running

	def start(self):
		log.info('Total jobs: ' + str(len(self.unfinished_jobs)))
		self._start()

	def _start(self):
		raise NotImplementedError
		
class Local(Run):
	"""docstring for local"""
	def __init__(self, jobs, max_parallel_job, shell, interval_time):
		super(Local, self).__init__(jobs, max_parallel_job, shell, 'local', interval_time, \
				submit="%s {script} > {out} 2> {err}" % shell, kill="kill {job_id}")
		self.ppid = os.getpid()
	
	def check_alive(self, job):
		return psutil.pid_exists(job.id) and psutil.Process(job.id).ppid() == self.ppid

	def parse_id(self, has_id):
		return

	def _start(self):
		subids = []
		for i in range(len(self.unfinished_jobs)):
			job = self.unfinished_jobs[i]
			newpid = os.fork()
			if newpid == 0:
				self.submit(job)
				os._exit(0)
			else:
				job.id = newpid
				self.running_jobs.append(job)
				log.info('Submitted jobID:[' + str(newpid) + '] jobCmd:['  + job.path + '] in the local_cycle.')
				if i >= self.max_parallel_job - 1:
					os.wait()
			time.sleep(0.5)

		pjobs = self.running_jobs[:]
		while pjobs:
			pjob = pjobs.pop()
			if self.check_alive(pjob):
				os.waitpid(pjob.id, 0)
				time.sleep(0.5)
			self.running_jobs.remove(pjob)

	def _clean(self):
		if os.getpid() != self.ppid:
			sys.exit(1)
		super(Local, self)._clean()

class Cluster(Run):

	def _start(self):
		j = 0
		while j < len(self.unfinished_jobs):
			job = self.unfinished_jobs[j]
			if j < self.max_parallel_job or self.check_running < self.max_parallel_job:
				self.submit(job)
				self.running_jobs.append(job)
				log.info('Submitted jobID:[' + job.id + '] jobCmd:['  + job.path + '] in the ' + self.job_type + '_cycle.')
				j += 1
			else:
				time.sleep(self.interval_time)
		else:
			while (1):
				if self.check_running:
					time.sleep(self.interval_time)
				else:
					break
		time.sleep(1)
		
class Drmaa(Run):

	def __init__(self, jobs, max_parallel_job, shell, job_type, interval_time, cpu, mem, cfg_file, submit):
		super(Drmaa, self).__init__(jobs, max_parallel_job, shell, job_type, interval_time, cpu, mem, \
				cfg_file, submit)
		self.option = self._get_option()

		import drmaa as drmaa
		self.drmaa = drmaa
		self.session = drmaa.Session()
		self.session.initialize()

	def _start(self):
		j = 0
		jt = self.session.createJobTemplate()
		jt.jobEnvironment = os.environ.copy()
		jt.nativeSpecification = self.option
		while j < len(self.unfinished_jobs):
			if j < self.max_parallel_job or self.check_running < self.max_parallel_job:
				job = self.unfinished_jobs[j]
				jt.remoteCommand = job.path
				jt.outputPath = ':%s' % job.out
				jt.errorPath = ':%s' % job.err
				jt.workingDirectory = os.path.dirname(job.path)
				job.id = self.session.runJob(jt)
				self.running_jobs.append(job)
				log.info('Submitted jobID:[' + job.id + '] jobCmd:['  + job.path + '] in the ' + self.job_type + '_cycle.')
				j += 1
			else:
				time.sleep(self.interval_time)
		else:
			while (1):
				if self.check_running:
					time.sleep(self.interval_time)
				else:
					break
		time.sleep(5)
		self.session.deleteJobTemplate(jt)
		self.session.exit()

	def kill(self, job):
		try:
			self.session.control(job.id, self.drmaa.JobControlAction.TERMINATE)
		except Exception:
			pass

	def check_alive(self, job):
		return self.session.jobStatus(job.id) not in [self.drmaa.JobState.UNDETERMINED, \
				self.drmaa.JobState.DONE, self.drmaa.JobState.FAILED]

	@property
	def check_running(self):
		running = 0
		pjobs = self.running_jobs[:]
		for job in pjobs:
			if self.check_alive(job):
				running += 1
			else:
				try:
					self.session.wait(job.id, self.drmaa.Session.TIMEOUT_WAIT_FOREVER)
				except Exception:
					pass
				finally:
					self.running_jobs.remove(job)
		return running

	def _clean(self):
		log.warning('Accepted a killed signal and killing all running jobs, please wait...')
		pjobs = self.running_jobs[:]
		for job in pjobs:
			try:
				self.session.control(job.id, self.drmaa.JobControlAction.TERMINATE)
				self.running_jobs.remove(job)
			except Exception:
				pass
		if self.has_alive():
			log.error("Failed to kill the running jobs, please check")
		else:
			log.warning('Killed all running jobs done')
		self.session.exit()

	def _get_option(self):
		assert self._submit
		opt = ''
		opts = self._submit.split()
		i = 0
		while i < len(opts):
			p = opts[i]
			if i == 0 and not p.startswith('-'):
				i += 1
			elif p.startswith('-'):
				if i < len(opts):
					v = opts[i + 1]
					if not v.startswith('-'):
						if v not in ['{out}', '{err}', '{script}']:
							opt += '%s %s ' % (p, v)
						i += 2
					else:
						opt += '%s ' % p
						i += 1
				else:
					opt += '%s ' % p
					i += 1
			else:
				if p not in ['{out}', '{err}', '{script}']:
					opt += '%s ' % p
				i += 1
		if self.job_type == 'sge' and "-w n" not in opt:
			opt += ' -w n'
		return opt.format(cpu=self.cpu, mem=self.mem, shell=self.shell)

signal.signal(signal.SIGINT, Run.clean)
signal.signal(signal.SIGTERM, Run.clean)
