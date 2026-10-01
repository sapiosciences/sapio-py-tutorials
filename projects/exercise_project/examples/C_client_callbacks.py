from typing import Any

from sapiopycommons.callbacks.callback_util import CallbackUtil
from sapiopycommons.webhook.webhook_handlers import CommonsWebhookHandler
from sapiopylib.rest.ClientCallbackService import ClientCallback
from sapiopylib.rest.DataMgmtService import DataMgmtServer
from sapiopylib.rest.pojo.datatype.FieldDefinition import VeloxStringFieldDefinition, AbstractVeloxFieldDefinition, \
    VeloxIntegerFieldDefinition, VeloxBooleanFieldDefinition
from sapiopylib.rest.pojo.webhook.ClientCallbackRequest import OptionDialogRequest, DisplayPopupRequest, PopupType, \
    FormEntryDialogRequest, TableEntryDialogRequest
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.utils.DataTypeCacheManager import DataTypeCacheManager
from sapiopylib.rest.utils.FormBuilder import FormBuilder

from utilities.data_type_models import SampleModel


class CallbackCallbackExample(CommonsWebhookHandler):
    """
    Under normal circumstances, a webhook will run from start to finish without any interruption or input form the user.
    There are often times when we do want input from the user, though, such as when we want the user to upload a file,
    acknowledge a change, or input values into a table or form. When this is the case, you need to make use of a client
    callback.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # Using the DataMgmtServer, you can retrieve a ClientCallback object used for making client callbacks.
        # For future reference, this DataMgmtServer class can be used to retrieve various other objects for making
        # API requests to the system, such as querying for data type definition information or running custom reports.
        callback: ClientCallback = DataMgmtServer.get_client_callback(context.user)

        # In order to make a client callback, you must first construct a request object corresponding to the type of
        # client callback you want to make. Let's create a client callback that asks the user to click either yes or no.
        # This can be done by creating an option dialog request, which displays text to the user alongside a selection
        # of buttons.
        options: list[str] = ["Yes", "No"]
        request = OptionDialogRequest("Notice", "Do you wish to proceed?", options, callback_context_data="1")
        # This request is then passed to the client callback class with the function corresponding to the request type.
        # This particular request type will return either an integer corresponding to the index of the above options
        # list for the button that the user chose, or it will return a None object if the user cancelled the dialog.
        response: int | None = callback.show_option_dialog(request)
        # Always check to see if the user cancelled the dialog before doing anything else with the response.
        if response is None:
            return SapioWebhookResult(True, "User cancelled.")
        # Now that we know that the user didn't cancel the request dialog, we can make use of the response.
        button: str = options[response]
        if button == "No":
            return SapioWebhookResult(True)

        # Aside from just dialog boxes, you can also generate toaster messages that pop up in the bottom right corner
        # of the user's screen without interrupting their correct actions.
        request = DisplayPopupRequest("Notice", f"You replied {button} to the option dialog.", PopupType.Info)
        callback.display_popup(request)

        # Let's construct a form for the user to edit the fields of. This can be done using the form builder class.
        form_builder = FormBuilder()
        # The form builder takes in field definitions to determine how to display the form to the user. In this case,
        # we're constructing a new field definition from scratch.
        form_builder.add_field(VeloxStringFieldDefinition("Test", "Test Field", "Test Field", editable=True), 0, 2)
        # But you can also use the data type cache manager to query the system for fields defined on a data type in the
        # data designer. Let's query for and display a few sample fields.
        dt_cache = DataTypeCacheManager(context.user)
        sample_fields: dict[str, AbstractVeloxFieldDefinition] = dt_cache.get_fields_for_type(SampleModel.DATA_TYPE_NAME)
        form_builder.add_field(sample_fields.get("SampleId"), 2, 2)
        form_builder.add_field(sample_fields.get("Volume"), 0, 2)
        form_builder.add_field(sample_fields.get("Concentration"), 2, 2)

        # The form dialog request allows you to specify the default values that appear for each field.
        default_values: dict[str, Any] = {
            "SampleId": "Fake Sample",
            "Volume": 10,
            "Concentration": 5,
            "Test Field": "Edit me."
        }

        temp_type_def = form_builder.get_temporary_data_type()
        request = FormEntryDialogRequest("Test Form", "Test form, please ignore.", temp_type_def, default_values)
        # The
        response: dict[str, Any] | None = callback.show_form_entry_dialog(request)
        # Remember to always check for a cancelled result.
        if response is None:
            return SapioWebhookResult(True, "User Cancelled")

        # We can use the same form builder for creating table dialogs.
        form_builder = FormBuilder()
        form_builder.add_field(VeloxStringFieldDefinition("Test", "Text", "Test Text Field"))
        form_builder.add_field(VeloxIntegerFieldDefinition("Test", "Integer", "Test Integer Field"))
        form_builder.add_field(VeloxBooleanFieldDefinition("Test", "Boolean", "Test Boolean Field"))

        rows: list[dict[str, Any]] = [
            {"Text": "Do", "Integer": 1, "Boolean": True},
            {"Text": "Re", "Integer": 2, "Boolean": False},
            {"Text": "Mi", "Integer": 3, "Boolean": True},
        ]
        temp_type_def = form_builder.get_temporary_data_type()
        request = TableEntryDialogRequest("Test Table", "Test table, please ignore.", temp_type_def, rows)
        response: list[dict[str, Any]] | None = callback.show_table_entry_dialog(request)
        if response is None:
            return SapioWebhookResult(True, "User cancelled.")

        # There are many, many other client callback types aside from just these. Explore the various functions of
        # the client callback class to see what's available.

        return SapioWebhookResult(True)


class CallbackUtilExample(CommonsWebhookHandler):
    """
    Similar to how sapiopycommons has the record handler class for streamlining record related actions, it also has
    a callback util class for streamlining client callback related actions.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # Callback util provides functions for constructing and returning the results of the various callback types.
        # It also takes care of checking if the user cancelled the dialog for you. If the user cancels a dialog, then a
        # SapioUserCancelledException is thrown. If you're using a webhook handler that extends CommonsWebhookHandler,
        # then that exception will be caught and return to the user as a "User cancelled" toaster message. If you wish
        # to add special cancellation handling, then just add a try/except around your callback calls and handle the
        # exception on your own, or have your webhook handler override CommonsWebhookHandler's
        # handle_user_cancelled_exception function.
        callback = CallbackUtil(context)
        responded_yes: bool = callback.yes_no_dialog("Notice", "Do you wish to proceed?")
        if not responded_yes:
            return SapioWebhookResult(True)

        # The client callback class allows you to request files from the user and send files to the user to download,
        # but these request types can be rather odd to use. The callback util's functions for these actions are much
        # simpler.
        file_name, file_bytes = callback.request_file("Provide a text file.", ["txt"])
        callback.write_file(file_name, file_bytes)

        # Callbacks that make use of the FormBuilder are made easy for you, condensing what would have been
        # many lines of code into a single function call. Assuming that there are sample records in the context,
        # the two callbacks below construct a form and then a table displaying fields from the sample data type,
        # with the fields in the entry dialogs populated by the given records.
        form_response: dict[str, Any] = callback.\
            record_form_dialog("Test Form", "Test form, please ignore",
                               ["SampleId", "Volume", "Concentration"], context.data_record,
                               {"SampleId": (0, 4), "Volume": (0, 2), "Concentration": (2, 2)},
                               editable=True)

        table_response: list[dict[str, Any]] = callback.\
            record_table_dialog("Test Form", "Test form, please ignore",
                                ["SampleId", "Volume", "Concentration"], context.data_record_list,
                                editable=True)

        return SapioWebhookResult(True)
