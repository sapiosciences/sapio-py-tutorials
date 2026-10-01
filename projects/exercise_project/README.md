# Webhook Development Examples Project
This project contains a series of Sapio webhook examples that utilize our official Python libraries, sapiopylib and
sapiopycommons. The files in the examples folder are intended to be reviewed in alphabetical order. Once you have
reviewed the examples, try your hand at the exercises in the exercises folder.

Note that the example webhooks are designed to teach the fundamentals of using our Python libraries to write webhooks
for a Sapio system. This means that they are not necessarily designed as functional webhooks if you were to register
an endpoint for them and run them from within the system.

If you are starting a brand new webhook project of your own, copy the [default_project](../default_project) instead
of this one.

### Prerequisites
Install the following:
* [Python 3.13 or greater](https://www.python.org/downloads/release/python-31315/)
* The Python packages in requirements.txt
  * For sapiopylib and sapiopycommons, visit our PyPI pages (linked below) to ensure that you are grabbing the 
    latest compatible library versions for your Sapio system's version. sapiopycommons depends on sapiopylib, so
    installing sapiopycommons also installs sapiopylib. See the [root README](../../README.md) for details.

Sapio utilizes [PyCharm](https://www.jetbrains.com/pycharm/) as our Python IDE. Some comments will include tips that 
reference key shortcuts or behaviors in PyCharm. Behavior may be different if you are using another IDE.

### Record Models
The utilities/data_type_models.py file contains Python record model classes that were generated from a stock Sapio
system, so it only includes the data types that every system has. Your own system will have different data types and
custom fields, so you should generate the file from your own system and replace the provided one:

1. In the Sapio web client, click App Setup under your profile icon.
2. Select Manage Rules & Webhooks -> Webservice API from the left menu.
3. Click "Generate Python Record Model Wrappers for System Data Types". The file will be downloaded as
   data_type_models.py.

See [tutorial 10](../../10_python_record_models.ipynb) for more information on using record models.

### Running the Server
Run server.py from within this project's folder (projects/exercise_project), since it imports the
exercise modules relative to that folder.

### Testing Locally
Webhooks can be tested locally by spinning up a webhook server within your IDE. Run the server.py file to start a
webhook server on your localhost port defined by the "port" variable at the bottom of the file.
In order to have Sapio make requests to your defined webhook endpoints, you will need to make your localhost port
available to the Sapio server.

If your local machine is on a separate network, you will need to use a tunneling/port forwarding service to make your
webhooks available to the Sapio server. Sapio's developers currently utilize [ngrok](https://ngrok.com/) for this
purpose. Once installed, you can run `ngrok http 8090` from a terminal to start an ngrok instance. The final value in
the command is the port that the ngrok instance will make available, which should match the port in the server.py file.
Going to http://localhost:4040 in your browser while an ngrok instance is running will allow you to review the requests
that the Sapio server makes to your webhook server, including displaying the JSON of the requests. This can be a useful
tool for understanding what Sapio is sending for the context of a particular endpoint. 

If your local machine is on the same network as the Sapio server, contact your IT team about making your local device's
IP available to the Sapio server.

### Deploying Webhooks
This project contains a Dockerfile that can be used to build this project into a Docker image. This Docker image can 
then be deployed to your service of choice to run a webhook server with a permanent URL that the Sapio system can 
access.

### Resources

* [sapiopylib](https://pypi.org/project/sapiopylib/): Our PyPI page for all sapiopylib releases.
* [sapiopycommons](https://pypi.org/project/sapiopycommons/): Our PyPI page for all sapiopycommons releases.
* [Sapio Py Tutorials](../../README.md): The tutorial repository containing this project, with further information
  and notebooks for sapiopylib.
