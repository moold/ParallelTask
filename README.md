# ParallelTask
A super simple and lightweight parallel task engine

# Configure drmaa for SGE
```
pip install drmaa
export DRMAA_LIBRARY_PATH=/path_to_sge/lib/lx-amd64/libdrmaa.so.1.0
```

# Configure drmaa for PBS
```
https://hub.docker.com/r/agaveapi/torque
pip install drmaa
wget https://downloads.sourceforge.net/project/pbspro-drmaa/pbs-drmaa/1.0/pbs-drmaa-1.0.19.tar.gz
tar -vxzf pbs-drmaa-1.0.19.tar.gz
cd pbs-drmaa-1.0.19
./configure && make && make install
export DRMAA_LIBRARY_PATH=`pwd`/pbs_drmaa/.libs/libdrmaa.so.1
```

# Configure drmaa for slurm
```
sudo docker run -it -h ernie  -v `pwd`:/tmp ohsucompbio/slurm:latest
pip install drmaa
wget https://github.com/natefoo/slurm-drmaa/releases/download/1.1.0/slurm-drmaa-1.1.0.tar.gz
tar -vxzf slurm-drmaa-1.1.0.tar.gz
cd slurm-drmaa-1.1.0/
./configure && make && make install
export DRMAA_LIBRARY_PATH=`pwd`/slurm_drmaa/.libs/libdrmaa.so.1
```

# Configure drmaa for LSF
```
pip install drmaa
wget https://downloads.sourceforge.net/project/lsf-drmaa/OldFiles/lsf-drmaa-0_1.zip
unzip lsf-drmaa-0_1.zip
cd drmaa_for_lsf/
./configure && make && make install

```