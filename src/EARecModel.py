import pandas as pd
import networkx as nx
from collections import Counter
from datetime import datetime
import time

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
