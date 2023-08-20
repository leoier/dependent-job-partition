# Dependent Job Partition

A useful tool to analyze the dependency relationships of the jobs and partition them into groups such that the jobs between groups can be run in parallel. 

## Requirements
- **[Python 3.8+](https://docs.python.org/3/using/index.html)**
- **[Pandas](https://pandas.pydata.org/docs/getting_started/index.html#installation)**
- **[Matplotlib](https://matplotlib.org/stable/index.html#installation)**
- **[NetworkX](https://networkx.org/documentation/stable/install.html)**

## Usage

### Input
- An Excel file containing the dependency relationships of the jobs, one relationship per row. 
- \[Optional\] A text file containing the jobs that should be ignored

### Run the app
```bash
python3 main.py
```

### Output
- csv file `job_segs.csv` for the jobs in each partition except the largest one. Jobs in different partitions can be run in parallel.
- csv file `job_max_seg.csv` for the jobs in the largest partition, partitioned further by the depth of each job. Jobs with depth `k` must be executed after all the jobs with depths `k-1` are finished. Jobs with the same depth can be run in parallel.
