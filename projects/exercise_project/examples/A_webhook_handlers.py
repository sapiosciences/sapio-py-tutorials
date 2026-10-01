import traceback
from abc import abstractmethod

from sapiopycommons.callbacks.callback_util import CallbackUtil
from sapiopycommons.general.exceptions import SapioUserErrorException, SapioException
from sapiopycommons.recordmodel.record_handler import RecordHandler
from sapiopycommons.webhook.webhook_handlers import CommonsWebhookHandler
from sapiopylib.rest.User import SapioUser
from sapiopylib.rest.WebhookService import AbstractWebhookHandler
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult

from utilities.data_type_models import SampleModel, PlateModel


class BasicWebhook(AbstractWebhookHandler):
    """
    All Sapio webhooks should be defined as classes that extend the AbstractWebhookHandler class (or one of its
    derivatives). This base class will take the JSON of the POST request that the Sapio system sends to the webhook
    server and convert it into a SapioWebhookContext object. At the end of the webhook's execution, it then takes the
    SapioWebhookResult that the class's run function returns and converts it into JSON to send back to the Sapio server
    as this webhook's final response.

    Webhook classes are tied to endpoints using the WebhookConfiguration class in the server.py file. The following
    webhook could be registered as follows: `config.register("/basic-webhook", BasicWebhook)`. This webhook could then
    be called from the system using the URL `[webhook-server-url]/basic-webhook`, where [webhook-server-url] is the
    URL of the webhook server.
    """
    def run(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # The context object contains information about where this endpoint was called from, as well as relevant
        # information to the webhook's execution. For example, if this endpoint were called from a form toolbar button,
        # then the data_record variable would contain the record from the form that the button was on.
        record: DataRecord = context.data_record

        # There are a lot of different variables in the context object that can be populated under different
        # circumstances and for different invocation points. Using ngrok, as described in the README file, to review
        # the context that is sent from these invocation points, as well as investigating the context object's
        # variables, is a good way to learn what's available and when.

        # Every Sapio webhook ends by returning a result to the server. At a bear minimum, this result must specify
        # whether the webhook passed or failed by providing True or False to the first parameter. The result object
        # is also capable of various other actions, such as directing the user to a new page in the system, displaying
        # a toaster popup with a message, refreshing data in experiments, and more.
        return SapioWebhookResult(True)


# PyCharm tip: If you hover over a class or function, you'll be given a tooltip for that item. Most classes and
# functions in our libraries have been given docstring comments that will be displayed in these tooltips, providing
# information on how the class or function behaves.
# You can ctrl+click on classes navigate to the file that they are located in, where you can also find the comment that
# gets displayed in the aforementioned tooltip. This may be helpful for more easily reading larger tooltips. Try
# ctrl+clicking on SapioWebhookResult above and locating the docstring that describes the various parameters of the
# result object.
# This ctrl+click behavior can also be used on variables to navigate to where they are initialized, or on the
# initialization of a variable to see where it is used.


class CommonsWebhook(CommonsWebhookHandler):
    """
    Sapiopycommons contains a webhook handler class that extends AbstractWebhookHandler to provide more base
    functionality. This CommonsWebhookHandler can be used to extend your webhooks. Key features of this class include:
    * An initialize function that runs before the execute function, which can be used to cleanly set up instance variables.
    * Commonly used classes are already initialized for you and available as instance variables.
    * Exception handling for sapiopycommons specific exceptions, such as SapioUserErrorException, which displays the
      exception's text as a toaster message to the user.
    * Overridable exception handling functions, allowing you to change how the aforementioned sapiopycommons exceptions
      behave.
    * Various other quality of life functions, such as what the invocation type of the webhook is.
    Going forward, all examples in this project will be extending this class.
    """
    # Perhaps you want easier access to the user object in your webhook, instead of always needing to go through the
    # context object. You could define a user variable for this class, then set it in the initialize function.
    user: SapioUser

    def initialize(self, context: SapioWebhookContext) -> None:
        self.user = context.user

    # CommonsWebhookHandler asks the extending class to implement an execute function that behaves similarly to the
    # AbstractWebhookHandler's run function.
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        #
        if not self.is_table_toolbar():
            # Most exceptions, including this one, will result in a generic message being sent to the user as a toaster
            # message. You'll want to review the webhook server's logs to determine what the exception was if a user
            # reports that they received an error message. The purpose of sending a generic message is because users
            # typically won't know what to do with an effectively random exception message.
            raise SapioException("This webhook should only be called as a table toolbar button.")

        # The instance manager, relationship manager, anr record model manager are examples of classes that are commonly
        # used and initialized by the CommonsWebhookHandler for you. More on these particular classes later.
        samples: list[SampleModel] = self.inst_man.add_existing_records_of_type(context.data_record_list, SampleModel)
        if not samples:
            # This exception, by default, sends the text in the exception to the user as a toaster message.
            # ctrl+click into CommonsWebhookHandler to see the other exceptions that are handled in its run function.
            raise SapioUserErrorException("There are no samples in the webhook context.")
        self.rel_man.load_parents_of_type(samples, PlateModel)
        for sample in samples:
            sample.set_Comments_field("Tested.")
        self.rec_man.store_and_commit()

        # As you can see here, we're able to access the user object that we set in the initialize function.
        return SapioWebhookResult(True, f"Hello, {self.user.username}.")

    # The handle_user_error_exception is what is run when a SapioUserErrorException is thrown by your webhook.
    # By default, it sends the error message as a toaster popup to the user's screen. Let's change that.
    def handle_user_error_exception(self, e: SapioUserErrorException) -> SapioWebhookResult:
        result: SapioWebhookResult | None = self.handle_any_exception(e)
        if result is not None:
            return result
        self.log_error(traceback.format_exc())
        # Instead of displaying a toaster popup that the user could potentially miss, display a popup that the user
        # must acknowledge that contains the error message. We only want to do this if we're able to send client
        # callbacks, though.
        error_msg: str = e.args[0]
        if self.can_send_client_callback():
            callback = CallbackUtil(self.context)
            callback.ok_dialog("Error", error_msg)
            return SapioWebhookResult(False)
        else:
            # If we can't send client callbacks, still send the error message in the webhook result so that it gets
            # logged in the system.
            return SapioWebhookResult(False, error_msg)


class ProjectWebhookHandler(CommonsWebhookHandler):
    """
    You can add any number of additional derivative classes to CommonsWebhookHandler. It's suggested that when starting
    a new project, you create a webhook handler for that project that all of your endpoints extend. This way you can
    make changes to the base class that will take effect in all of your endpoints.
    """
    # Perhaps there's a class you make common use of that you don't want to initialize in every one of your webhooks.
    # With a project webhook handler, you can set it to initialize here, making it accessible to all your endpoints
    # without extra effort on their part.
    rec_handler: RecordHandler

    def initialize(self, context: SapioWebhookContext) -> None:
        self.rec_handler = RecordHandler(context)

    @abstractmethod
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        pass

    # Or perhaps you want all of your endpoints to have the same override behavior for user error exceptions that was
    # shown off in the previous class.
    def handle_user_error_exception(self, e: SapioUserErrorException) -> SapioWebhookResult:
        result: SapioWebhookResult | None = self.handle_any_exception(e)
        if result is not None:
            return result
        self.log_error(traceback.format_exc())
        # Instead of displaying a toaster popup that the user could potentially miss, display a popup that the user
        # must acknowledge that contains the error message. We only want to do this if we're able to send client
        # callbacks, though.
        error_msg: str = e.args[0]
        if self.can_send_client_callback():
            callback = CallbackUtil(self.context)
            callback.ok_dialog("Error", error_msg)
            return SapioWebhookResult(False)
        else:
            # If we can't send client callbacks, still send the error message in the webhook result so that it gets
            # logged in the system.
            return SapioWebhookResult(False, error_msg)


class ProjectWebhook(ProjectWebhookHandler):
    """
    Endpoints that you register would then be classes that extend ProjectWebhookHandler.
    """
    # Your endpoint classes can still use the initialize function by calling the super class' initialize function first.
    user: SapioUser

    def initialize(self, context: SapioWebhookContext) -> None:
        super().initialize(context)
        self.user = context.user

    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # The ProjectWebhookHandler's instance variables will then be available here.
        samples: list[SampleModel] = self.rec_handler.wrap_models(context.data_record_list, SampleModel)
        if not samples:
            # This class will use the ProjectWebhookHandler's exception handling, displaying this as a dialog instead of
            # a toaster message.
            raise SapioUserErrorException("There are no samples in the webhook context.")
        # And you can still use variables specific to this endpoint.
        return SapioWebhookResult(True, f"Hello, {self.user.username}.")
