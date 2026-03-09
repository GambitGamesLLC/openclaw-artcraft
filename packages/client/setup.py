from setuptools import setup, find_packages

setup(
    name="openclaw-artcraft",
    version="0.2.0",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[],
    extras_require={
        "dev": ["pytest", "pytest-asyncio", "mypy"]
    },
    entry_points={
        "console_scripts": [
            "openclaw-artcraft=artcraft_client.client:main",
        ],
    },
    author="Derrick",
    description="Python client for OpenClaw ArtCraft AI generation CLI",
    long_description=open("README.md").read() if __import__("pathlib").Path("README.md").exists() else "",
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
