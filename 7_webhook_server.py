from datetime import date
from typing import Any, Dict, List, Optional, cast

from sapiopylib.rest.DataMgmtService import DataMgmtServer
from sapiopylib.rest.WebhookService import AbstractWebhookHandler, WebhookConfiguration, WebhookServerFactory
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.datatype.FieldDefinition import VeloxBooleanFieldDefinition, VeloxEnumFieldDefinition, \
    VeloxIntegerFieldDefinition, \
    VeloxStringFieldDefinition
from sapiopylib.rest.pojo.eln.ExperimentEntry import ExperimentEntry
from sapiopylib.rest.pojo.eln.ExperimentEntryCriteria import ElnEntryCriteria, ExperimentEntryCriteriaUtil
from sapiopylib.rest.pojo.eln.SapioELNEnums import ElnEntryType, ExperimentEntryStatus
from sapiopylib.rest.pojo.webhook.ClientCallbackRequest import FormEntryDialogRequest, OptionDialogRequest, \
    DataRecordSelectionRequest
from sapiopylib.rest.pojo.webhook.ClientCallbackResult import DataRecordSelectionResult, FormEntryDialogResult, \
    OptionDialogResult
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.utils.FormBuilder import FormBuilder
from sapiopylib.rest.utils.FoundationAccessioning import FoundationAccessionManager
from sapiopylib.rest.utils.ProtocolUtils import ELNStepFactory
from sapiopylib.rest.utils.Protocols import ElnEntryStep, ElnExperimentProtocol
from sapiopylib.rest.utils.recordmodel.RecordModelManager import RecordModelManager
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
            form_result: Optional[FormEntryDialogResult] = cast(Optional[FormEntryDialogResult],
                                                                context.client_callback_result)

            # Check that the user has not cancelled
            if not form_result.user_cancelled:
                # Get a dictionary which maps form field names to the user input
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


