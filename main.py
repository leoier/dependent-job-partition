import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt


class UnionFind:
    def __init__(self, ignore_source=None):
        self.id = []
        self.sizes = []
        self.dict = {}
        self.num_segments = 0
        self.ignore_source = ignore_source


    def add(self, u):
        if u in self.dict.keys():
            return
        id = len(self.id)
        self.dict[u] = id
        self.id.append(id)
        self.sizes.append(1)
        self.num_segments += 1


    def find(self, u):
        if u not in self.dict.keys():
            return None
        id = self.dict[u]
        while id != self.id[id]:
            id = self.id[id]
        return id


    def connected(self, u, v):
        return self.find(u) == self.find(v)


    def union(self, u, v):
        self.add(u)
        self.add(v)
        # ignore the edge if it starts with the ignore_source
        if self.ignore_source is not None and u == self.ignore_source:
                return
        root_u = self.find(u)
        root_v = self.find(v)
        if root_u == root_v:
            return
        
        if self.sizes[root_u] < self.sizes[root_v]:
            self.id[root_u] = root_v
            self.sizes[root_v] += self.sizes[root_u]
        else:
            self.id[root_v] = root_u
            self.sizes[root_u] += self.sizes[root_v]

        self.num_segments -= 1

    
    def get_segments(self):
        segments = {}
        for u in self.dict.keys():
            root = self.find(u)
            if root not in segments.keys():
                segments[root] = []
            segments[root].append(u)
        return [segments[key] for key in segments.keys()]


'''
    Set the relevant variables
'''
working_dir = ""
filename_dependencies = ""
filename_valid_jobs = ""
source = ""  # source job

df = pd.read_excel(working_dir + filename_dependencies, dtype=str,
                   names=["job_name", "job_id", "db_name", "db_id", 
                          "parent_name", "parent_id", "parent_db_name", "parent_db_id"])

with open(working_dir + filename_valid_jobs, "r") as f:
    valid_jobs = set(f.read().split(', '))

# filter out invalid jobs
mask = df["job_name"].isin(valid_jobs)
df = df[mask]

# filter out parent_name not in job_name
mask = (df["parent_name"] == source) | df["parent_name"].isin(set(df["job_name"]))
df = df[mask]

# segment the jobs that are not connected
uf = UnionFind(ignore_source=source)
G = nx.DiGraph()

for index, row in df.iterrows():
    uf.union(row["parent_name"], row["job_name"])
    G.add_edge(row["parent_id"], row["job_id"])

print(f"Number of segments: {uf.num_segments}")

# # visualize the graph
# nx.draw_networkx(G)
# plt.show()


# TODO: add support for multiple segments exceeding size limit
# find the segment with the largest number of jobs
segs = uf.get_segments()
max_seg = max(segs, key=lambda s: len(s))
segs.sort(key=lambda s: len(s), reverse=True)

print(f"Number of jobs in the largest segment: {len(max_seg)}")
# print("\n".join(max_seg))

# construct the subgraph for the largest segment
mask = df["job_name"].isin(max_seg) | df["parent_name"].isin(max_seg)
df_sub = df[mask]
G_sub = nx.DiGraph()
for index, row in df_sub.iterrows():
    G_sub.add_edge(row["parent_name"], row["job_name"])

# # visualize the subgraph
# nx.draw_networkx(G_sub)
# plt.show()


# find the longest path from source to each node as depth
depth = {node:-1e9 for node in G_sub.nodes()}
depth[source] = 0
# Dijkstra's algorithm on topological sorted nodes
for node in nx.topological_sort(G_sub):
    for u, v in G_sub.in_edges(node):
        if depth[v] < depth[u] + 1:
            depth[v] = depth[u] + 1

# aggregate the jobs by depth
depth_jobs = {}
for node in G_sub.nodes():
    if depth[node] not in depth_jobs.keys():
        depth_jobs[depth[node]] = []
    depth_jobs[depth[node]].append(node)

# # print the jobs in each depth
# for key in sorted(depth_jobs.keys()):
#     print(f"Depth {key}: {len(depth_jobs[key])} jobs")
#     print("\n".join(depth_jobs[key]))
#     print("\n")


# output the results
out_segs = pd.DataFrame([{"segment": f"{i} @ {len(seg)}", "job": job} 
                         for i, seg in enumerate(segs) 
                         for job in seg 
                         if len(seg) != len(max_seg)])

out_segs.to_csv(working_dir + "job_segs.csv", encoding="GBK", index=False)

out_depths = pd.DataFrame([{"depth": depth, "job": job} 
                           for depth in sorted(depth_jobs.keys()) 
                           for job in depth_jobs[depth]
                           if depth != 0]
                           )

n_per_group = 10
out_depths_rn = out_depths.groupby("depth").cumcount()
out_depths["group"] = out_depths_rn.apply(lambda x: x // n_per_group)
out_depths["group_num"] = out_depths_rn.apply(lambda x: x % n_per_group + 1)
out_depths = out_depths[["depth", "group", "group_num", "job"]]

out_depths.to_csv(working_dir + "job_max_seg.csv", encoding="GBK", index=False)
