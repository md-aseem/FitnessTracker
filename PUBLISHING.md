# Publishing to Artifactory

Follow these steps to build and release a new version of the `quantum_thermal_model`.

## 1. Prerequisites
Ensure your virtual environment is active:
```bash
source venv/bin/activate
pip install setuptools wheel twine
```

## 2. Build and Publish

1.  **Update Version**: Increment the `version` string in `setup.py` (e.g., `0.1.1`).
2.  **Clean previous builds**:
    ```bash
    rm -rf build/ dist/ *.egg-info
    ```
3.  **Build the package**:
    ```bash
    python3 setup.py sdist bdist_wheel
    ```
4.  **Upload to Artifactory**:
    ```bash
    python3 -m twine upload --config-file .pypirc -r gems-artifactory dist/*
    ```

## 3. Installation
To install the package in any project:
```bash
pip install quantum_thermal_model
```
