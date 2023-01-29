import setuptools

with open("README.md") as fh:
    long_description = fh.read()

setuptools.setup(
    name="Paralleltask",
    version="0.2.1",
    author="Hu Jiang",
    author_email="mooldhu@gmail.com",
    description="A simple and lightweight parallel task engine",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/moold/ParallelTask",
    license="GPLv3",
    packages=setuptools.find_packages("src"),
    package_dir = {"": "src"},
    zip_safe=False,
    package_data={
        "":["cluster.cfg"]
    },
    install_requires=["psutil"],
    classifiers=[
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
    entry_points={
        'console_scripts': [
            'paralleltask=paralleltask.__main__:main',
        ],
    }
)
