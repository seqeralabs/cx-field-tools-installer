import json
import os
import subprocess


def test_input():
    """Emulate TF calling external data. Invoke function and pass data via stdin."""

    # Get current POSIX path and calculate POSIX location of target script.
    current_filepath = os.path.dirname(os.path.realpath(__file__))
    target_script = (
        f"{current_filepath}/../installer/data_external/example_get_payload_from_tf.py"
    )

    INPUT = '{"a": "b"}'

    # Must encode to avoid: `TypeError: memoryview: a bytes-like object is required, not 'str'` error
    res = subprocess.run(
        [target_script],
        input=INPUT.encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Convert byte string to useable JSON
    print(res)
    print(json.loads(res.stdout.decode("utf-8")))

    json_res = json.loads(res.stdout.decode("utf-8"))
    assert json_res == {"status": "0", "value": f"{INPUT}"}
