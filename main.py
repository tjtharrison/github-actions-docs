import yaml
import sys
import os

try:
    if len(os.environ.get("RUNNER_OS")) > 0:
        print("Running on Github Runner")
except Exception as error_message:
    print("Not running on Github runner")
    from dotenv import load_dotenv
    load_dotenv()

def main():
    with open(os.environ.get("ACTION_FILE_NAME"), "r") as stream:
        print("Loading " + os.environ.get("ACTION_FILE_NAME"))
        try:
            action_contents = yaml.safe_load(stream)
        except yaml.YAMLError as error_message:
            print(error_message)
            sys.exit(1)

    output_list = []

    print("Writing action title")
    output_list.append("# " + action_contents["name"])
    output_list.append(action_contents["description"])

    try:
        if len(action_contents["inputs"]) > 0:
            print("Processing action inputs")
            output_list.append("# inputs")
            output_list.append("| Title | Required | Type | Description |")
            output_list.append("|-----|-----|-----|-----|")
            for input in action_contents["inputs"]:
                try:
                    input_type = action_contents["inputs"][input]["type"]
                except KeyError:
                    input_type = ""

                try:
                    input_description = action_contents["inputs"][input]["description"]
                except KeyError:
                    input_description = ""

                output_list.append(
                    "| "
                    + input
                    +  " | "
                    + str(action_contents["inputs"][input]["required"])
                    + " | "
                    + str(input_type)
                    + " |"
                    + str(input_description)
                    + " |"
                )
    except KeyError:
        print("No inputs provided")

    try:
        if len(action_contents["outputs"]) > 0:
            print("Processing action outputs")
            output_list.append("# outputs")
            output_list.append("| Title | Description | Value |")
            output_list.append("|-----|-----|-----|")
            for output in action_contents["outputs"]:
                try:
                    output_description = action_contents["outputs"][output]["description"]
                except KeyError:
                    output_description = ""

                output_list.append(
                    "|"
                    + output
                    + " | "
                    + output_description
                    + " | "
                    + " `" + action_contents["outputs"][output]["value"] + "`"
                    + " | "
                )
    except KeyError:
        print("No outputs provided")

    # Handle modes
    print("Writing output")
    with open(os.environ.get("OUTPUT_FILE_NAME"), "r", encoding="UTF-8") as original_file:
        print("Original file read")
        original_file_contents = original_file.readlines()
    with open(os.environ.get("OUTPUT_FILE_NAME"), "w", encoding="UTF-8") as markdown_output_file:
        print("Output file opened")

        if os.environ.get("OUTPUT_MODE") == "update":
            print("Update mode detected, updating original file")
            print("Looking for required BEGIN/END lines")
            found_start = False
            found_end = False

            for source_line in original_file_contents:
                if source_line.startswith("<!-- BEGIN_ACTION_DOCS -->"):
                    found_start = True
                elif source_line.startswith("<!-- END_ACTION_DOCS -->"):
                    found_end = True

            if found_start and found_end:
                print("Deleting between BEGIN/END lines")
                temp_original_file_contents = []
                do_write = True
                for source_line in original_file_contents:
                    if source_line.startswith("<!-- BEGIN_ACTION_DOCS -->"):
                        print("Start found, deleting")
                        temp_original_file_contents.append(source_line)
                        do_write = False
                    elif source_line.startswith("<!-- END_ACTION_DOCS -->"):
                        print("End found, continuing write")
                        temp_original_file_contents.append(source_line)
                        do_write = True
                    elif do_write == True:
                        temp_original_file_contents.append(source_line)
            else:
                print("Required BEGIN/END lines not detected, please see documentation")
                sys.exit(1)

            original_file_contents = list.copy(temp_original_file_contents)

            for line in original_file_contents:
                markdown_output_file.write(line)
                if line.startswith("<!-- BEGIN_ACTION_DOCS -->"):
                    print("BEGIN_ACTION_DOCS detected, writing action-docs")
                    for output_item in output_list:
                        if output_item.startswith("#"):
                            print("")
                            markdown_output_file.write("\n")
                        print(output_item)
                        markdown_output_file.write(output_item)
                        if output_item.startswith("#"):
                            print("")
                            markdown_output_file.write("\n")
                        markdown_output_file.write("\n")
        elif os.environ.get("OUTPUT_MODE") == "overwrite":
            for output_item in output_list:
                if output_item.startswith("#"):
                    print("")
                    markdown_output_file.write("\n")
                print(output_item)
                markdown_output_file.write(output_item)
                if output_item.startswith("#"):
                    print("")
                    markdown_output_file.write("\n")
                markdown_output_file.write("\n")


if __name__ == "__main__":
    main()
