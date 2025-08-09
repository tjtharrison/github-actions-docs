
# github-actions-cleanup-action-cache
GitHub action to cleanup actions cache from a repository

# inputs
| Title | Required | Type | Default| Description |
|-----|-----|-----|-----|-----|
| DRY_RUN | False | string | `true` | Whether to run the action in dry-run mode <true|false> |
| CACHE_KEY | False | string |  | The specific cache key to delete |
| GIT_REF | False | string |  | The git ref to delete the cache for |
| GITHUB_TOKEN | True | string |  | The GitHub token to use for the API requests |

# outputs
| Title | Description | Value |
|-----|-----|-----|
|CACHE_DELETED | Indicates whether the cache was deleted successfully |  `true` | 
