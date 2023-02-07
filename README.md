# github-actions-docs

Github Action to generate github-actions docs for a composite action.

<!-- BEGIN_ACTION_DOCS -->

<!-- END_ACTION_DOCS -->

# Local development

To develop locally, install requirements and create a .env file in the directory root with the following contents:

```
pip3 install -r requirements.txt
```

.env:
```
ACTION_FILE_NAME="./example/action.yaml"
OUTPUT_FILE_NAME="./example/README.md"
OUTPUT_MODE="update"
```