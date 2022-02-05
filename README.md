# Crawler for the Ticker

## Basic setup

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

Run tests with
```
python -m pytest
```

Tests and the tickergadse module should pass flake8 tests as defined in ``setup.cfg``.

```
flake8 tickergadse tests
```

The tickergadse module should also pass mypy checks.
```
mypy tickergadse
```


## Building Docker image

Build the image with the following command:

```
docker build -t tickergadse .
```
