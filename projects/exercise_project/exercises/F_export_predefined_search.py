from typing import Any

from sapiopycommons.files.file_writer import FileWriter
from sapiopycommons.general.custom_report_util import CustomReportUtil
from sapiopycommons.webhook.webhook_handlers import CommonsWebhookHandler
from sapiopylib.rest.WebhookService import SapioWebhookContext, SapioWebhookResult


# Task:
#   The webhook below has been provided to you to practice the setting up of a webhook. You will need to register an
#   endpoint for this webhook in the server.py file using the config.register() function. Once this webhook class has
#   been registered to an endpoint, running the webhook server and calling that endpoint from within the Sapio system
#   will run this code.
# Training Topics:
#   Running a simple webhook
#   Custom reports
#   Creating files
# System Config:
#   In order for the below code to function, you must have a predefined search in the system that matches the name of
#   the second parameter to the CustomReportUtil.run_system_report call. In order to create a custom report, navigate
#   to App Setup -> Data Designer -> Pick the data type you wish to make a predefined search for -> Click on "Predefined
#   Search" -> Add a new predefined search with a unique name.
#
#   Then navigate to App Setup -> Manage Rules & Webhooks -> Webhooks and add a new webhook. Choose the invocation type
#   "Main Toolbar" and use the endpoint name you defined for this class in the server.py file.
# Relevant Classes:
#   CustomReportUtil: A sapiopycommons utility class for returning the results of custom reports.
#   FileWriter: A sapiopycommons utility class for generating CSV files from dictionaries.
#   ClientCallback: The base class used for sending client callback requests. You can initialize a ClientCallback
#       yourself, or get one from the DataMgmtServer. There are multiple methods that you could use to request an
#       integer from the user, but consider using the show_input_dialog() function.
#   CallbackUtil: A utility class for streamlining client callback requests. If the base class of your webhook is
#       CommonsWebhookHandler (which it is here), then self.callback provides you with a CallbackUtil.
# Other Info:
#   Custom report, advanced search, system report, predefined search, and saved search are all names for similar
#   concepts. The name most often seen in code is "custom report", while in the client these types of searches are
#   referred to as "advanced searches". A "saved search" is an advanced search created by a user in the system and saved
#   for uses in the "Saved Searches" section under the save menu on the sidebar in the system. These searches cannot be
#   used in code, as they do not enforce that the name of the search must be unique, and therefore there is no unique
#   means of using them in code. "Predefined searches" are advanced searches created by admins in the data designer, and
#   these must have a unique name that will be enforced by the client. That is, if you make a "MouseSearchExample"
#   predefined search for the Sample data type, you won't be allowed to make another search with that same name for any
#   other data type. This means that we can query the searches with these unique names using the API. The term "system
#   report" is used in code to refer to these predefined searches.

class ExportPredefinedSearch(CommonsWebhookHandler):
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # Run a system report defined in the system. Note that if you named the predefined search something different
        # from what is listed here, this line will fail to run. Either change the predefined search to match the name
        # shown here, or change the name used here to match the search in the system.
        report_results: list[dict[str, Any]] = CustomReportUtil.run_system_report(context, "MouseSearchExample")

        # Check if there are any results.
        if not report_results:
            return SapioWebhookResult(True, "No results found for this search.")

        # Extract header names from the first result.
        headers: list[str] = list(report_results[0].keys())

        # Create a CSV writer with the extracted headers.
        writer = FileWriter(headers)

        # Iterate over the results and add each row to the CSV.
        for result in report_results:
            writer.add_row_dict(result)

        # Build the CSV file contents.
        results_csv: str = writer.build_file()

        # Prompt the user to download this CSV file.
        # You could theoretically do something else with this file, such as send it to an external system with an HTTP
        # request, or send it to a file bridge directory.
        self.callback.write_file("AdvancedMouse.csv", results_csv)

        # Return a successful webhook result.
        return SapioWebhookResult(True)
