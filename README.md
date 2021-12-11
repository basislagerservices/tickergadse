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