class AddRecords(AbstractWebhookHandler):
    """
    This webhook adds records to a table in the experiment its invoked on.
    """
    DATA_TYPE = "Data Type"
    NUMBER = "Number"

    NEW = "Add New Records"
    EXISTING = "Add Existing Records"
    CANCEL = "Cancel"

    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        form_result = cast(
            FormEntryDialogResult | OptionDialogResult | DataRecordSelectionResult | None,
            context.client_callback_result,
        )

        # Step 1: Display a form and ask the user to choose a data type
        if form_result is None:
            return self.__prompt_for_data_type(context)

        # Step 2: Ask whether to add new or existing records
        elif (
                isinstance(form_result, FormEntryDialogResult)
                and form_result.user_response_map is not None
                and self.DATA_TYPE in form_result.user_response_map
        ):
            return self.__prompt_for_new_or_existing(context, form_result)

        # Step 3.new: New was selected so prompt for the number of records
        elif (
                isinstance(form_result, OptionDialogResult)
                and form_result.button_text == self.NEW
        ):
            return self.__prompt_for_number_of_records(context)

        # Step 4.new: Add new records
        elif (
                isinstance(form_result, FormEntryDialogResult)
                and form_result.user_response_map is not None
                and self.NUMBER in form_result.user_response_map
        ):
            selected_internal_data_type_name = context.client_callback_result.callback_context_data

            num_records: int = form_result.user_response_map[self.NUMBER]

            records: list[DataRecord] = context.data_record_manager.add_data_records(
                selected_internal_data_type_name, num_records
            )

            self.__add_records_to_table(context, records)

            return SapioWebhookResult(True)

        # Step 3.existing: Existing was selected so show a prompt with existing data records to be added
        elif (
                isinstance(form_result, OptionDialogResult)
                and form_result.button_text == self.EXISTING
        ):
            return self.__prompt_for_existing_records(context)

        # Step 4.existing: Add selected records to table
        elif isinstance(form_result, DataRecordSelectionResult) and form_result.selected_field_map_list is not None:

            # Get the RecordIds of the selected records
            record_ids = [
                selected_record_map["RecordId"] for selected_record_map in form_result.selected_field_map_list
            ]

            selected_data_type_internal_name = context.client_callback_result.callback_context_data

            data_record_manager = context.data_record_manager
            records = list(data_record_manager.query_data_records_by_id(selected_data_type_internal_name, record_ids))

            self.__add_records_to_table(context, records)

            return SapioWebhookResult(True)

        elif form_result.user_cancelled or (
                isinstance(form_result, OptionDialogResult) and form_result.button_text == self.CANCEL
        ):
            print("User cancelled adding records.")
            return SapioWebhookResult(True)

        print(f"Unhandled case in {self.__class__.__name__}: type of form_result is {type(form_result)}"
              "which is not expected")

        return SapioWebhookResult(
            False,
            display_text=f"An error occurred. Please report a bug in {self.__class__.__name__} to Support",
        )

    def __prompt_for_data_type(self, context: SapioWebhookContext) -> SapioWebhookResult:

        data_type_manager = DataMgmtServer.get_data_type_manager(context.user)
        data_type_internal_names = data_type_manager.get_data_type_name_list()

        data_type_cache_manager = RecordModelManager(context.user).data_type_cache_manager

        # This line performs an api call for each name which makes it slow
        data_type_display_names = [
            data_type_cache_manager.get_display_name(internal_name) for internal_name in data_type_internal_names
        ]

        internal_and_display_names = zip(data_type_internal_names, data_type_display_names)

        data_type_names_formatted = [
            f"{display_name} ({internal_name})" for internal_name, display_name in internal_and_display_names
        ]

        form_builder = FormBuilder()
        data_type_field = VeloxEnumFieldDefinition(
            form_builder.get_data_type_name(),
            self.DATA_TYPE,
            self.DATA_TYPE,
            default_value=None,
            values=data_type_names_formatted,
        )
        data_type_field.required = True
        data_type_field.editable = True

        form_builder.add_field(data_type_field)
        temp_dt = form_builder.get_temporary_data_type()
        request = FormEntryDialogRequest("Choose a Data Type", "", temp_dt)

        return SapioWebhookResult(True, client_callback_request=request)

    def __prompt_for_new_or_existing(self, context: SapioWebhookContext,
                                     form_result: FormEntryDialogResult) -> SapioWebhookResult:

        data_type_manager = DataMgmtServer.get_data_type_manager(context.user)
        internal_data_type_names = data_type_manager.get_data_type_name_list()

        data_type_idx: int = form_result.user_response_map[self.DATA_TYPE]

        selected_internal_data_type_name = internal_data_type_names[data_type_idx]

        # These options may be displayed in the reverse order.
        # This can be controlled by a user theme setting.
        options = [self.CANCEL, self.NEW, self.EXISTING]

        option_request = OptionDialogRequest(
            "Add New or Existing Records",
            "Add New or Existing Records",
            options,
            closable=True,
        )

        # We save data between calls to this webhook by attaching it to the request via the
        # callback_context_data attribute
        option_request.callback_context_data = selected_internal_data_type_name

        return SapioWebhookResult(True, client_callback_request=option_request)

    def __prompt_for_number_of_records(self, context: SapioWebhookContext) -> SapioWebhookResult:
        form_builder = FormBuilder()
        num_field = VeloxIntegerFieldDefinition(
            form_builder.get_data_type_name(),
            self.NUMBER,
            "Number of Records to add",
            default_value=1,
            min_value=1,
        )
        num_field.required = True
        num_field.editable = True

        form_builder.add_field(num_field)
        temp_dt = form_builder.get_temporary_data_type()
        request = FormEntryDialogRequest("", "", temp_dt)

        # Context data only persists from one call to the next,
        # so we need to manually pass it along.
        request.callback_context_data = context.client_callback_result.callback_context_data

        return SapioWebhookResult(True, client_callback_request=request)

    def __prompt_for_existing_records(self, context: SapioWebhookContext) -> SapioWebhookResult:
        experiment_id = context.active_protocol.get_id()

        data_type_cache_manager = RecordModelManager(context.user).data_type_cache_manager
        selected_internal_data_type_name = context.client_callback_result.callback_context_data
        data_type_plural_display_name = data_type_cache_manager.get_plural_display_name(
            selected_internal_data_type_name
        )

        data_record_manager = context.data_record_manager

        # Get all records of type selected_internal_data_type_name
        records = list(data_record_manager.query_all_records_of_type(selected_internal_data_type_name))

        records_in_table = _get_records_in_table(context, experiment_id, data_type_plural_display_name)

        # Display records that are not already in the table
        records_not_in_table = [record for record in records if record not in records_in_table]

        data_type_display_name = data_type_cache_manager.get_display_name(selected_internal_data_type_name)
        data_type_manager = DataMgmtServer.get_data_type_manager(context.user)
        fields = data_type_manager.get_field_definition_list(selected_internal_data_type_name)

        request = DataRecordSelectionRequest(
            data_type_display_name,
            data_type_plural_display_name,
            fields,
            [record.get_fields() for record in records_not_in_table],
            multi_select=True,
        )
        request.callback_context_data = selected_internal_data_type_name
        return SapioWebhookResult(True, client_callback_request=request)

    def __add_records_to_table(self, context: SapioWebhookContext, records: list[DataRecord]) -> None:
        """
        If the table doesn't already exist it is created and added to the Experiment
        """
        data_type_cache_manager = RecordModelManager(context.user).data_type_cache_manager

        selected_internal_data_type_name = context.client_callback_result.callback_context_data

        data_type_plural_display_name = data_type_cache_manager.get_plural_display_name(
            selected_internal_data_type_name)

        protocol = context.active_protocol

        experiment_id = protocol.get_id()

        table_name = format_table_name(data_type_plural_display_name)
        table = get_entry_by_name(context, experiment_id, table_name)

        eln_manager = context.eln_manager

        if table is None:
            # Create new table entry since it doesn't exist

            # Place the table at the end of the experiment
            table_position = len(protocol.get_sorted_step_list()) + 1

            new_table_entry_criteria = ElnEntryCriteria(
                ElnEntryType.Table, table_name, selected_internal_data_type_name, table_position
            )

            table = eln_manager.add_experiment_entry(experiment_id, new_table_entry_criteria)

        eln_manager.add_records_to_table_entry(experiment_id, table.entry_id, records)


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
config.register('/eln/add_records', AddRecords)
config.register('/eln/check_number_samples', CheckNumberOfSamples)

app = WebhookServerFactory.configure_flask_app(app=None, config=config)
# UNENCRYPTED! This should not be used in production. You should give the "app" a ssl_context or set up a reverse-proxy.

# Dev Mode:
# app.run(host="0.0.0.0", port=8090)

# Production Mode
serve(app, host="0.0.0.0", port=8090)
