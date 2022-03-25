# Openshift cluster cleanup scripts for AWS

This folder contains python scripts to help identify and delete openshift(OCP) clusters deployed on AWS. 
The scripts make use of boto3 a python SDK(software developement kit) for AWS. You can use the scripts to only identify clusters or identify+delete clusters. 

Prerequsites: 
install boto3 : python -m pip install boto3  

To enable boto3 to communicate with your AWS account you will first need to configure credentials by following any of the below methods: 

- Configure ~/.aws/credentials and ~/.aws/config files so that they look like this:  

   ~/.aws/config  
[default]  
region = us-east-1  

   ~/.aws/credentials  
[default]  
aws_access_key_id = xyz  
aws_secret_access_key = abc123  

- Exporting the following environment variables with the right values:  
export AWS_ACCESS_KEY_ID=  
export AWS_SECRET_ACCESS_KEY=  
export AWS_DEFAULT_REGION=  

## Identify clusters 

To identify clusters deployed in you AWS account in the specified region, you can use the `identify_clusters.py` script. The script takes in 2 command line arguments with the flags: -id to input your 12 digit AWS account id and -R to specify the region to search in. Note: the region specified here must match the region specified while configuring aws configs above. To search for a different region you first have to modify the aws region in the configs either by modifying ~/.aws/config or exporting AWS_DEFAULT_REGION env var again. 

If there are clusters which need to be ignored/which need not be cleaned you can add the cluster name to the whitelist.json file. An example_whitelist.json file is provided for reference.**The whitelist.json file needs to be created mandatorily, copy the example_whitelist.json and make a new file called whitelist.josn, it can be left unpopulated/unchanged if no clusters need to be whitelisted.** Please note the first 2 entries in the example_whitelist file are clusters used by the ocp perfscale team as long term infrastructure and should not be deleted.  

Run commands:  
`cp example_whitelist.json whitelist.json`  
`python3 identify_clusters.py -R <AWS region> -id <AWS account id>`  

Once the script has run, a list of all the OCP clusters in your account in that region are displayed and a clusters.json file gets generated which can be used to generate cluster metadata as seen in the next script.

## Generate Metadata

The `generate_metadata.py` script is used to generate a metadata.json file for each of the clusters identified in clusters.json. This script takes in 2 command line arguments: -R for the default Region and -bd for the *openshift base domain* used while deploying the cluster. This metadata.json is necessary if you want to delete the cluster. A openshift install binary file uses this metadata.json file to identify and delete all resources associated with the cluster. This metadata.json will help the binary identify all the resources such as instances,volumes,elastic-ip's,vpc's,subnets etc.

Run Command: `python3 generate_metadata.py -R <AWS region> -bd <openshift cluster base domain>`  

upon running this script a new folder named *clusters/* is created with a seperate folder for each entry in the clusters.json file. 
An example tree schema of the generated folder is given below: 
$ tree clusters

```bash
clusters
├── ci-4-10-aws-acs
│   └── metadata.json
├── perf-code49
│   └── metadata.json
├── stackrox-4-7-aws
│   └── metadata.json
```

## Deleting a Cluster

To delete an identified cluster for which a metadata.json has been generated, you first need to download an openshift install binary. You can make use of your own binary or download one stored on the redhat internal dell server. 
Note: You need to be connected to the redhat vpn to download this. The download will take a while :)
Run the command from the root of the AWS-OCP-cleanup-scripts folder.  
Download command : `wget http://dell-r510-01.perf.lab.eng.rdu2.redhat.com/openshift-bin/openshift-install` 

`chmod +x openshift-install`

once downloaded, copy the install binary into any/all of the folders in clusters/ ; **Eg**: cp openshift-install ./clusters/ci-4-10-aws-acs/ , This will make sure that the metadata.json and the binary are in the same folder. Make sure to copy the openshift install binary into each sub folder and not move since it will get deleted once used and you will have to download it again! Run the below command from within the newly created named folder. 

Command to delete a cluster : `./openshift-install destroy cluster --log-level=debug` 


