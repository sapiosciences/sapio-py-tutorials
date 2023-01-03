from typing import List, Dict, Any

from sapiopylib.rest.DataMgmtService import DataMgmtServer
from sapiopylib.rest.WebhookService import AbstractWebhookHandler, WebhookConfiguration, WebhookServerFactory
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.datatype.FieldDefinition import VeloxBooleanFieldDefinition, VeloxStringFieldDefinition
from sapiopylib.rest.pojo.webhook.ClientCallbackRequest import FormEntryDialogRequest
from sapiopylib.rest.pojo.webhook.ClientCallbackResult import FormEntryDialogResult
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.utils.FormBuilder import FormBuilder
from sapiopylib.rest.utils.Protocols import AbstractProtocol
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


class ExperimentRuleHandler(AbstractWebhookHandler):
    """
    The entry and notebook that triggered the rule will be on the context.
    """

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        print("Experiment Entries of Rule: " + ','.join([entry.entry_name for entry in context.experiment_entry_list]))
        print("Notebook Experiment of Rule: " + context.eln_experiment.notebook_experiment_name)
        entry = context.experiment_entry_list[0]
        eln_manager = DataMgmtServer.get_eln_manager(context.user)
        records = eln_manager.get_data_records_for_entry(context.eln_experiment.notebook_experiment_id, entry.entry_id)
        print("Record Values were: " + ','.join([str(record.get_field_value('NewField'))
                                                 for record in records.result_list]))
        return SapioWebhookResult(True)


class NotebookExperimentToolbarExampleHandler(AbstractWebhookHandler):
    """
    Find the source sample table in the notebook experiment. Count how many samples there are.
    Then, see if there are aliquots. If there are aliquots, print aliquot/sample ratio.
    If there are no aliquot table or sample table, display a text to user saying so.
    """

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        active_protocol: AbstractProtocol = context.active_protocol
        sample_step = active_protocol.get_first_step_of_type('Sample')
        if sample_step is None:
            return SapioWebhookResult(True, display_text='There are no source sample table.')
        source_sample_records: List[DataRecord] = sample_step.get_records()
        source_sample_record_count = len(source_sample_records)
        # Find the next sample table after the current source sample table,
        # excludes the sample table and everything before.
        aliquot_step = active_protocol.get_next_step(sample_step, 'Sample')
        if aliquot_step is None:
            return SapioWebhookResult(True, display_text='There are no aliquot sample table.')
        aliquot_sample_record_count = len(aliquot_step.get_records())
        return SapioWebhookResult(True, display_text='The aliquot to sample ratio is: ' +
                                                     str(aliquot_sample_record_count / source_sample_record_count))


# Note: the registration points here are directly under root.
# In this example, we are listening to 8090. So the endpoint URL to be configured in Sapio is:
# http://[webhook_server_hostname]:8090/hello_world

config: WebhookConfiguration = WebhookConfiguration(verify_sapio_cert=False, debug=True)
config.register('/hello_world', HelloWorldWebhookHandler)
config.register('/feedback_form', UserFeedbackHandler)
config.register('/new_goo', NewGooOnSaveRuleHandler)
config.register('/eln/rule_test', ExperimentRuleHandler)
config.register('/eln/sample_aliquot_count', NotebookExperimentToolbarExampleHandler)

app = WebhookServerFactory.configure_flask_app(app=None, config=config)
# UNENCRYPTED! This should not be used in production. You should give the "app" a ssl_context or set up a reverse-proxy.

# Dev Mode:
# app.run(host="0.0.0.0", port=8090)

# Production Mode
serve(app, host="0.0.0.0", port=8090)
