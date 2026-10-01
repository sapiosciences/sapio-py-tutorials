# Sapio Default Webhook Project
This folder contains the code that should be used as the basis for all new Python webhook projects for Sapio. Copy
this folder to a new location (it does not need to stay inside this tutorial repository) and start building from there.

The necessary files have been provided to build this project into a Docker image, which can then be deployed to the
service of your choice.

The server.py file is where all new webhook endpoints should be registered. If you run this
file within your IDE, then you will be running a local server that you can use to test your
changes.

### Library Versions
Whenever you are starting a new project, or if your Sapio system is being upgraded, make sure that the sapiopylib and
sapiopycommons versions in the requirements.txt file match the compatible versions with your Sapio system. Since
sapiopycommons depends on sapiopylib, the sapiopycommons version is the one that matters most. For example, a 26.8
system should use sapiopycommons 38.0.1.26.8. See the [root README](../../README.md) for details on the difference
between the two libraries and how versioning works.

* https://pypi.org/project/sapiopylib
* https://pypi.org/project/sapiopycommons

### Record Models
If your webhooks use Python record models, generate the record model file from your own system (App Setup ->
Manage Rules & Webhooks -> Webservice API -> "Generate Python Record Model Wrappers for System Data Types") so that
it contains your system's exact data types and fields. See [tutorial 10](../../10_python_record_models.ipynb) for details.

### Next Steps
The [exercise_project](../exercise_project) project contains a series of examples and exercises that teach the
fundamentals of writing webhooks with these libraries.
