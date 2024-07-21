def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    pass


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    # https://stackoverflow.com/questions/27844088/python-get-directory-two-levels-up
    # Assumes following path: .. > installer > tests > conftest.py
    # import sys
    # from pathlib import Path

    # grandparent_dir = Path(__file__).resolve().parents[2]
    # sys.path.append(str(grandparent_dir))
    pass


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """
    pass


def pytest_unconfigure(config):
    """
    Called before test process is exited.
    """
    pass
