# github-actions-docs

Github Action to generate github-actions docs for a composite action.

# Usage

Before using the action, if you are using `update` OUTPUT_MODE (To inject generated docs into an existing markdown file), ensure you add the following (uncommented) comments blocks to your markdown files to replace.

```
# <!-- BEGIN_ACTION_DOCS -->
# <!-- END_ACTION_DOCS -->
```

<!-- BEGIN_ACTION_DOCS -->

# github-actions-docs
Generate GitHub action docs for action

# inputs
| Title | Required | Type | Default| Description |
|-----|-----|-----|-----|-----|
| ACTION_FILE_NAME | True | string | `action.yaml` | The name of the file to be processed |
| OUTPUT_FILE_NAME | True | string | `README.md` | The file that the output report will be written to |
| OUTPUT_MODE | True | string | `update` | The output mode, [update/overwrite]. Update will be inserted after a line containing `<!-- BEGIN_ACTION_DOCS -->`, overwrite will overwrite the whole file |
<!-- END_ACTION_DOCS -->

# Permissions

This action requires the following permissions:

```
permissions:
  contents: write
```
# Workflow Usage

## Basic usage
```yaml
jobs:
  action-docs:
    runs-on: default
    steps:
    - uses: actions/checkout@v4
    - name: Setup Python
      uses: actions/setup-python@v5
    - name: github-actions-docs
      uses: tjtharrison/github-actions-docs@1.2.0
```

## Documenting nested actions

```yaml
jobs:
  action-docs:
    strategy:
      max-parallel: 1 # required, otherwise it will fail to lock ref on auto-commit
      matrix:
        paths:
          - ".", 
          - ".github/actions/nested-action-1", 
          - ".github/actions/nested-action-2"

    runs-on: default
    steps:
    - uses: actions/checkout@v4

    - name: Setup Python
      uses: actions/setup-python@v5

    - name: github-actions-docs
      uses: tjtharrison/github-actions-docs@1.2.0
      with:
        ACTION_FILE_NAME: ${{ matrix.paths }}/action.yml
        OUTPUT_FILE_NAME: ${{ matrix.paths }}/README.md
```

# Using YAML multiline strings and pipes

If you're using pipes or multiline strings in your YAML inputs, check below a documentation-friendly example:

```yaml
MY_INPUT:
    description: >-
      Use a folded block scalar with chomping indicator (i.e. `>-`) when defining your multiline YAML.<br>
      Also use HTML breaking spaces as you can see at the end of each line here.<br>
      Whenever you have a pipe, please escape it with a backslash: (e.g:)`<this\|that>`.
    required: false
    default: "my_input"
```

# Local development

To develop locally, install requirements to ensure the .env file is used in the project root:

```
pip3 install -r requirements.txt
```
