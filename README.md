# Crawler for the Ticker

## Building Docker image

For write-access to repositories on Github, a personal access token is required.
Build the image with the following command:

```
docker build \
    --build-arg github_name=<name> \
    --build-arg github_email=<email> \
    --build-arg github_token=<token> \
    -t tickergadse .
```

## Setup Github Actions

The crawler action requires a [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) to push to the data repository.
Set or update the `REPO_TOKEN` secret in the repository settings.
