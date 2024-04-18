import json
import ast

from utils.logger import logger


## ------------------------------------------------------------------------------------
## Convert terraform.tfvars to JSON
## Notes:
##   1. I know it's dumb to home-roll your own parser, but I don't want to introduce extra random
##      packages from the internet. This is fine for our purposes.
##   2. Clean command: `sed '/^\s*\/\*/,/^\s*\*\//d;/^\s*#/d' terraform.tfvars > terraform_no_comments.tfvars`
##      However, `sed` has problem on MacOS, so sticking with (uglier) native Python.
## ------------------------------------------------------------------------------------

# Rules:
#   1. Purge any blank line.
#   2. Purge any line starting with a `#``
#   3. Purge any line starting with `/*`, `*/`, or in between them.
#   4. Purge via tracking indices; purge from right-to-left to avoid index shifting.

# Assumptions:
#   1. Inline comments will only use 1 `#`
#   2. All discrete keys start on Column 1 of a line.

# Edgecase:
#   1. `default_tags` has closing brace without leading space.


lines_array = []
data = {}
default_tags = {}


def purge_indices_in_reverse(indices_to_pop):
    for i in reversed(indices_to_pop):
        lines_array.pop(i)


def convert_tfvars_to_dictionary(file):

    global lines_array

    with open(file, 'r') as file:
        lines = file.readlines()
        lines_array = [line.strip() for line in lines]

        # 1) Remove any blank link in file
        flag_skip_block_comment = False
        indices_to_pop = []

        for i, line in enumerate(lines_array):
            if (line.strip() == "") or (line.startswith('#')):
                indices_to_pop.append(i)

            # Once '/*' detected, flag every line for deletion until '*/' encountered.
            elif line.startswith("/*"):
                flag_skip_block_comment = True
                indices_to_pop.append(i)
                continue
            elif line.startswith("*/"):
                flag_skip_block_comment = False
                indices_to_pop.append(i)
                continue
            elif flag_skip_block_comment:
                indices_to_pop.append(i)

        logger.debug(f"Indices to pop: {indices_to_pop}")
        purge_indices_in_reverse(indices_to_pop)


        # 2) Purge inline comments from rationalized kv pairs
        for i, line in enumerate(lines_array):
            line = line.rsplit('#')[0]
            lines_array[i] = line


        # 3) Handle `default tags` edge case: extract this value specifically into a dict and pop lines.
        start_handling_tags = False
        indices_to_pop = []

        for i, line in enumerate(lines_array):
            if "default_tags" in line:
                start_handling_tags = True
                indices_to_pop.append(i)
            elif (start_handling_tags) and ("=" in line):
                key, value = [x.strip() for x in line.split('=', 1)]
                default_tags[key] = value.strip('"')
                indices_to_pop.append(i)
            elif (start_handling_tags) and (line == "}"):
                indices_to_pop.append(i)
                break

        purge_indices_in_reverse(indices_to_pop)
        data['default_tags'] = default_tags


        # 4) Handle multiline arrays. Find opening line with '=' and ending in '['
        target_index = None
        indices_to_pop = []
        for i, line in enumerate(lines_array):
            if ("=" in line) and (line.strip()[-1] == "["):
                target_index = i
                continue

            if (target_index is not None):
                lines_array[target_index] += line.strip()
                indices_to_pop.append(i)

            if (line.strip()[-1] == "]"):
                target_index = None

        purge_indices_in_reverse(indices_to_pop)


        # 5) Convert items to proper python types.
        for line in lines_array:
            if "=" in line:
                key, value = [x.strip() for x in line.split('=', 1)]
                if value.lower() == 'true':
                    data[key] = True
                elif value.lower() == 'false':
                    data[key] = False
                else:
                    data[key] = ast.literal_eval(value)

    return data

    # # with open('output.json', 'w') as file:
    # #     json.dump(data, file, indent=4)


def get_tfvars_as_json():
    return convert_tfvars_to_dictionary('terraform.tfvars')
