#!/usr/bin/env python3
import yaml

yaml.sort_base_mapping_type_on_output = False

original_setup = open('../setup.yml', 'r')

cc_first_keys = ["organizations","workspaces","teams","participants","credentials"]
cc_second_keys = ["pipelines","launch","compute-envs"]

cc_first_dict = {}
cc_second_dict = {}

original_yaml = yaml.safe_load(original_setup) #, Loader=Loader)


for key in cc_first_keys:
    cc_first_dict[key] = original_yaml[key]

for key in cc_second_keys:
    cc_second_dict[key] = original_yaml[key]


with open('../cc_first.yaml', 'w') as yamlfile:
    yaml.safe_dump(cc_first_dict, yamlfile, sort_keys=False)

with open('../cc_second.yaml', 'w') as yamlfile:
    yaml.safe_dump(cc_second_dict, yamlfile, sort_keys=False)

