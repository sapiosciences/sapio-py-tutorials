from typing import List, Dict, Any

from sapiopylib.rest.WebhookService import AbstractWebhookHandler, WebhookConfiguration, WebhookServerFactory
from sapiopylib.rest.pojo.datatype.FieldDefinition import VeloxBooleanFieldDefinition, VeloxStringFieldDefinition
from sapiopylib.rest.pojo.webhook.ClientCallbackRequest import FormEntryDialogRequest
from sapiopylib.rest.pojo.webhook.ClientCallbackResult import FormEntryDialogResult
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.utils.FormBuilder import FormBuilder
from waitress import serve


class HelloWorldWebhookHandler(AbstractWebhookHandler):
    """
    Prints "Hello World" in the python console whenever the webhook handler is invoked.
    """

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        print("Hello World!")
        return SapioWebhookResult(True)


class UserFeedbackHandler(AbstractWebhookHandler):
    """
    Ask user some questions, get response back.
    """

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        if context.client_callback_result is not None:
            # This is Round 2, user has answered the feedback form. We are parsing the results...
            # noinspection PyTypeChecker
            form_result: FormEntryDialogResult = context.client_callback_result
            if not form_result.user_cancelled:
                response_map: Dict[str, Any] = form_result.user_response_map
                feeling: bool = response_map.get('Feeling')
                comments: str = response_map.get('Comments')
                msg: str
                if feeling:
                    msg = "User felt very good! Nothing to do here..."
                else:
                    msg = "=_= User didn't feel very good. The comment left was: " + str(comments)
                print(msg)
                # Display text sent over will be a toastr on the web client in Sapio.
                return SapioWebhookResult(True, client_callback_request=None, display_text=msg)
            else:
                print("Cancelled.")
                return SapioWebhookResult(True, display_text="You have Cancelled!")
        else:
            # This is Round 1, user hasn't done anything we are just telling Sapio Platform to display a form...
            form_builder: FormBuilder = FormBuilder()
            feeling_field = VeloxBooleanFieldDefinition(form_builder.get_data_type_name(), 'Feeling',
                                                        "Are you feeling well?", default_value=False)
            feeling_field.required = True
            feeling_field.editable = True
            form_builder.add_field(feeling_field)
            comments_field = VeloxStringFieldDefinition(form_builder.get_data_type_name(), 'Comments',
                                                        "Additional Comments", max_length=2000)
            comments_field.editable = True
            form_builder.add_field(comments_field)
            temp_dt = form_builder.get_temporary_data_type()
            request = FormEntryDialogRequest("Feedback", "Please provide us with some feedback!", temp_dt)
            return SapioWebhookResult(True, client_callback_request=request)


class NewGooOnSaveRuleHandler(AbstractWebhookHandler):
    """
    When a new "Goo" data type record is created, run this rule.
    """

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        print("New Goo '" + str(context.data_record))
        return SapioWebhookResult(True, display_text="New Goo!")


config: WebhookConfiguration = WebhookConfiguration(verify_sapio_cert=False, debug=True)
config.register('/hello_world', HelloWorldWebhookHandler)
config.register('/feedback_form', UserFeedbackHandler)
config.register('/new_goo', NewGooOnSaveRuleHandler)

app = WebhookServerFactory.configure_flask_app(app=None, config=config)
# Dev Mode:
# app.run(host="0.0.0.0", port=8090)

# Production Mode
serve(app, host="0.0.0.0", port=8090)
