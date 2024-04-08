from datetime import date
from typing import Any, Dict, List, Optional, cast

from sapiopylib.rest.ClientCallbackService import ClientCallback
from sapiopylib.rest.DataMgmtService import DataMgmtServer
from sapiopylib.rest.User import SapioUser
from sapiopylib.rest.WebhookService import AbstractWebhookHandler, WebhookConfiguration, WebhookServerFactory
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.datatype.FieldDefinition import VeloxBooleanFieldDefinition, VeloxStringFieldDefinition
from sapiopylib.rest.pojo.eln.ExperimentEntry import ExperimentEntry
from sapiopylib.rest.pojo.eln.ExperimentEntryCriteria import ElnEntryCriteria, ExperimentEntryCriteriaUtil
from sapiopylib.rest.pojo.eln.SapioELNEnums import ElnEntryType, ExperimentEntryStatus
from sapiopylib.rest.pojo.webhook.ClientCallbackRequest import FormEntryDialogRequest, DisplayPopupRequest, PopupType
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.utils.FormBuilder import FormBuilder
from sapiopylib.rest.utils.FoundationAccessioning import FoundationAccessionManager
from sapiopylib.rest.utils.ProtocolUtils import ELNStepFactory
from sapiopylib.rest.utils.Protocols import ElnEntryStep, ElnExperimentProtocol
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
        user: SapioUser = context.user
        client_callback: ClientCallback = DataMgmtServer.get_client_callback(user)

        # Use the FormBuilder utility to quickly create a temporary data type with default layouts.
        form_builder: FormBuilder = FormBuilder()

        # Define a Boolean field
        # The 2nd argument data_field_name is the key for this field in the user_response_map
        # The 3rd argument display_name is the message shown to the user besides the field itself
        feeling_field = VeloxBooleanFieldDefinition(form_builder.get_data_type_name(), 'Feeling',
                                                    "Are you feeling well?", default_value=False)
        # Make the field required to submit the form and make it changeable by the user
        feeling_field.required = True
        feeling_field.editable = True

        # Add the field to the form
        form_builder.add_field(feeling_field)
        comments_field = VeloxStringFieldDefinition(form_builder.get_data_type_name(), 'Comments',
                                                    "Additional Comments", max_length=2000)
        comments_field.editable = True
        form_builder.add_field(comments_field)
        temp_dt = form_builder.get_temporary_data_type()

        # 1st argument is the form's title, 2nd is the message
        request = FormEntryDialogRequest("Feedback", "Please provide us with some feedback!", temp_dt)
        form_dialog_result = client_callback.show_form_entry_dialog(request)

        if not form_dialog_result:
            # If user clicked cancel in the form entry dialog, a None object is returned.
            client_callback.display_popup(DisplayPopupRequest("Feedback Form", "You have Cancelled!", PopupType.Info))
        else:
            # Otherwise, the dictionary by field names we entered above would have been returned as result.
            feeling: bool = form_dialog_result.get('Feeling')
            comments: str = form_dialog_result.get('Comments')
            msg: str
            if feeling:
                msg = "User felt very good! Nothing to do here..."
            else:
                msg = "=_= User didn't feel very good. The comment left was: " + str(comments)
            client_callback.display_popup(DisplayPopupRequest("Feedback Form", msg, PopupType.Success))
        return SapioWebhookResult(True)


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

        # Get the first entry in the experiment
        entry = context.experiment_entry_list[0]

        eln_manager = DataMgmtServer.get_eln_manager(context.user)

        # Get the records contained in that entry
        records = eln_manager.get_data_records_for_entry(context.eln_experiment.notebook_experiment_id, entry.entry_id)

        # Print the value of NewField for each record in the entry
        print("Record Values were: " + ','.join([str(record.get_field_value('NewField'))
                                                 for record in records.result_list]))

        return SapioWebhookResult(True)


class ElnSampleAliquotRatioCountHandler(AbstractWebhookHandler):
    """
    Find the source sample table in the notebook experiment. Count how many samples there are.
    Then, see if there are aliquots. If there are aliquots, print aliquot/sample ratio.
    If there are no aliquot table or sample table, display a text to user saying so.
    """

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        active_protocol: Optional[ElnExperimentProtocol] = context.active_protocol

        # Get the first entry which has records of type Sample
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


