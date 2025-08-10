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
                    input_default = action_contents["inputs"][action_input]["default"]
                except KeyError:
                    input_default = ""

                try:
                    input_description = action_contents["inputs"][action_input][
                        "description"
                    ]
                except KeyError:
                    input_description = ""

                try:
                    input_required = action_contents["inputs"][action_input]["required"]
                except KeyError:
                    input_required = "False"

                output_list.append(
                    "| "
                    + action_input
                    + " | "
                    + str(input_required)
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


def find_action_docs_markers(file_contents):
    """
    Find BEGIN and END action docs markers in file contents.

    Args:
        file_contents: List of lines from the file

    Returns:
        tuple: (found_start, found_end) boolean tuple
    """
    found_start = False
    found_end = False

    for line in file_contents:
        if line.startswith("<!-- BEGIN_ACTION_DOCS -->"):
            found_start = True
        elif line.startswith("<!-- END_ACTION_DOCS -->"):
            found_end = True

    return found_start, found_end


def remove_content_between_markers(file_contents):
    """
    Remove content between BEGIN and END action docs markers.

    Args:
        file_contents: List of lines from the file

    Returns:
        list: File contents with content between markers removed
    """
    result = []
    include_line = True

    for line in file_contents:
        if line.startswith("<!-- BEGIN_ACTION_DOCS -->"):
            logging.info("Start found, deleting")
            result.append(line)
            include_line = False
        elif line.startswith("<!-- END_ACTION_DOCS -->"):
            logging.info("End found, continuing write")
            result.append(line)
            include_line = True
        elif include_line:
            result.append(line)

    return result


def write_action_docs_content(file_handle, output_list):
    """
    Write action documentation content to file handle.

    Args:
        file_handle: Open file handle for writing
        output_list: List of documentation lines to write
    """
    for output_item in output_list:
        if output_item.startswith("#"):
            file_handle.write("\n")
        logging.info(output_item)
        file_handle.write(output_item)
        file_handle.write("\n")


def write_output_file_update_mode(output_file_name, original_contents, output_list):
    """
    Write output file in update mode, preserving existing content.

    Args:
        output_file_name: Path to output file
        original_contents: Original file contents as list of lines
        output_list: Documentation content to insert
    """
    found_start, found_end = find_action_docs_markers(original_contents)

    if not (found_start and found_end):
        logging.info("Required BEGIN/END lines not detected, please see documentation")
        sys.exit(1)

    logging.info("Deleting between BEGIN/END lines")
    cleaned_contents = remove_content_between_markers(original_contents)

    with open(output_file_name, "w", encoding="UTF-8") as markdown_output_file:
        logging.info("Output file opened")

        for line in cleaned_contents:
            markdown_output_file.write(line)
            if line.startswith("<!-- BEGIN_ACTION_DOCS -->"):
                logging.info("BEGIN_ACTION_DOCS detected, writing action-docs")
                write_action_docs_content(markdown_output_file, output_list)


def write_output_file_overwrite_mode(output_file_name, output_list):
    """
    Write output file in overwrite mode, replacing entire content.

    Args:
        output_file_name: Path to output file
        output_list: Documentation content to write
    """
    with open(output_file_name, "w", encoding="UTF-8") as markdown_output_file:
        logging.info("Output file opened")
        write_action_docs_content(markdown_output_file, output_list)


def read_original_file(output_file_name):
    """
    Read the original file contents.

    Args:
        output_file_name: Path to the file to read

    Returns:
        list: List of lines from the file

    Raises:
        FileNotFoundError: If the file doesn't exist
        IOError: If there's an error reading the file
    """
    try:
        with open(output_file_name, "r", encoding="UTF-8") as original_file:
            logging.info("Original file read")
            return original_file.readlines()
    except FileNotFoundError as error_message:
        logging.error("Output file not found: %s (%s)", output_file_name, error_message)
        raise
    except IOError as error_message:
        logging.error("Error reading output file: %s", error_message)
        raise


def generate_documentation_content(action_contents):
    """
    Generate complete documentation content from action contents.

    Args:
        action_contents: Parsed action YAML contents

    Returns:
        list: List of documentation lines
    """
    output_list = []

    logging.info("Writing action title")
    output_list.append("# " + action_contents["name"])
    output_list.append(action_contents["description"])

    # Process inputs
    try:
        output_list = process_action_inputs(action_contents, output_list)
    except KeyError:
        logging.info("No inputs provided")

    # Process outputs
    try:
        output_list = process_action_outputs(action_contents, output_list)
    except KeyError:
        logging.info("No outputs provided")

    return output_list


def write_documentation_file(output_file_name, output_mode, output_list):
    """
    Write documentation to output file based on specified mode.

    Args:
        output_file_name: Path to output file
        output_mode: Mode for writing ('update' or 'overwrite')
        output_list: Documentation content to write
    """
    logging.info("Writing output")

    if output_mode == "update":
        logging.info("Update mode detected, updating original file")
        logging.info("Looking for required BEGIN/END lines")
        original_contents = read_original_file(output_file_name)
        write_output_file_update_mode(output_file_name, original_contents, output_list)
    elif output_mode == "overwrite":
        write_output_file_overwrite_mode(output_file_name, output_list)
    else:
        logging.error("Unknown output mode: %s", output_mode)
        sys.exit(1)


def main():
    """
    Execute the script.

    Returns:
        True
    """
    # Load action file
    try:
        action_contents = open_action_file(os.environ.get("ACTION_FILE_NAME"))
    except yaml.YAMLError as yaml_error_message:
        logging.info("Some error occurred while opening the action file:")
        logging.info(str(yaml_error_message))
        sys.exit(1)
        # This line never executes in normal flow, but helps with tests
        return False  # pylint: disable=unreachable
    except FileNotFoundError as file_error_message:
        logging.info("Some error occurred while opening the action file:")
        logging.info(str(file_error_message))
        sys.exit(1)
        # This line never executes in normal flow, but helps with tests
        return False  # pylint: disable=unreachable

    # Generate documentation content
    output_list = generate_documentation_content(action_contents)

    # Write documentation to output file
    output_file_name = os.environ.get("OUTPUT_FILE_NAME")
    output_mode = os.environ.get("OUTPUT_MODE")

    try:
        write_documentation_file(output_file_name, output_mode, output_list)
    except (FileNotFoundError, IOError) as file_error:
        logging.error("Error writing documentation file: %s", file_error)
        sys.exit(1)
        # This line never executes in normal flow, but helps with tests
        return False  # pylint: disable=unreachable

    return True


if __name__ == "__main__":
    main()
