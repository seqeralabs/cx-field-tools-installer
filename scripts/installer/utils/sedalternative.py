# This script used as an alternative to `sed` given differences between GNU and Darwin sed syntax.
import sys

if len(sys.argv) != 4:
    print("Usage: python example.py <wave-lite-limited-user> <wave-lite-limited-password> <file_root>")
    sys.exit(1)

# placeholder = sys.argv[1]
# replacement_value = sys.argv[2]
# sourcefile = sys.argv[3]
limited_user        = sys.argv[1]
limited_password    = sys.argv[2]
file_root         = sys.argv[3]

entries = [
    ("replace_me_wave_lite_db_limited_user", limited_user, f"{file_root}/wave-lite-rds.sql"),
    ("replace_me_wave_lite_db_limited_password", limited_password, f"{file_root}/wave-lite-rds.sql"),

]

for entry in entries:
    placeholder, replacement_value, sourcefile = entry

    # Read and replace contents
    with open(sourcefile, "r", encoding="utf-8") as file:
        content = file.read()
        content = content.replace(placeholder, replacement_value)

    with open(sourcefile, "w", encoding="utf-8") as file:
        file.write(content)
