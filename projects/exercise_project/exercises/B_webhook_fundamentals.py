from sapiopycommons.webhook.webhook_handlers import CommonsWebhookHandler
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult

from utilities.data_type_models import SampleModel, SubjectModel


# This file contains webhook examples for counting selected records and for linking a Sample to a Subject.


class ContextCounter(CommonsWebhookHandler):
    """
    Exercise 1: A basic webhook that just counts how many records are in the context and returns that count to the user
    using a client callback. For table toolbar invoked webhooks like this, the records in the context are the ones
    that the user selected.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        self.callback.ok_dialog("Notice", f"You selected {len(context.data_record_list)} records.")
        return SapioWebhookResult(True)


class SubjectLinkSolution(CommonsWebhookHandler):
    """
    Exercise 2: An on save webhook that queries the system for a Subject record using the name from the Subject Name
    field of a changed Sample record. If no Subject record exists with the given name, then create one. Side link this
    Subject record to the Sample record.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # Get the changed Samples from the context.
        samples: list[SampleModel] = self.rule_handler.get_models(SampleModel)

        # Collect the Subject Name field value for every sample in the context. Skip empty values.
        subject_names: list[str] = [x.get_C_SubjectName_field() for x in samples if x.get_C_SubjectName_field()]

        # Query the system for the Subject records that match the collected Subject Name field values.
        # Map each Subject to a dictionary where the key is the Subject's name. This will make it easy to determine
        # which Subject record we want to side link to later.
        subjects: dict[str, list[SubjectModel]] = self.rec_handler.query_and_map_models(SubjectModel,
                                                                                        SubjectModel.SUBJECTNAME__FIELD_NAME,
                                                                                        subject_names)

        # The Subject side link is located on this field. Load the existing Subject side links to the Samples in the
        # context. This is necessary for updating the Sample side links.
        subject_link: str = SampleModel.C_SUBJECTLINK__FIELD_NAME.field_name
        self.rel_man.load_forward_side_links_of_type(samples, subject_link)

        # Now iterate over each Sample in the context and update its Subject side link.
        for sample in samples:
            subject_name: str = sample.get_C_SubjectName_field()
            # If the Subject Name is empty, then the Sample should have no linked subject.
            if not subject_name:
                sample.set_C_SubjectLink_field(None)
                continue

            # Get the list of Subject records that match this Subject Name.
            subjects: list[SubjectModel] | None = subjects.get(subject_name)
            if subjects:
                # If a subject exists for a matching Subject Name, side link it to the Sample.
                # There could theoretically be multiple Subjects with the same name. In this case, we'll just side link
                # to the first one, but if this were a real world situation, this would be a good time to ask for
                # clarification on the requirements for what to do in this scenario.
                subject: SubjectModel = subjects[0]
            else:
                # If a Subject doesn't exist for a matching Subject Name, create one and then side link it to the
                # Sample. Remember to set the Subject Name of the newly created Subject.
                subject: SubjectModel = self.rec_handler.add_model(SubjectModel)
                subject.set_SubjectName_field(subject_name)

            # Side link the Sample to the located or created Subject.
            sample.set_side_link(subject_link, subject)

        # Commit your changes to the system.
        self.rec_man.store_and_commit()
        return SapioWebhookResult(True)


class SubjectLinkBroken(CommonsWebhookHandler):
    """
    Exercise 3: This webhook is the same as the one above, except it has been tweaked with an intentional mistake.
    Comments have only been added around these changes. When this comment is run, an exception will occur. The cause
    and log of this exception can bt found in the system by navigating to App Setup -> Manage Rules & Webhooks
    -> On Save Rules -> Click on the enabled rule that calls this webhook -> Click on the URL for the webhook
    -> Click on "View Logs" -> Click on one of the webhook executions where the result is Result Failed -> Click on the
    "Download Log" button that appears on the right side of the dialog. This will download a text file containing the
    Sapio server's logs of the webhook execution, including information about why the commit was rejected. Due to using
    the CommonsWebhookHandler class as a base for this webhook, the webhook server will also have sent additional
    logging information back to the Sapio server that is stored in the same text file.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        samples: list[SampleModel] = self.rule_handler.get_models(SampleModel)

        subject_names: list[str] = [x.get_C_SubjectName_field() for x in samples if x.get_C_SubjectName_field()]
        subjects: dict[str, list[SubjectModel]] = self.rec_handler.query_and_map_models(SubjectModel,
                                                                                        SubjectModel.SUBJECTNAME__FIELD_NAME,
                                                                                        subject_names)

        # Although the requirement is to side link the matching Subject, this webhook instead attempts to make the
        # Subject a child of the Sample. This load function will not cause an exception, but it is incorrect for the
        # requirement.
        self.rel_man.load_children_of_type(samples, SubjectModel)
        for sample in samples:
            subject_name: str = sample.get_C_SubjectName_field()
            if not subject_name:
                # This will cause an exception if the Sample has no child Subject, as the return result of
                # get_child_of_type will be None, and remove_child expects a non-None value.
                sample.remove_child(sample.get_child_of_type(SubjectModel))
                continue

            subjects: list[SubjectModel] | None = subjects.get(subject_name)
            if subjects:
                subject: SubjectModel = subjects[0]
            else:
                subject: SubjectModel = self.rec_handler.add_model(SubjectModel)
                subject.set_SubjectName_field(subject_name)
            # This line is attempting to add the Subject as a child of the Sample instead of as a side link.
            sample.add_child(subject)

        # If the add_child function was called above, then this line will throw an exception. The server will reject
        # the commit because Subjects are not a valid child data type of Sample.
        self.rec_man.store_and_commit()
        return SapioWebhookResult(True)
