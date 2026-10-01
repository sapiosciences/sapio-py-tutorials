from sapiopycommons.webhook.webhook_handlers import CommonsWebhookHandler
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult

# Task:
#   Create a main toolbar button that prompts the user for a number of new samples to create. After creating the number
#   of records provided by the user, direct the user to a table containing the newly created records.
#   Prevent the user from inputting an invalid value, such as a negative value or a value that is too high.
# Training Topics:
#   Main toolbar buttons
#   Record creation
#   Client callbacks
#   Directives
# Webhook Context:
#   Main toolbar buttons contain the bare minimum amount of information in the context. Aside from knowing that the
#   invocation point is from the main toolbar and having information about the user who called the webhook, the
#   webhook context for main toolbar buttons is effectively empty.
# System Config:
#   In the system, navigate to App Setup -> Manage Rules & Webhooks -> Webhooks, create a new webhook, and select
#   "Main Toolbar" as the invocation type. You may name this button however you wish, and may also optionally give it
#   a different icon, a description, and a folder path that the button should appear in.
#   The main toolbar is the menu that appears on the left side of the screen on any page in the system. If you have not
#   given your button a folder path, it may be present in a "General" folder. If there is only a single button defined
#   to appear in a folder, then the button will appear in place of the folder instead.
# Relevant Classes:
#   ClientCallback: The base class used for sending client callback requests. You can initialize a ClientCallback
#       yourself, or get one from the DataMgmtServer. There are multiple methods that you could use to request an
#       integer from the user, but consider using the show_input_dialog() function.
#   CallbackUtil: A utility class for streamlining client callback requests. If the base class of your webhook is
#       CommonsWebhookHandler (which it is here), then self.callback provides you with a CallbackUtil. Consider using
#       the input_dialog() or integer_input_dialog() functions.
#   DataMgmtServer: This is a class with static functions for initializing manager/service classes from sapiopylib.
#       It can be used to retrieve a ClientCallback object using the get_client_callback() function.
#   DataRecordManager: This can be used for creating data records in the system via webservice request. You can retrieve
#       a DataRecordManager using context.data_record_manager, or self.dr_man if your webhook extends
#       CommonsWebhookHandler. You will want to use the add_data_records() function to create new sample records.
#   RecordModelManager: This class can be used for committing record model changes to the system. You can initialize a
#       RecordModelManager yourself, or by using self.rec_man if your webhook extends CommonsWebhookHandler. The
#       store_and_commit() function is what is used to commit record model changes.
#   RecordModelInstanceManager: This class can be used to create record models in your webhook cache without creating
#       them in the system until you commit the record model changes. You can retrieve one from an existing
#       RecordModelManager, or by using self.inst_man if your webhook extends CommonsWebhookHandler. The
#       add_new_records_of_type() function is what you would use to create new sample record models.
#   SampleModel: If you utilize record models to achieve this task, then you would use this wrapper to create the
#       sample record models.
#   TableDirective: Directives are a type of object that can be returned in a SapioWebhookResult's "directive"
#       parameter. They direct the user to a new page after the webhook is done running and has returned a result.
#       A TableDirective takes in a list of DataRecords and directs the user to a table containing those records.
#       Note that not all invocation types in the system are able to use directives. If you utilize record models
#       to achieve this task, you will need to convert them to DataRecords in order to add them to the TableDirective.
#   AliasUtil: A class with functions for converting between similar types of records. You can use the to_data_records()
#       function to easily convert a list of record models to DataRecords.
#   SapioUserErrorException: If the user creates an error of some sort given their input (e.g. if a value is outside of
#       an allowed range), then you can raise this exception at any point in your webhooks to return an error message as
#       a toaster popup to the user if your webhook extend CommonsWebhookHandler. Note that for the purposes of this
#       example, you may also be able to create your client callback in such a way that it prevents the user from giving
#       a bad value to the webhook to begin with. In this case you could also return an error message to the user by
#       returning a SapioWebhookResult with a display_text value filled in, or use a different client callback request
#       to notify the user.
# Other Info:
#   Remember to go to the server.py file and register an endpoint for the class you create. This endpoint will be what
#   you add to the end of the webhook server URL in the "Webhook URL" field of the webhook config.
#
#   There are multiple ways to achieve any task. You won't need to use all the relevant classes listed above, but each
#   of them can be used to achieve this task. Try creating multiple classes that each use a different method to achieve
#   this task so that you can get familiar with the different ways of doing things. We encourage you to try this with
#   each of the exercises in this project.
#
#   Using the CallbackUtil's integer_input_dialog() function is the simplest way to achieve asking the user for an
#   integer. Using input_dialog() or ClientCallback's show_input_dialog() will require you to define a
#   VeloxIntegerFieldDefinition. If you go down this route, the C_client_callbacks.py file has examples of creating
#   field definitions.


class MainToolbarButton(CommonsWebhookHandler):
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # TODO: Implement the webhook here.
        return SapioWebhookResult(True)
