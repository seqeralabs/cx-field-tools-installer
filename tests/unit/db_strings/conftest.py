import pytest
import tftest

import os
from pathlib import Path
import shutil
import warnings


# TODO: June 21/2025 -- This is a hack to get the test to run.
root = "/home/deeplearning/cx-field-tools-installer"


"""
EXPLANATION
=======================================
I don't want tests happening in the source project. But `tftest` needs to be able to find the source code.
So, we copy the source code to a temporary directory and then run the tests from there.
This feels like a hack but I haven't seen better guidance anywhere.
`.terraform` folder is 400+MB. I can cache plugins but not the modules (downloaded each time). So these are symlinked in to save
time and bandwidth.

`try/except` wraps the tf.plan beause I wanted to use pytest-xdist to parallelize. Multiprocessing massively slows down small volumes 
(see: https://github.com/pytest-dev/pytest-xdist/issues/346 and https://stackoverflow.com/questions/42288175/why-does-pytest-xdist-make-my-tests-run-slower-not-faster)
Keeping the hooks in for now but DONT use them until there is more critical mass.

Rewritten the call to the python function to use path.module, so the fixtures below can specifically target that connection_strings module alone versus whole project.
Saves about 20 seconds per testing cycle and pattern is scaleable in situations where full project plannning is required.

NOTE: 
1) DONT cleanup on exist or you'll crush the symlinked .terraform folder and have to reinstall in actual project.
2) Targeting module only seems to produce no output. Stick with full plan.
  e.g `return tf.plan(output=True, targets=["module.connection_strings"])` vs `return tf.plan(output=True, targets=["aws_instance.ec2"])`
"""

# def create_symlinked_folder(source_dir, target_dir):
#     """
#     Usage example:
#     create_symlinked_folder('/path/to/source', '/path/to/target')
#     """
#     source_path = Path(source_dir).resolve()
#     target_path = Path(target_dir).resolve()

#     # Create target directory if it doesn't exist
#     target_path.mkdir(parents=True, exist_ok=True)

#     # Create symlinks for all items in source
#     for item in source_path.iterdir():
#         link_path = target_path / item.name
#         if not link_path.exists():
#             os.symlink(item, link_path)


def create_copied_folder(source_dir, target_dir):
    source_path = Path(source_dir).resolve()
    target_path = Path(target_dir).resolve()

    # Create target directory if it doesn't exist
    target_path.mkdir(parents=True, exist_ok=True)
    # print(f"Scratch: {target_dir}")

    # Create physical copies for all items in source
    for item in source_path.iterdir():
        # Dont copy .git or terraform.tfvars
        # print(f"Item: {str(item)}")
        if any(substring in str(item) for substring in [".git", "terraform.tfvars"]):
            # print(f"\nFound not-to-be-copied file: {str(item)}")
            continue
        elif ".terraform" in str(item):
            # print(f"Found .terraform {item}")
            link_path = target_path / item.name
            if not link_path.exists():
                os.symlink(item, link_path)
        else:
            dest_path = target_path / item.name
            if not dest_path.exists():
                if item.is_dir():
                    shutil.copytree(item, dest_path)
                else:
                    shutil.copy2(item, dest_path)


def cleanup_folder(scratch):
    # Suppress warnings about not finding the auto-unlinked extra_files
    warnings.filterwarnings("ignore", category=pytest.PytestUnraisableExceptionWarning)
    shutil.rmtree(str(scratch))


@pytest.fixture(scope="session")
def plan_new_db(tmpdir_factory, datafiles_folder):
    # Generate string representation and build symlinks.
    scratch = tmpdir_factory.mktemp("newdb")
    create_copied_folder(root, scratch)
    # print(f"Scratch: {scratch}")

    tf = tftest.TerraformTest(tfdir=f"{scratch}/modules/connection_strings/v1.0.0")

    # Copy test configurations to fixtures directory
    tf.setup(
        extra_files=[
            f"{datafiles_folder}/terraform.tfvars",
            f"{datafiles_folder}/external_db_new.auto.tfvars",
        ],
        cleanup_on_exit=False,  # Dont trash .terraform and terraform.tfstate
    )
    yield tf.plan(output=True)

    # Clean up folder
    cleanup_folder(scratch)


@pytest.fixture(scope="session")
def plan_existing_db(tmpdir_factory, datafiles_folder):
    # Copy original files and symlinks.
    scratch = tmpdir_factory.mktemp("existingdb")
    create_copied_folder(root, scratch)
    # print(f"Scratch: {scratch}")

    # Tftest
    tf = tftest.TerraformTest(
        tfdir=f"{scratch}"
    )  # /modules/connection_strings/v1.0.0")

    # Copy test configurations to fixtures directory
    tf.setup(
        extra_files=[
            f"{datafiles_folder}/terraform.tfvars",
            f"{datafiles_folder}/external_db_existing.auto.tfvars",
        ],
        cleanup_on_exit=False,  # Dont trash .terraform and terraform.tfstate
    )
    yield tf.plan(output=True)

    # Clean up folder
    cleanup_folder(scratch)


@pytest.fixture(scope="session")
def plan_new_redis(tmpdir_factory, datafiles_folder):
    # Copy original files and symlinks.
    scratch = tmpdir_factory.mktemp("newredis")
    create_copied_folder(root, scratch)
    # print(f"Scratch: {scratch}")

    # Tftest
    tf = tftest.TerraformTest(
        tfdir=f"{scratch}"
    )  # /modules/connection_strings/v1.0.0")

    # Copy test configurations to fixtures directory
    tf.setup(
        extra_files=[
            f"{datafiles_folder}/terraform.tfvars",
            f"{datafiles_folder}/external_redis_new.auto.tfvars",
        ],
        cleanup_on_exit=False,  # Dont trash .terraform and terraform.tfstate
    )
    # return tf.plan(output=True, targets=["module.connection_strings"])  # BREAKS THING
    yield tf.plan(output=True)

    # Clean up folder
    cleanup_folder(scratch)
