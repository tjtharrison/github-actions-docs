"""Process provided mode and verify against accepted modes."""

import sys


def main(args):
    """
    Process provided mode and verify against accepted modes.

    Args:
        args: List of arguments provided to the script

    Returns:
        True if mode is valid, exits with error code 1 if not
    """
    accepted_modes = ["update", "overwrite"]

    if len(args) < 2:
        print("Requires input")
    else:
        if sys.argv[1] not in accepted_modes:
            print(
                "Provided value " + str(sys.argv[1]) + " not in " + str(accepted_modes)
            )
            sys.exit(1)
        else:
            print(sys.argv[1] + " mode set")

    return True


if __name__ == "__main__":
    main(sys.argv)
