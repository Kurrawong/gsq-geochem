import sys
from pathlib import Path


profile_home = Path(__file__).parent.parent.resolve()

sys.path.append(str(profile_home / "scripts"))

from profiles.gsq.scripts.validate import convert_and_validate

for eg in Path(profile_home / "examples").glob("eg-*"):
    print(f"validating {eg}")
    print(convert_and_validate(eg))
