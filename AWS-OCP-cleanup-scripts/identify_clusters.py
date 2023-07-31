import boto3
import json
import argparse
import sys
import os

parser = argparse.ArgumentParser()
parser.add_argument("--Region", "-R", help="Enter AWS Default Region",nargs=1,required=True)
parser.add_argument("--acc_id", "-id", help="Enter AWS account id",nargs=1,required=True)

args = parser.parse_args()

if len(args.acc_id[0]) != 12:
    print("Please check if you have entered the correct AWS account id")
    exit(1) 

print("Default region selected: %s" % args.Region[0])
os.environ["AWS_DEFAULT_REGION"] = args.Region[0]

client = boto3.client('resourcegroupstaggingapi')
ec2 = boto3.client('ec2')

def get_tag_keys():
    tag_keys = []
    response = client.get_tag_keys()
    tag_keys.extend(response['TagKeys'])
    while 'PaginationToken' in response and response['PaginationToken'] != "":
        current_token = response['PaginationToken']
        response = client.get_tag_keys(PaginationToken=current_token)
        tag_keys.extend(response['TagKeys'])
    return tag_keys

def get_only_clusters(tags):
    return [tag for tag in tags if "kubernetes.io/cluster" in tag]


def get_resources_for_cluster(cluster_tag):
    resources = []
    response = client.get_resources(TagFilters=[cluster_tag])
    resources.extend([resource['ResourceARN']
                      for resource in response['ResourceTagMappingList']])
    while 'PaginationToken' in response and response['PaginationToken'] != "":
        current_token = response['PaginationToken']
        response = client.get_resources(
            PaginationToken=current_token, TagFilters=[cluster_tag])
        resources.extend([resource['ResourceARN']
                          for resource in response['ResourceTagMappingList']])
    return resources

def filter_list(key, full_list):
    return [resource.split(f"arn:aws:ec2:{args.Region[0]}:{args.acc_id[0]}:{key}")[-1] for resource in full_list if key in resource]

def remove_whitelisted_tags(tags, whitelist):
    return [tag for tag in tags if all(whitelist_tag not in tag for whitelist_tag in whitelist)]

def main():
    print("Searching for clusters, Please wait this may take a while!")

    with open("./whitelist.json") as json_file:
        whitelist = json.load(json_file)

    tag_keys = get_tag_keys()
    only_clusters = get_only_clusters(tag_keys)
    clusters_to_delete = remove_whitelisted_tags(only_clusters, whitelist['tags'])

    clusters_with_instances = []
    total_instances_counted = 0
    for cluster in clusters_to_delete:
        resources = get_resources_for_cluster({"Key": cluster, "Values": ["owned"]})
        instances = filter_list('instance/', resources)
        volumes = filter_list('volume/', resources)
        if len(instances) > 0:
            instance_vol = boto3.resource('ec2', region_name='us-west-2')
            try:
                volume = instance_vol.Volume(volumes[0])
                cluster_creation_time=volume.create_time.strftime("%Y-%m-%d %H:%M:%S")
            except:
                cluster_creation_time="undefined"

            clusters_with_instances.append({
            "cluster": cluster,
            "instance_count": len(instances),
            "cluster_creation_time": cluster_creation_time
        })
            total_instances_counted += len(instances)

    print("Total instances count=",total_instances_counted)

    jsn= { "clusters": clusters_with_instances }
    json_output= json.dumps(jsn,indent=4)
    print(json_output)

    # Writing output to clusters.json file
    with open("clusters.json", "w") as outfile:
        outfile.write(json_output)

if __name__ == "__main__":
    main()