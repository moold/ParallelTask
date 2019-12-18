# ParallelTask
A super simple and lightweight parallel task engine using drmaa

## USUAGE
The doc. and API examples are in `main.py`, use `python main.py -h` for details.

The default cluster_option is listed below, which also can be set manually:
* sge    `-l vf={vf} -pe smp {cpu} -S {bash} -w n`
* pbs    `-l nodes=1:ppn={cpu}`
* slurm  `--cpus-per-task={cpu} --mem-per-cpu={vf}`
* lsf    `-n {cpu}`

## INSTALL

* **Configure drmaa for SGE**
```
pip install drmaa
export DRMAA_LIBRARY_PATH=/path_to_sge/lib/lx-amd64/libdrmaa.so.1.0
```

* **Configure drmaa for PBS**
<!--https://hub.docker.com/r/agaveapi/torque -->
```
pip install drmaa
wget https://downloads.sourceforge.net/project/pbspro-drmaa/pbs-drmaa/1.0/pbs-drmaa-1.0.19.tar.gz
tar -vxzf pbs-drmaa-1.0.19.tar.gz
cd pbs-drmaa-1.0.19
./configure && make && make install
export DRMAA_LIBRARY_PATH=`pwd`/pbs_drmaa/.libs/libdrmaa.so.1
```

* **Configure drmaa for slurm**  
<!-- https://hub.docker.com/r/ohsucompbio/slurm -->
```
pip install drmaa
wget https://github.com/natefoo/slurm-drmaa/releases/download/1.1.0/slurm-drmaa-1.1.0.tar.gz
tar -vxzf slurm-drmaa-1.1.0.tar.gz
cd slurm-drmaa-1.1.0
./configure && make && make install
export DRMAA_LIBRARY_PATH=`pwd`/slurm_drmaa/.libs/libdrmaa.so.1
```

* **Configure drmaa for LSF**
```
pip install drmaa
wget https://github.com/IBMSpectrumComputing/lsf-drmaa/archive/v1.11.tar.gz
tar -vxzf v1.11.tar.gz
cd lsf-drmaa-1.11
./configure && make && make install
export DRMAA_LIBRARY_PATH=`pwd`/lsf_drmaa/.libs/libdrmaa.so.1
```