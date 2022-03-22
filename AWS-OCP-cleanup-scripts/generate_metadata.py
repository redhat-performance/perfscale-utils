import json
import pprint
import os
import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

pp = pprint.PrettyPrinter()

parser = argparse.ArgumentParser()
parser.add_argument("--Region", "-R", help="Enter AWS Default Region",nargs=1,required=True)
parser.add_argument("--base_domain", "-bd", help="Enter clusters' openshift base domain",nargs=1,required=True)

args = parser.parse_args()

print("Default region selected:",args.Region[0],"Openshift cluster base domain entered:",args.base_domain[0])

with open("./clusters.json") as json_file:
    clusters = json.load(json_file)['clusters']



for cluster in clusters:
    infra_id = cluster['cluster'].split('kubernetes.io/cluster/')[-1]
    cluster_name = "-".join(infra_id.split('-')[:-1])
    
    cluster_json = {
        "clusterName": cluster_name,
        "clusterID": "foo",
        "infraID":infra_id,
        "aws": {
            "region":f"{args.Region[0]}",
            "identifier":[
                {f"kubernetes.io/cluster/{infra_id}":"owned"},
                {"openshiftClusterID":"foo"}
            ],
            "clusterDomain":f"{cluster_name}.{args.base_domain[0]}"
            }
        }
    pp.pprint(cluster_json)

    with tempfile.TemporaryDirectory(dir=".") as temp_dir:
        Path(f"clusters/{cluster_name}").mkdir(parents=True, exist_ok=True)
        with open(f"clusters/{cluster_name}/metadata.json", 'w+') as json_file:
            json.dump(cluster_json, json_file, sort_keys=True, indent=4)

        