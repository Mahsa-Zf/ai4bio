#!/bin/bash
#SBATCH --job-name=embed_pubmed_kcbbe
#SBATCH --gres=shard:2
#SBATCH --partition=assemblix
#SBATCH --array=0-7                 # 7 workers, task ids 0..6
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=24:00:00
#SBATCH --output=embed_%A_%a.log     # one log per worker (%A=array id, %a=task id)


# source ~/venv/bin/activate
python embed.py