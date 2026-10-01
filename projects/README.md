# Webhooks
This folder contains two Python projects for writing Sapio webhooks with sapiopycommons and sapiopylib.

* [default_project](default_project): The starting point for every new webhook project. Copy this folder when you
  are creating a project from scratch. It contains a ready-to-run webhook server, a Dockerfile for deployment, and a
  requirements.txt that pins the library versions.
* [exercise_project](exercise_project): A series of examples and exercises that teach the fundamentals of writing
  webhooks. Review the files in the examples folder in alphabetical order, then try the exercises.

Other resources in this repository:
* [08_webhook_server.py](../08_webhook_server.py): A single-file sapiopylib webhook server example.
* [Tutorial 10](../10_python_record_models.ipynb): How to generate record models for your own system. Both projects
  mention this, since the bundled record model file only covers the data types of a stock system.

See the [root README](../README.md) for the difference between sapiopylib and sapiopycommons and how to pick the
library versions that match your Sapio system.

### Testing and Deploying
Running a project's server.py starts a local webhook server. Sapio needs network access to that server to call it. If
your machine is on a separate network from the Sapio server, use a tunneling service such as
[ngrok](https://ngrok.com/) (`ngrok http 8080`), or ask your
IT team to make your machine available. Each project's Dockerfile can build the project into an image for permanent
deployment.
