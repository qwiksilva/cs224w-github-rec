import pandas as pd
import networkx as nx
from collections import Counter
from datetime import datetime
import time


# Build a user-user graph base on Yu et al. 
# Params:
#   graph: A Networkx graph
#   owner_to_reviewers: a dict from pr owner -> list of reviewers
#   edge_weights: a dict of dicts, pr owner -> reviewer -> edge weight
#   user_attributes: dict of user attributes, user -> dict ofattributes
# Note: in EARec, edges go from
def build_user_graph(graph, owner_to_reviewers, edge_weights, user_attributes=None, directed=True):
    # Owner node
    for (pr_owner_id, reviewer_set) in owner_to_reviewers.items():
        if not graph.has_node(pr_owner_id):
            graph.add_node(pr_owner_id, is_user=True, **user_attributes[pr_owner_id] if user_attributes else {})

        # Reviewer node
        for reviewer_id in reviewer_set:
            if not graph.has_node(reviewer_id):
                graph.add_node(reviewer_id, is_user=True, **user_attributes[reviewer_id] if user_attributes else {})
            
            if not graph.has_edge(pr_owner_id, reviewer_id):
                weight = edge_weights[pr_owner_id][reviewer_id]
                graph.add_edge(pr_owner_id, reviewer_id, weight=weight)

    return graph

class PullRequest():
    def __init__(self, id, file_paths):
        self.id = pr_id
        self.file_paths = file_paths

# user_pr_set: dict from user -> associated prs
def add_pr(graph, pr_in, user_pr_set):
    weights = {}
    similarities = {}
    for user_id in graph.nodes:
        pr_set = user_pr_set(user_id)

        weight = 0.0
        for pr in pr_set:
            if pr.id in similarities:
                weight += similarities[pr.id]
            else:
                sim = pr_file_sim(pr_in.file_paths, pr.file_paths)
                similarities[pr.id] = sim
                weight += sim

        graph.add_edge(pr_in.id, user_id, weight=weight)

    return graph

def pr_file_sim(a_files, b_files):
    pr_sim = 0.0
    for a in a_files:
        for b in b_files:
            pr_sim += file_sim(a, b)

    return pr_sim

def file_sim(path_a, path_b):
    a_words = set(path_a.split("/"))
    b_words = set(path_b.split("/"))
    return float(len(a_words.intersection(b_words))) / max(len(a_words), len(b_words))


def build_user_graph(graph, data, add_attributes=False, directed=True):
    pr_id_list = data['pr_id'].unique()
    for pr_id in pr_id_list:
        pr_owner_set, reviewer_set = extract_node_ids(pr_id, data)

        # Owner node
        for pr_owner_id in pr_owner_set:
            if not graph.has_node(pr_owner_id):
                user_metadata = extract_metadata(pr_owner_id, data) if add_attributes else {}
                graph.add_node(pr_owner_id, is_user=True, **user_metadata)

            # Reviewer node
            for reviewer_id in reviewer_set:
                if not graph.has_node(reviewer_id):
                    user_metadata = extract_metadata(reviewer_id, data) if add_attributes else {}
                    graph.add_node(reviewer_id, is_user=True, **user_metadata)
                
                if not graph.has_edge(pr_owner_id, reviewer_id):
                    if directed:
                        weight = get_edge_weight(pr_owner_id, reviewer_id, data)
                    else:
                        weight = get_edge_weight(pr_owner_id, reviewer_id, data)
                    graph.add_edge(pr_owner_id, reviewer_id, weight=weight)

    return graph

def get_num_comments(owner, commenter, data):
    comments = data[(data['commenter_id']==commenter) & \
        ((data['head_commit_author_id']==owner)|(data['base_commit_committer_id']==owner))]
    num_comments = len(comments)
    return num_comments  

def get_edge_weight(pr_owner_id, reviewer_id, data):
    df = data[(data['commenter_id']==reviewer_id) & \
        ((data['head_commit_author_id']==pr_owner_id) | (data['head_commit_committer_id']==pr_owner_id))]
    
    comment_times = df['comment_created_at'].map(convert_to_tic)
    df['weight'] = comment_times
    df = df.sort_values(by='weight')

    decay = 0.8
    counts = Counter()
    for index, row in df.iterrows():
        row['weight'] *= decay**counts[(row['pr_id'], row['commenter_id'])]
        counts[(row['pr_id'], row['commenter_id'])] += 1

    weight = df['weight'].sum()
    return weight

def extract_node_ids(pr_id, data):
    # Extract PR owner and metadata
    pr_df = data.loc[data.pr_id == pr_id, :]
    commenter_set = set(pr_df.commenter_id.values)
    head_commiter_set = set(pr_df.head_commit_committer_id.values)
    head_author_set = set(pr_df.head_commit_author_id.values)
    # Only counted as a PR owner if participating in the comments
    pr_owner_set = (head_author_set | head_commiter_set) & commenter_set
    reviewer_set = commenter_set - pr_owner_set
    return pr_owner_set, reviewer_set

def extract_metadata(target, data):
    metadata_cols = ['commenter_username', 'commenter_follower_count',
                        'commenter_total_github_commit_count', 'commenter_base_repo_commit_count']
    metadata_dict = data.loc[(data.commenter_id == target), metadata_cols].iloc[0].to_dict()
    return metadata_dict

def convert_to_tic(s):
    #Jan, 1, 2014
    start_time = time.mktime(datetime(2014, 1, 1).timetuple())
    #Jan, 1, 2019
    end_time = time.mktime(datetime(2019, 1, 1).timetuple())
    time_delta = end_time-start_time
    return float(time.mktime(pd.to_datetime(s).timetuple()) - start_time) / time_delta

def add_pr(graph, pr_data):
    pass