class ElnStepCreationHandler(AbstractWebhookHandler):
    """
    Here are examples on how to use the protocol/step interfaces to easily create new steps in ELN.
    """

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        active_protocol: Optional[ElnExperimentProtocol] = context.active_protocol

        # We will create a Request form.
        request_record = context.data_record_manager.add_data_record('Request')
        request_record.set_field_value('RequestId', 'Python Webhook Demo Request ' + str(date.today()))

        context.data_record_manager.commit_data_records([request_record])

        ELNStepFactory.create_form_step(active_protocol, 'Request Data', 'Request', request_record)

        # Now, create another empty sample table under request form. This will be created after the last form.
        # Note: the cache for protocol provided is invalidated upon creating a new step,
        # but any other protocol references to the same protocol will not.
        ELNStepFactory.create_table_step(active_protocol, 'Samples', 'Sample')
        ELNStepFactory.create_text_entry(active_protocol, 'Hello World!')

        return SapioWebhookResult(True)


class ElnSampleCreationHandler(AbstractWebhookHandler):
    """
    Create a sample step if not exists, and then accession 8 blood samples.
    """

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        active_protocol: Optional[ElnExperimentProtocol] = context.active_protocol

        # Get the first entry which has records of type Sample
        sample_step = active_protocol.get_first_step_of_type('Sample')
        if sample_step is None:
            # Create the sample step if it doesn't exist
            sample_step = ELNStepFactory.create_table_step(active_protocol, 'Samples', 'Sample')

        sample_fields: List[Dict[str, Any]] = []
        num_samples = 8
        accession_man: FoundationAccessionManager = FoundationAccessionManager(context.user)
        sample_id_list: List[str] = accession_man.get_accession_with_config_list('Sample', 'SampleId', num_samples)

        # We're creating samples with ExemplarSampleType=Blood and with the ids accessioned above
        for sample_id in sample_id_list:
            sample_field = {
                'ExemplarSampleType': 'Blood',
                'SampleId': sample_id
            }
            sample_fields.append(sample_field)

        sample_records = context.data_record_manager.add_data_records_with_data('Sample', sample_fields)
        context.eln_manager.add_records_to_table_entry(active_protocol.eln_experiment.notebook_experiment_id,
                                                       sample_step.eln_entry.entry_id, sample_records)
        return SapioWebhookResult(True)


class BarChartDashboardCreationHandler(AbstractWebhookHandler):
    """
    Provide a bar chart for a sample table where x-axis is sample ID and y-axis is concentration.
    """

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        active_protocol: Optional[ElnExperimentProtocol] = context.active_protocol

        sample_step: Optional[ElnEntryStep] = active_protocol.get_first_step_of_type('Sample')

        # Check if the sample step exists
        if sample_step is None:
            return SapioWebhookResult(True, display_text="There are no sample step. Create it first.")

        ELNStepFactory.create_bar_chart_step(active_protocol, sample_step, "Concentration vs Sample ID",
                                             "SampleId", "Concentration")

        return SapioWebhookResult(True)


class AddInstrumentTracking(AbstractWebhookHandler):
    """
    Adds an Instrument Tracking Field Set to the experiment.
    Invoked by a toolbar button.
    """
    INSTRUMENT_TRACKING_NAME = "Instrument Tracking Field Set"

    INSTRUMENT_TRACKING_FIELD_SET_ID = 109

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        protocol = cast(ElnExperimentProtocol | None, context.active_protocol)
        assert protocol is not None

        experiment_id = protocol.get_id()
        entries = protocol.get_sorted_step_list()

        # Check if the Instrument Tracking field set is already present
        for entry in entries:
            if entry.get_name() == self.INSTRUMENT_TRACKING_NAME:
                return SapioWebhookResult(
                    True,
                    display_text="The Instrument Tracking Field Set is already used in this Experiment.",
                )

        # Place at the end of the experiment
        field_set_position = len(entries) + 1

        field_set_entry_criteria = ElnEntryCriteria(
            ElnEntryType.Form,
            self.INSTRUMENT_TRACKING_NAME,
            "",
            field_set_position,
            enb_field_set_id=self.INSTRUMENT_TRACKING_FIELD_SET_ID,
        )

        context.eln_manager.add_experiment_entry(experiment_id, field_set_entry_criteria)

        return SapioWebhookResult(True)


class AutoCompleteFirstEntry(AbstractWebhookHandler):
    """
    Autocompletes the first entry of the experiment it is called on.
    Invoked by a rule on experiment creation.
    """

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        protocol: ElnExperimentProtocol | None = cast(
            ElnExperimentProtocol | None, context.active_protocol
        )

        if protocol is None:
            msg = "Error: Protocol was None"
            print(msg)
            return SapioWebhookResult(False, display_text=msg)

        entry_list = context.eln_manager.get_experiment_entry_list(protocol.eln_experiment.notebook_experiment_id)

        # index 1 not 0 because experiments have a hidden first entry, Experiment Overview
        first_entry = entry_list[1]

        first_entry_update_criteria = (
            ExperimentEntryCriteriaUtil.create_empty_criteria(first_entry)
        )

        first_entry_update_criteria.entry_status = ExperimentEntryStatus.Completed

        exp_id = protocol.eln_experiment.notebook_experiment_id

        first_entry_id = first_entry.entry_id

        context.eln_manager.update_experiment_entry(
            exp_id, first_entry_id, first_entry_update_criteria
        )

        return SapioWebhookResult(True)


