from sapiopycommons.webhook.webhook_handlers import CommonsWebhookHandler
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult

# Task:
#   Create a form toolbar button for samples that lets you update the sample status field from a list of values defined
#   in the system. You will first need to query the list from the system and then display its contents to the user to
#   choose from. Once the user has selected an option, you will need to update the sample's ExemplarSampleStatus field
#   with the value and commit that change to the server.
#   You could use the "Exemplar Sample Status" list that already exists in the system, or you could create your own.
# Training Topics:
#   Form toolbar buttons
#   Record manipulation
#   Pick lists
#   Client callbacks
# Webhook Context:
#   Form toolbar buttons contain the data record and data type name for the record in the system that the button was
#   clicked from. These are present in context.data_record and context.data_type_name. If this were a table toolbar
#   button, then the list of records that were selected by the user would be in the context.data_record_list variable.
# System Config:
#   In the system, navigate to App Setup -> Manage Rules & Webhooks -> Webhooks, create a new webhook, and select
#   "Data Type Record Toolbar" as the invocation type. Restrict the button to only appear on Samples. You may optionally
#   update the order that the webhook appears in on the toolbar. Lower values result in the button appearing further to
#   the left in the toolbar. If there are too many buttons on the toolbar and you configure the webhook with a large
#   order value, then it will appear in the overflow menu of the toolbar (the triple dots).
# Relevant Classes:
#   ClientCallback: Consider using the show_list_dialog() functions.
#   CallbackUtil: Consider using the list_dialog() functions.
#   PickListManager: This class can be used to retrieve lists that are defined in the system. Lists are defined by going
#       to App Setup -> Configuration Manager -> List Manager.
#   DataMgmtServer: This can be used to retrieve the ClientCallback or PickListManager classes.
#   DataRecordManager: If you use data records to achieve this task, you will want to use the commit_data_records()
#       function to commit data record changes to the system.
#   RecordModelManager: If you use record models to achieve this task, you store_and_commit() function is what is used
#       to commit record model changes.
#   RecordModelInstanceManager: If you use record models to achieve this task, you will want to use the
#       add_existing_records_of_type() function to convert the sample data record in the context into a record model.
#   SampleModel: If you use record models to achieve this task, then you would use this wrapper to create the
#       sample record model.
# Other Info:
#   Although using a list dialog is a simple way of achieving this task, you can also use an input dialog similar to
#   the previous exercise by creating a VeloxSelectionListFieldDefinition that is populated by the
#   "Exemplar Sample Status" pick list. When there are multiple ways of achieving the same task, the method chosen
#   typically comes down to which solution has the better UX and user preference for that particular task.


class SampleFormToolbarButton(CommonsWebhookHandler):
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # TODO: Implement the webhook here.
        return SapioWebhookResult(True)
