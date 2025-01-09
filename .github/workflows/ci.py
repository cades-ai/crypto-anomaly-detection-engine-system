name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.9', '3.10', '3.11']  # Updated Python versions

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
        cache: 'pip'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt

    - name: Run linting
      run: |
        pip install flake8 black isort
        flake8 . --count --show-source --statistics
        black . --check
        isort . --check-only

    - name: Run tests with coverage
      run: |
        pip install pytest pytest-cov
        pytest tests/ --cov=src/ --cov-report=xml

  build:
    needs: [test]
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3

    - name: Set up Docker Buildx
      uses: docker/setup-buildx-action@v2

    - name: Build Docker image
      uses: docker/build-push-action@v4
      with:
        context: .
        file: docker/Dockerfile  # Updated path
        push: false
        tags: cade:test
        cache-from: type=gha
        cache-to: type=gha,mode=max