def get_entry_by_name(context: SapioWebhookContext, experiment_id: int, entry_name: str) -> ExperimentEntry | None:
    """
    Returns the entry with the specified name if it exists in the experiment else returns None
    """
    entries = context.eln_manager.get_experiment_entry_list(experiment_id)

    for entry in entries:
        if entry.entry_name == entry_name:
            return entry

    return None


# No way to reuse f-strings so use a function
def format_table_name(data_type_plural_display_name: str) -> str:
    """
    Given the plural display name of a data type this function returns the name of a table
    which holds records of that data type
    """
    return f"{data_type_plural_display_name} Records"


def _get_records_in_table(context: SapioWebhookContext, experiment_id: int,
                          data_type_plural_display_name: str) -> list[DataRecord]:
    """
    If the table exists then return a list of the records it contains, otherwise return an empty list
    """
    table_name = format_table_name(data_type_plural_display_name)
    table = get_entry_by_name(context, experiment_id, table_name)

    eln_manager = context.eln_manager

    records_in_table = []
    if table is not None:
        records_in_table = list(eln_manager.get_data_records_for_entry(experiment_id, table.entry_id))

    return records_in_table


def get_entry_by_option(context: SapioWebhookContext, option: str) -> ExperimentEntry | None:
    """
    Get the first entry in the context with the given entry option key, or None if no entry has that entry option.
    """
    exp_id = context.eln_experiment.notebook_experiment_id
    eln_manager = context.eln_manager
    entry_list = eln_manager.get_experiment_entry_list(exp_id, False)

    for entry in entry_list:
        if option in eln_manager.get_experiment_entry_options(exp_id, entry.entry_id):
            return entry
    return None


class CheckNumberOfSamples(AbstractWebhookHandler):
    """
    This webhook ensures that the table of samples has the correct number of samples.
    Invoked when the sample check entry is initialized.
    The samples table should have the option "SOURCE SAMPLES".
    The check entry should have the option "SAMPLE NUMBER CHECK"
    """

    CORRECT_NUM_SAMPLES = 5

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        samples_table = get_entry_by_option(context, "SOURCE SAMPLES")

        eln_manager = context.eln_manager
        exp_id = context.active_protocol.get_id()
        samples = list(eln_manager.get_data_records_for_entry(exp_id, samples_table.entry_id))

        # The check entry is false by default so there's no need to do anything in this case
        if len(samples) != self.CORRECT_NUM_SAMPLES:
            return SapioWebhookResult(True)

        check_entry = get_entry_by_option(context, "SAMPLE NUMBER CHECK")

        check_entry_record = list(eln_manager.get_data_records_for_entry(exp_id, check_entry.entry_id))[0]

        # Set the check to True, allowing the check entry to be submitted without being rejected.
        check_entry_record.set_field_value("CorrectNumber", True)

        # commit_data_records only accepts a list so wrap the record in a list
        context.data_record_manager.commit_data_records([check_entry_record])

        return SapioWebhookResult(True)


# Note: the registration points here are directly under root.
# In this example, we are listening to 8090. So the endpoint URL to be configured in Sapio is:
# http://[webhook_server_hostname]:8090/hello_world
config: WebhookConfiguration = WebhookConfiguration(verify_sapio_cert=False, debug=True)
config.register('/hello_world', HelloWorldWebhookHandler)
config.register('/feedback_form', UserFeedbackHandler)
config.register('/new_goo', NewGooOnSaveRuleHandler)
config.register('/eln/rule_test', ExperimentRuleHandler)
config.register('/eln/sample_aliquot_count', ElnSampleAliquotRatioCountHandler)
config.register('/eln/create_new_steps', ElnStepCreationHandler)
config.register('/eln/sample_creation', ElnSampleCreationHandler)
config.register('/eln/bar_chart_creation', BarChartDashboardCreationHandler)
config.register('/eln/add_instrument_tracking', AddInstrumentTracking)
config.register('/eln/autocomplete_first_entry', AutoCompleteFirstEntry)
config.register('/eln/check_number_samples', CheckNumberOfSamples)

app = WebhookServerFactory.configure_flask_app(app=None, config=config)
# UNENCRYPTED! This should not be used in production. You should give the "app" a ssl_context or set up a reverse-proxy.

# Dev Mode:
# app.run(host="0.0.0.0", port=8090)

# Production Mode
serve(app, host="0.0.0.0", port=8090)

#For performance reasons, we recommend using gunicorn. If you have gunicorn installed:
#Run "gunicorn server:app"
