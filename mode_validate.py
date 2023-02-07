import sys

accepted_modes = ["update","overwrite"]

if len(sys.argv) < 2:
    print("Requires input")
else:
    if sys.argv[1] not in accepted_modes:
        print("Provided value " + str(sys.argv[1]) + " not in " + str(accepted_modes))
        sys.exit(1)
    else:
        print(sys.argv[1] + " mode set")