from typing import cast

from sapiopycommons.eln.experiment_handler import ExperimentHandler
from sapiopycommons.webhook.webhook_handlers import CommonsWebhookHandler
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.eln.ElnExperiment import ElnExperimentUpdateCriteria
from sapiopylib.rest.pojo.eln.ExperimentEntry import ExperimentEntry
from sapiopylib.rest.pojo.eln.ExperimentEntryCriteria import ElnFormEntryUpdateCriteria
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.utils.Protocols import ElnEntryStep, ElnExperimentProtocol

from utilities.data_type_models import SampleModel


class ElnManagerExample(CommonsWebhookHandler):
    """
    When utilizing Sapio's experiment engine to construct workflows, it is very common to need to write webhooks to
    add custom logic. With such cases, the ELN manager class from sapiopylib can be utilized to make modifications to
    an experiment and its entries.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # Similar to the data record manager, the ELN manager is already initialized within the context, making it easy
        # to make use of.
        eln_manager = context.eln_manager

        # Another similarity between the data record manager and ELN manager is the need to reduce the objects you're
        # dealing with down into IDs. For data records they get reduced to record IDs, while ELN experiments get reduced
        # to notebook experiment IDs and experiment entries to entry IDs.
        # If this webhook was invoked from within an experiment, then the context would contain an object in the
        # eln_experiment variable.
        exp_id: int = context.eln_experiment.notebook_experiment_id

        # Let's get all the records for a samples entry and wrap them as SampleModels.
        # First we have to get the entries from the experiment...
        entries: list[ExperimentEntry] = eln_manager.get_experiment_entry_list(exp_id)
        # Then find the correct one, typically keying off of the entry's name...
        mapped_entries: dict[str, ExperimentEntry] = {x.entry_name: x for x in entries}
        samples_entry: ExperimentEntry = mapped_entries.get("Samples")
        if samples_entry is None:
            raise Exception("Entry doesn't exist.")
        # Then get its ID to use with the ELN manager...
        samples_entry_id: int = samples_entry.entry_id
        # Then use the ElnManager to get the records, which returns a paged result, meaning we might need to use an
        # auto-pager...
        samples: list[DataRecord] = eln_manager.get_data_records_for_entry(exp_id, samples_entry_id).result_list
        # And finally we can wrap everything as SampleModels using the instance manager.
        sample_models: list[SampleModel] = self.inst_man.add_existing_records_of_type(samples, SampleModel)

        # Then say we want to add records to an entry. Well that's easy for table records.
        subset_entry: ExperimentEntry = mapped_entries.get("Samples Subset")
        eln_manager.add_records_to_table_entry(exp_id, subset_entry.entry_id, [x for x in samples if x.record_id % 2])
        # Notice though how we need to give the records as data records. If we only had SampleModels at this point,
        # we'd need to unwrap them back into DataRecords before passing them to the entry.

        # Form entries are a bit more difficult, though. To update a form entry, we need to use an entry update criteria
        # and grab the record ID of the record we want to set in the entry.
        form_entry: ExperimentEntry = mapped_entries.get("Sample Form")
        update_criteria = ElnFormEntryUpdateCriteria()
        update_criteria.record_id = sample_models[0].record_id
        eln_manager.update_experiment_entry(exp_id, form_entry.entry_id, update_criteria)

        # Any time we want to get options from an experiment or its entries, that also ends up being a separate call
        # that we then need to keep track of the result of.
        form_options: dict[str, str] = eln_manager.get_experiment_entry_options(exp_id, form_entry.entry_id)
        exp_options: dict[str, str] = eln_manager.get_notebook_experiment_options(exp_id)

        # And the updating of entry and experiment options requires the use of an update criteria object.
        # Using this method always replaces the option map, meaning that if you want to add to the options map, you
        # must first get the existing options, add to those, and then send the updated options back in an update
        # criteria.
        update_criteria = ElnFormEntryUpdateCriteria()
        form_options.update({"Testing": ""})
        update_criteria.entry_options_map = form_options
        eln_manager.update_experiment_entry(exp_id, form_entry.entry_id, update_criteria)

        update_criteria = ElnExperimentUpdateCriteria()
        exp_options.update({"Testing": ""})
        update_criteria.experiment_option_map = exp_options
        eln_manager.update_notebook_experiment(exp_id, update_criteria)

        return SapioWebhookResult(True)


class ProtocolExample(CommonsWebhookHandler):
    """
    Sapiopylib provides what are known as Protocol and Step classes for experiments and entries respectively to
    streamline some experiment logic operations. Many of the utilities in sapiopylib and sapiopycommons make use of
    these classes due to their ease of use.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # If your webhook is invoked from within an experiment, then a Protocol object for the experiment will already
        # be in the context.
        exp_protocol: ElnExperimentProtocol = cast(ElnExperimentProtocol, context.active_protocol)

        # Using this object, you can get all the entries in the experiment as Step objects.
        steps: list[ElnEntryStep] = exp_protocol.get_sorted_step_list()
        mapped_steps: dict[str, ElnEntryStep] = {x.get_name(): x for x in steps}

        # Protocol and step objects provide functions for streamlining various operations that were previously shown.
        samples_step: ElnEntryStep = mapped_steps.get("Samples")
        # For example, you can get records from an entry without needing to worry about the experiment or entry IDs,
        # and it'll take care of any paging for you.
        samples: list[DataRecord] = samples_step.get_records()
        # You'll still need to wrap the data records yourself, though.
        sample_models: list[SampleModel] = self.inst_man.add_existing_records_of_type(samples, SampleModel)

        # Adding records to an entry is easier as well, although you'll still need to unwrap any record models into
        # dt records.
        subset_step: ElnEntryStep = mapped_steps.get("Samples Subset")
        subset_step.add_records([x for x in samples if x.record_id % 2])

        # You can even call set_records on a form entry using a list with a single element to set a form entry's record,
        # making the updating of a form entry just as simple as a table entry when using the Step class. This same ease
        # of use is also added to attachment entries.
        form_step: ElnEntryStep = mapped_steps.get("Sample Form")
        form_step.set_records([samples[0]])

        # Protocol and Step objects also have simple getters and setters for options. But for getting options, these
        # results are not caches, meaning that repeated calls of these functions will make repeated webservice calls.
        # This method also still requires you to get the existing options, add to that, and then set the option using
        # the new mapping if you only want to add options.
        form_options: dict[str, str] = form_step.get_options()
        exp_options: dict[str, str] = exp_protocol.get_options()
        form_options.update({"Testing": ""})
        form_step.set_options(form_options)
        exp_options.update({"testing": ""})
        exp_protocol.set_options(exp_options)

        return SapioWebhookResult(True)


