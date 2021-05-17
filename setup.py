from setuptools import setup
from setuptools.command.install import install


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):
        install.run(self)
        # Custom post-install commands could come here


def readme():
    with open("README.rst") as f:
        return f.read()


exec(open("resolos/version.py").read())
setup(
    name="resolos",
    version=__version__,
    description="Reproducible research made easy",
    long_description=readme(),
    url="https://github.com/nuvolos-cloud/resolos",
    author="Alphacruncher",
    author_email="support@nuvolos.cloud",
    license="MIT",
    packages=["resolos", "resolos.storage"],
    install_requires=[
        "click",
        "click-log",
        "pyyaml",
        "semver",
        "conda-pack",
        "requests",
        "pyjwt",
    ],
    zip_safe=False,
    entry_points="""
        [console_scripts]
        r3s=resolos.interface:res
    """,
    cmdclass={"install": PostInstallCommand},
    include_package_data=True,
    setup_requires=["pytest-runner"],
    tests_require=["pytest"],
)
