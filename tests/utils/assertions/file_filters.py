from tests.utils.config import all_template_files, kitchen_sink


def filter_templates(desired_files: list) -> dict:
    """
    Filter templates based on desired files.
      - If files are not specifically named in the testcase, generate all of them.
      - If named files are provided, only use those.
      - If kitchen_sink is True, we are doing a delibrate full-coverage test.
    """
    if kitchen_sink or desired_files == []:
        return all_template_files
    return {k: v for k, v in all_template_files.items() if k in desired_files}