class ExperimentHandlerExample(CommonsWebhookHandler):
    """
    Sapiopycommons provides a class known as the experiment handler that provides an additional layer of utility around
    experiment and entry operations, including support for getting and setting entry records using record models instead
    of data records, as well as caching of webservice calls to ensure speedier webhook execution.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # The ExperimentHandler will initialize with the ELN experiment that is in the context, assuming there is one.
        # You may also pass a separate experiment as an input parameter to be used instead.
        exp_handler = ExperimentHandler(context)

        # Using the experiment handler, you can directly get record models from any entry given its name. What was about
        # seven lines to query the entries, find the particular entry you wanted, get the records from that entry, and
        # wrap those records as record models is now only one!
        samples: list[SampleModel] = exp_handler.get_step_models("Samples", SampleModel)

        # You can also add, remove, or set records to entries using the experiment handler. Unlike Protocols and Steps,
        # the experiment handler's functions can take in record models, avoiding the need for you to unwrap them.
        exp_handler.add_step_records("Samples Subset", [x for x in samples if x.record_id % 2])
        exp_handler.set_form_record("Sample Form", samples[0])

        # Just like with Protocols and Steps, you can get the options from an entry or experiment. The experiment
        # handler will cache the results of these calls, though, meaning that repeated calls will not result in repeated
        # webservice queries.
        form_options: dict[str, str] = exp_handler.get_step_options("Sample Form")
        exp_options: dict[str, str] = exp_handler.get_experiment_options()
        # The experiment handler also has methods to add to an entry or experiment's options without you needing to
        # query the existing options and add to them yourself.
        exp_handler.add_step_options("Sample Form", {"Testing": ""})
        exp_handler.add_experiment_options({"Testing": ""})

        # Just like with the classes from the previous two example files, the experiment handler has many other
        # functions you may find useful. Play around and see what you can find.

        return SapioWebhookResult(True)
