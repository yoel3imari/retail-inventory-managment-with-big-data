from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="retail-inventory-management",
    version="1.0.0",
    author="Retail Inventory Team",
    author_email="team@retail-inventory.com",
    description="Big Data Retail Inventory Management System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yoel3imari/retail-inventory-management",
    packages=find_packages(include=["src", "src.*"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "spark": [
            "pyspark>=3.4.0",
        ],
        "ml": [
            "scikit-learn>=1.0.0",
            "joblib>=1.1.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "retail-data-generator=scripts.data_generator:main",
            "retail-sample-data=scripts.create_sample_data:main",
            "retail-bootstrap=scripts.bootstrap:main",
        ],
    },
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
)