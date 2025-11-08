"""Setup script for gate_controller."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith('#')]

setup(
    name="gate_controller",
    version="0.1.0",
    author="Alex Fok",
    description="Automated gate control system with BLE token detection and Control4 integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alexfok/gate_controller",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Home Automation",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "gate-controller=gate_controller.__main__:main",
            "gate-cli=gate_controller.cli:main",
        ],
    },
)

