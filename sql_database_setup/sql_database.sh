#!/bin/bash
# Load ONE .tsv into MySQL.
#
# First argument is the file. Anything AFTER it is forwarded straight to
# load_sentences.py, so you can set the worker count and batch size per run:
#
#   sbatch sql_database.sh aa.tsv                   # defaults
#   sbatch sql_database.sh aa.tsv -n 8              # 8 workers
#   sbatch sql_database.sh aa.tsv -n 8 -b 100000    # 8 workers, 100k batch

# ---------------------------------------------------------------------------
# SLURM resource requests (read by `sbatch`, ignored by bash as comments).
# NOTE: if you pass a big -n, bump --cpus-per-task to match, or override it at
# submit time:  sbatch --cpus-per-task=8 sql_database.sh aa.tsv -n 8
# ---------------------------------------------------------------------------
#SBATCH --job-name=load_sentences_kcbbe
#SBATCH --partition=assemblix
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=load_%j.out

# Shell safety: -u errors on unset vars, pipefail catches failures inside pipes.
set -uo pipefail

# Require at least the input file.
if [[ $# -lt 1 ]]; then
    echo "usage: sbatch 1.0.sql_database.sh <input.tsv> [-n N_PROCESS] [-b BATCH_SIZE]" >&2
    exit 1
fi


# Keep each spaCy worker single-threaded (avoid thread oversubscription).
export OMP_NUM_THREADS=1
# Fallback worker count = cores SLURM gave us. Overridden if you pass -n.
export N_PROCESS=${SLURM_CPUS_PER_TASK}


# "$1"      -> the input file (required)
# "${@:2}"  -> every argument after the file (e.g. -n 8 -b 100000),
#              forwarded verbatim to the python CLI. A passed -n/-b overrides
#              the fallback above, because a CLI flag beats the env var.
python database.py "$1" "${@:2}"