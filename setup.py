from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="seo_automation",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An automated SEO analysis tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/seo_automation",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Marketing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires='>=3.8',
    install_requires=[
        "requests==2.31.0",
        "beautifulsoup4==4.12.2",
        "lxml==4.9.3",
        "nltk==3.8.1",
        "pandas==2.0.3",
        "matplotlib==3.7.2",
        "scikit-learn",
        "jinja2==3.1.2",
        "pdfkit==1.0.0",
        "click==8.1.3",
        "validators==0.22.0",
        "python-dotenv==1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "seo-automation=seo_automation.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "seo_automation": ["templates/*"],
    },
)