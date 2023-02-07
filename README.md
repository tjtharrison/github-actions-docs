
# github-actions-docs

Generate GitHub action docs for action

# inputs

| Title | Required | Type | Description |
|-----|-----|-----|-----|
| ACTION_FILE_NAME | True | string |The name of the file to be processed |
| OUTPUT_FILE_NAME | True | string |The file that the output report will be written to |
| OUTPUT_MODE | True | string |The output mode, [update/overwrite]. Update will be inserted after a line containing <!-- INSERT_ACTION_DOCS -->, overwrite will overwrite the whole file |
