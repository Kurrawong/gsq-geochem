import sys
from geochemxl.convert import main


if __name__ == "__main__":
    retval = main(sys.argv[1:])
    if retval is not None:
        sys.exit(retval)
