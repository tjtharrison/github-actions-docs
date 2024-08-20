"""Generate action docs."""

import logging
import os
import sys

import yaml

# Configure logging
logging.basicConfig(
    format=(
        "{"
        '"time":"%(asctime)s",'
        ' "name": "%(name)s",'
        ' "level": "%(levelname)s",'
        ' "message": "%(message)s"'
        "}"
    ),
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)

try:
    if len(os.environ.get("RUNNER_OS")) > 0:
        logging.info("Running on Github Runner")
except Exception as error_message:
    logging.info("Not running on Github runner")
    from dotenv import load_dotenv

    load_dotenv()


def open_action_file(action_file):
    """
    Open the action file and return the contents.

    Args:
        action_file: Name of the action file

    Raises:
        YAMLError: If there is an issue with the action file
        FileNotFoundError: If the action file is not found

    Returns:
        action_file_contents: Contents of the action file
    """
    try:
        with open(action_file, "r", encoding="UTF-8") as stream:
            logging.info("Loading %s", os.environ.get("ACTION_FILE_NAME"))
            action_contents = yaml.safe_load(stream)
    except FileNotFoundError as file_error_message:
        logging.info(file_error_message)
        raise FileNotFoundError from file_error_message
    except yaml.YAMLError as yaml_error_message:
        logging.info(yaml_error_message)
        raise yaml.YAMLError from yaml_error_message

    return action_contents


def process_action_inputs(action_contents, output_list):
    """
    Process action inputs.

    Args:
        action_contents: Contents of the action file.
        output_list: Current contents of action docs.

    Returns:
        output_list: Updated contents of action docs.
    """
    try:
        if len(action_contents["inputs"]) > 0:
            logging.info("Processing action inputs")
            output_list.append("# inputs")
            output_list.append("| Title | Required | Type | Default| Description |")
            output_list.append("|-----|-----|-----|-----|-----|")
            for action_input in action_contents["inputs"]:
                try:
                    input_type = action_contents["inputs"][action_input]["type"]
                except KeyError:
                    input_type = ""

                try:
                    input_default = action_contents["inputs"][action_input][
                        "default"
                    ]
                except KeyError:
                    input_default = ""

                try:
                    input_description = action_contents["inputs"][action_input][
                        "description"
                    ]
                except KeyError:
                    input_description = ""

                output_list.append(
                    "| "
                    + action_input
                    + " | "
                    + str(action_contents["inputs"][action_input]["required"])
                    + " | "
                    + str(input_type)
                    + " | "
                    + ("`" + str(input_default) + "`" if input_default else "")
                    + " | "
                    + str(input_description)
                    + " |"
                )
    except KeyError:
        logging.info("No inputs provided")

    return output_list


def process_action_outputs(action_contents, output_list):
    """
    Process action outputs.

    Args:
        action_contents: Contents of the action file.
        output_list: Current contents of action docs.

    Returns:
        output_list: Updated contents of action docs.
    """
    try:
        if len(action_contents["outputs"]) > 0:
            logging.info("Processing action outputs")
            output_list.append("# outputs")
            output_list.append("| Title | Description | Value |")
            output_list.append("|-----|-----|-----|")
            for output in action_contents["outputs"]:
                try:
                    output_description = action_contents["outputs"][output][
                        "description"
                    ]
                except KeyError:
                    output_description = ""

                output_list.append(
                    "|"
                    + output
                    + " | "
                    + output_description
                    + " | "
                    + " `"
                    + action_contents["outputs"][output]["value"]
                    + "`"
                    + " | "
                )
    except KeyError:
        logging.info("No outputs provided")

    return output_list

def main():
    """
    Execute the script.

    Returns:
        True
    """
    try:
        action_contents = open_action_file(os.environ.get("ACTION_FILE_NAME"))
    except yaml.YAMLError as yaml_error_message:
        logging.info("Some error occurred while opening the action file:")
        logging.info(str(yaml_error_message))
        sys.exit(1)
    except FileNotFoundError as file_error_message:
        logging.info("Some error occurred while opening the action file:")
        logging.info(str(file_error_message))
        sys.exit(1)

    output_list = []

    logging.info("Writing action title")
    output_list.append("# " + action_contents["name"])
    output_list.append(action_contents["description"])

    # Handle inputs
    try:
        input_list = process_action_inputs(action_contents, output_list)
        print(input_list)
    except KeyError:
        logging.info("No inputs provided")

    # Handle outputs
    try:
        output_list = process_action_outputs(action_contents, output_list)
    except KeyError:
        logging.info("No outputs provided")

    # Handle modes
    logging.info("Writing output")
    with open(
        os.environ.get("OUTPUT_FILE_NAME"), "r", encoding="UTF-8"
    ) as original_file:
        logging.info("Original file read")
        original_file_contents = original_file.readlines()
    with open(
        os.environ.get("OUTPUT_FILE_NAME"), "w", encoding="UTF-8"
    ) as markdown_output_file:
        logging.info("Output file opened")

        if os.environ.get("OUTPUT_MODE") == "update":
            logging.info("Update mode detected, updating original file")
            logging.info("Looking for required BEGIN/END lines")
            found_start = False
            found_end = False

            for source_line in original_file_contents:
                if source_line.startswith("<!-- BEGIN_ACTION_DOCS -->"):
                    found_start = True
                elif source_line.startswith("<!-- END_ACTION_DOCS -->"):
                    found_end = True

            if found_start and found_end:
                logging.info("Deleting between BEGIN/END lines")
                temp_original_file_contents = []
                do_write = True
                for source_line in original_file_contents:
                    if source_line.startswith("<!-- BEGIN_ACTION_DOCS -->"):
                        logging.info("Start found, deleting")
                        temp_original_file_contents.append(source_line)
                        do_write = False
                    elif source_line.startswith("<!-- END_ACTION_DOCS -->"):
                        logging.info("End found, continuing write")
                        temp_original_file_contents.append(source_line)
                        do_write = True
                    elif do_write is True:
                        temp_original_file_contents.append(source_line)
            else:
                logging.info(
                    "Required BEGIN/END lines not detected, please see documentation"
                )
                sys.exit(1)

            original_file_contents = list.copy(temp_original_file_contents)

            for line in original_file_contents:
                markdown_output_file.write(line)
                if line.startswith("<!-- BEGIN_ACTION_DOCS -->"):
                    logging.info("BEGIN_ACTION_DOCS detected, writing action-docs")
                    for output_item in output_list:
                        if output_item.startswith("#"):
                            logging.info("")
                            markdown_output_file.write("\n")
                        logging.info(output_item)
                        markdown_output_file.write(output_item)
                        markdown_output_file.write("\n")

        elif os.environ.get("OUTPUT_MODE") == "overwrite":
            for output_item in output_list:
                if output_item.startswith("#"):
                    logging.info("")
                    markdown_output_file.write("\n")
                logging.info(output_item)
                markdown_output_file.write(output_item)
                markdown_output_file.write("\n")

    return True


if __name__ == "__main__":
    main()
