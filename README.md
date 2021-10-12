# Paralleltask
Paralleltask is a simple and lightweight parallel task engine. It can launch a given number of tasks from a batch of independent tasks, and keep this number of running tasks until all tasks are completed.

## Why Paralleltask?
Suppose you have dozens or hundreds of independent tasks that can run in parallel (non-independent tasks can be put together to form an independent task group). Due to the limitation of computing resources, you cannot run all tasks at the same time. Of course, it is not realistic to run one by one, so you want to run a specific number of tasks at the same time, and keep this number of running tasks (once a task is completed, start a new task) until all tasks are completed.

* zero configuration, no dependencies, no prior knowledge required, easy to install and use.

* support breakpoint resume, automatically re-execute failed tasks and ignore successful tasks.

* automatically kill submitted tasks once the main program receives a termination signal (`Ctrl+C`).

* support multiple task scheduling systems, such as `LOCAL`, `SGE`, `PBS`, `SLURM` and `LSF`.

* automatically convert relative path to absolute path in shell scripts.

* support python 2 and 3.

## Installation
```
pip install paralleltask
```

If you prefer to use the [drmaa](https://github.com/pygridtools/drmaa-python) library, instead of using commands (such as `qsub`) to submit and control tasks, see [here](https://github.com/moold/ParallelTask/blob/master/DRMAA.md) to install `drmaa`.

## Usage
```
paralleltask work.sh
```

The only required input file `work.sh` is a command collection file, which contains all the task commands that need to be run. A task command can be one or more lines, and an independent task group can be set by the parameter `--lines`. Using `paralleltask -h` for details.

## Testing
```bash
# produce a work file: test.sh
for i in {1..50};do echo "sleep ${i} && echo \"I am subtask${i}\"" >> test.sh;done;
# run
paralleltask test.sh
```
A demo file `test.sh` is [here](https://github.com/moold/ParallelTask/blob/master/test/test.sh)


## Configuration 
If you want to change some of the default settings, you can pass parameters (use `paralleltask -h` for details) or directly edit the configure template file `cluster.cfg`.

***Note***: Paralleltask will replace `{mem}`, `{cpu}`, `{bash}`, `{out}`, `{err}`, `{script}` and `{job_id}` with specific values needed for each jobs, see the configure template [file](https://github.com/moold/ParallelTask/blob/master/src/paralleltask/cluster.cfg) for details.

## Getting Help

Feel free to raise an issue at the [issue page](https://github.com/moold/ParallelTask/issues), and welcome to [pull request](https://github.com/moold/ParallelTask/pulls) if you find a bug or have an idea for this project.

## Star
You can track updates by tab the `Star` button on the upper-right corner at the [github page](https://github.com/moold/ParallelTask).
