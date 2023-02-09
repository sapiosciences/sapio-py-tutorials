
# sapiopylib: Official Sapio Informatics Platform Python API

<div align="center">
  <img src="https://www.sapiosciences.com/css/images/sapio-sciences-official-python-api-library.png" alt="logo"><br>
</div>

-----------------
[![PyPI Latest Release](https://img.shields.io/pypi/v/sapiopylib.svg)](https://pypi.org/project/sapiopylib/) [![License](https://img.shields.io/pypi/l/sapiopylib.svg)](https://github.com/sapiosciences/sapio-py-tutorials/blob/master/LICENSE) [![Issues](https://img.shields.io/github/issues/sapiosciences/sapio-py-tutorials)](https://github.com/sapiosciences/sapio-py-tutorials/issues)

## What is it?
sapiopylib is a powerful Python package, developed and maintained by Sapio Sciences, that provides the ability to create endpoints to manipulate data and make configuration changes within the Sapio LIMS system in a quick and straightforward manner.

The package makes it easy to automate changes to and queries of different types of data in the system, ranging from records to notebooks and the entries within them. Intuitive datatypes, such as record models that allow for simple manipulation of data records and their fields, within the package help to make development nearly as straightforward as performing the same tasks in the application.

As well as serving as the most direct way to programmatically alter data in the application, sapiopylib makes it possible to create endpoints to alter and query configurations in the system. Configurations for system data types, lists used by the system, and more can be easily accessed using this package.

## Main Features
Here is a list of major features in this library:
- Support all Sapio REST API functions.
- Manipulate data records with record models using client-based caching. This allows you to batch requests easily for performance. Making your changes in mini-batch is also provides transactional commits outside of a webhook context for data record changes.
- Create new temporary data types easily with FormBuilder utility.
- Provides Protocol-Step API as we have defined in Sapio Java API.
- Supports creation of a Flask-based webhook server. Implement additional toolbar buttons, rules, validation logic to customize your ELN experiment, workflows, and user interface.

## Where to get it?
Installation is simple:
```sh
pip install sapiopylib
```
However, you may need to pay attention to the library version to ensure it is compatible with your Sapio Informatics Platform.
The correct versions for each platform can be found under the tutorial github. The github will create a branch under 'prior_releases' folder when a specific sapiopylib is made against a platform release. The installation manual inside the tutorial, with the correct branch checked out, will make a reference to the exact version you should install for that platform.
The most recent release may contain REST calls that will require a bleeding edge version of Sapio Platform that has not yet reached GA status.

## Licenses
sapiopylib along with its tutorials in the github are licensed under MPL 2.0.
pypi.org is granted the right to distribute sapiopylib forever.

This license does not provide any rights to use any other copyrighted artifacts from Sapio Sciences. (And they are typically written in another programming language with no linkages to this library.)

## Dependencies
The following dependencies are required for this package:
- [requests - Requests is an Apache2 Licensed HTTP library, written in Python, for human beings.](https://pypi.org/project/requests/2.7.0/)
- [pandas - pandasis a fast, powerful, flexible and easy to use open source data analysis and manipulation tool,  
  built on top of the Python programming language.](https://pandas.pydata.org/)
- [Flask - A simple framework for building complex web applications.](https://pypi.org/project/Flask/)
- [buslane - A simple implementation of event-bus system with proper type hinting](https://pypi.org/project/buslane/)

## Documentation
All documentations, including code examples and installation guide, are provided at [our sapiopylib tutorial github](https://github.com/sapiosciences/sapio-py-tutorials).

## Getting Help
If you have support contract with Sapio Sciences, please use our technical support channels. support@sapiosciences.com

If you have any questions about how to use sapiopylib, please visit our tutorial page.

If you would like to report an issue on sapiopylib, or its tutorial content, please feel free to create a issue ticket at the tutorial github.

## About Us
Sapio is at the forefront of the Digital Lab with its science-aware platform for managing all your life science data with its integrated Electronic Lab Notebook, LIMS Software and Scientific Data Management System.

Visit us at https://www.sapiosciences.com/