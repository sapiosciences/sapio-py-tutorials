#! /usr/bin/env python
import os

from sapiopycommons.general.time_util import TimeUtil
from sapiopycommons.webhook.webhook_handlers import CommonsWebhookHandler
from sapiopylib.rest.WebhookService import WebhookConfiguration, WebhookServerFactory
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from waitress import serve

from exercises.B_webhook_fundamentals import SubjectLinkSolution, \
    SubjectLinkBroken, ContextCounter
from exercises.G_record_models_comparison import DataRecordTimingExample, RecordModelTimingExample

# TimeUtil is a utility provided by sapiopycommons for handling timezone conversions.
# This call sets up a default timezone that all calls to TimeUtil will use unless otherwise
# specified by the input parameters. This would typically be the timezone that matches the
# customer's location.
TimeUtil.set_default_timezone("UTC")

# verify_sapio_cert should be true by default. This means that the webhook server will verify the certifications
# of the system that it is interacting with.
# debug should be false by default, as having a deployed server in debug mode can be unsafe.
# client_timeout_seconds is the default amount of time that the webhook server will wait for a response from the
# Sapio server when making requests. This can be changed here to affect all registered endpoints, or changed on a
# per-endpoint basis by changing the webhook handler's client_timeout_seconds class variable.
config: WebhookConfiguration = WebhookConfiguration(verify_sapio_cert=True, debug=False, client_timeout_seconds=600)

# IMPORTANT NOTICE: This should never be true for deployed code. It should only be necessary to set this to false when
# developing on a local Sapio system that does not have valid certs (but does not need them because it is not on the
# wider internet). We suggest using environment variables instead of changing the values in the server file directly to
# avoid unintentionally deploying unsafe changes.
if os.environ.get('SapioWebhooksInsecure') == "True":
    config.verify_sapio_cert = False


class Ping(CommonsWebhookHandler):
    """
    A simple webhook that returns the time as a toaster popup when invoked from the system.
    Intended to be placed on the main toolbar to verify that the webhook server is running and
    is able to be access by the system.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        now: str = TimeUtil.now_in_format("%H:%M:%S")
        return SapioWebhookResult(True, f"The webhook server is active.\nServer time: {now}.")


# Ping to see if the webhook server is running.
config.register('/ping', Ping)

# Register new endpoints here:
# config.register('/endpoint', ClassName)

config.register('/context-counter', ContextCounter)
config.register('/working-example', SubjectLinkSolution)
config.register('/broken-example', SubjectLinkBroken)

config.register('/data-record-timing-example', DataRecordTimingExample)
config.register('/record-model-timing-example', RecordModelTimingExample)

app = WebhookServerFactory.configure_flask_app(app=None, config=config)


# Health check route. This is required for deployments to services which use
# a specific GET endpoint to check the health of the webhook server.
@app.route("/ping")
def health_check():
    return "Alive!"


# Run this to run a local server. The app you are using will need a way to access this
# port on your local host in order to interact with the webhook server. This can be achieved
# by using a service such as ngrok, or using your device's IP on an internal network as the webhook URL.
# A Docker image built using the provided Dockerfile will instead use Gunicorn as the entry point,
# meaning that changes to the below code will not affect a deployed webhook server.
if __name__ == '__main__':
    host = "0.0.0.0"
    port = 8080
    # You can set this environment variable to true on your local machine
    # to change this behavior when you run the server locally.
    if os.environ.get('SapioWebhooksDebug') == "True":
        app.run(host=host, port=port, debug=True)
    else:
        serve(app, host=host, port=port)
