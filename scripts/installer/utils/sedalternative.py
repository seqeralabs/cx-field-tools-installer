# This script used as an alternative to `sed` given differences between GNU and Darwin sed syntax.
import sys

if len(sys.argv) != 4:
    print("Usage: python example.py <arg1> <arg2> <arg3>")
    sys.exit(1)

placeholder = sys.argv[1]
replacement_value = sys.argv[2]
sourcefile = sys.argv[3]

print(f"{placeholder=}")
print(f"{replacement_value=}")
print(f"{sourcefile=}")

# Read and replace contents
with open(sourcefile, "r", encoding="utf-8") as file:
    content = file.read()
    content = content.replace(placeholder, replacement_value)

with open(sourcefile, "w", encoding="utf-8") as file:
    file.write(content)
