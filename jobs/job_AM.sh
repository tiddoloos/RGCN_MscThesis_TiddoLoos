#!/bin/bash
#SBATCH --partition=normal
#SBATCH --constraint=silver_4110
#SBATCH --job-name=AM_CPU_run
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH -t 100:00:00
#SBATCH --mail-type=ALL
#SBATCH --mail-user=t.j.loos@student.vu.nl

source /home/${USER}/.bashrc
source activate scaling_rgcn

cd "$TMPDIR"/
mkdir ./results
scp -r $HOME/graphdata ./

#Run Program
python /home/loost/RGCN_MscThesis_TiddoLoos/main.py -dataset AM -i 5 -w_grad False -exp attention -w_trans True

#Copy output directory from scratch to results folder on local machine
cd "$TMPDIR"/
scp -r results/* $HOME/results/AM