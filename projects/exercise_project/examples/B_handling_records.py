from sapiopycommons.general.time_util import TimeUtil
from sapiopycommons.recordmodel.record_handler import RecordHandler
from sapiopycommons.webhook.webhook_handlers import CommonsWebhookHandler
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.utils.MultiMap import SetMultimap
from sapiopylib.rest.utils.autopaging import GetParentsListAutoPager, QueryDataRecordsAutoPager
from sapiopylib.rest.utils.recordmodel.RecordModelManager import RecordModelManager
from sapiopylib.rest.utils.recordmodel.RelationshipPath import RelationshipPath
from sapiopylib.rest.utils.recordmodel.ancestry import RecordModelAncestorManager

from utilities.data_type_models import SampleModel, PlateModel, BatchModel, RequestModel


# For basics on querying data records, read through the following tutorial page:
# https://github.com/sapiosciences/sapio-py-tutorials/blob/master/02_query_data_records.ipynb
# For basics on manipulating data records, read through the following tutorial page:
# https://github.com/sapiosciences/sapio-py-tutorials/blob/master/03_manipulate_data_records.ipynb
# For basics on record models, read through the following tutorial page:
# https://github.com/sapiosciences/sapio-py-tutorials/blob/master/10_python_record_models.ipynb


class DataRecordsExample(CommonsWebhookHandler):
    """
    Data records are the first object type you'll encounter when dealing with records from the system. They're easy to
    get your hands on, but they can be difficult to work with given that they are data type agnostic. That is, a
    data record could be any data type, and therefore does not have data type specific functions. The data record
    manager used to get data records can also require verbose code due to paging.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # A data record manager is already initialized in the context objet provided to every webhook.
        dr_man = context.data_record_manager

        # If you're using CommonsWebhookHandler, the data record manager is also an instance variable, and are therefore
        # accessible via the "self" variable.
        # Data record managers return pages of results. If there are more records than can fit in a page, this
        # result_list won't contain every record you want. In this case we're only querying three records, so the page
        # size is not an issue, but it may be something you need to keep in mind for larger queries.
        samples: list[DataRecord] = self.dr_man.query_data_records("Sample", "SampleId", ["00000", "00001", "00001"])\
            .result_list

        # Since data records are type agnostic, in order to get and set field values, you need to remember the exact
        # field names, or cross-reference your code with the data designer in the system.
        for sample in samples:
            # Notably, these get/set field functions return/take an Any parameter for the field value. There's no
            # telling from a DataRecord what the object type of a field value is; that's up to you to remember or
            # look up.
            sample_id: str = sample.get_field_value("SampleId")
            sample_status: str = sample.get_field_value("ExemplarSampleStatus")
            print(f"Updating sample {sample_id} with status {sample_status}.")
            sample.set_field_value("Volume", 10)
            sample.set_field_value("Concentration", 20)

        # Committing data record field changes to the server is also done through the data record manager. Only after
        # you have called commit_data_records on a list of data records will any changes you made to the fields of those
        # records take effect in the system.
        self.dr_man.commit_data_records(samples)

        # You can also create new records through the data record manager. An important note though is that this
        # also creates the record in the system at the moment of calling this function. This means that if for some
        # reason this webhook were to fail later on, this record would exist in an incomplete state in the system.
        new_plate: DataRecord = self.dr_man.add_data_record("Plate")

        # You can also update record relationships using the data record manager.
        # Notably, the data record manager has no way to add parents of a data type. You can only add children, and must
        # swap your inputs based on which record you want to be the parent and which you want to be the child.
        self.dr_man.add_children_for_record(new_plate, samples)

        # You can also query relationships, although you will need to convert your records to record IDs for such
        # queries. The keys in this dict are the record IDs of the records you requested the children of.
        # Note that this query is also a paged result, same as the query at the start of this example.
        aliquots: dict[int, list[DataRecord]] = self.dr_man.get_children_list([x.record_id for x in samples], "Sample")\
            .result_map

        # In cases where paging is a concern, you could make use of an auto-pager instead of directly calling the data
        # record manager query methods. Auto-pagers will take care of any paging for you.
        requests: SetMultimap[int, DataRecord] = GetParentsListAutoPager([x.record_id for x in samples], "Sample",
                                                                         "Request", context.user).get_all_at_once()
        return SapioWebhookResult(True)


class RecordModelsExample(CommonsWebhookHandler):
    """
    Record models, unlike data records, have a sense of what data type they are. This means that they contain functions
    for getting and setting the specific fields on the record. This way you're safeguarded against typos in field names,
    since an incorrect function name would be highlighted by your IDE while an incorrect field name string isn't. Using
    your IDE's function suggestions can also help lessens the burden of remembering the exact names of fields in the
    system.

    Making use of record models also results in improved webservice call batching, as committing changes made to record
    models will commit relationship updates, record creation, and record field updates all in a single call as opposed
    to the multiple separate calls it would take to achieve the same things with the data record manager.

    Using record models and record model managers is also generally less verbose to achieve the same thing as compared
    to using data records and the data record manager, resulting in quicker turn around times for producing a webhook.

    An important note to make is that record models have additional overhead compared to data records due to the caching
    that is done for them. So although data records can be more difficult to work with, their minimal overhead compared
    to record models makes them useful in extremely high volume applications. Such applications are typically few and
    far between, though, so for a vast majority of cases you will want to make use of record models.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # Unlike the data record manager, which is already initialized in the context, you'll need to initialize your
        # own record model managers.
        rec_man = RecordModelManager(context.user)
        inst_man = rec_man.instance_manager
        rel_man = rec_man.relationship_manager
        an_man = RecordModelAncestorManager(rec_man)
        # But as with the data record manager, these managers are already initialized as instance variables by
        # CommonsWebhookHandler.

        # In order to get record models, you'll first need to start from data records. Let's use the same query as in
        # the data records example, except this time using the auto pager, although you could still make use of the
        # data record manager directly to make this query.
        samples: list[DataRecord] = QueryDataRecordsAutoPager("Sample", "SampleId", ["00000", "00001", "00001"],
                                                              context.user).get_all_at_once()
        # With data records in hand, you can use the record model instance manager to "wrap" data records with a
        # record model wrapper. These wrappers can be generated in the system by going to App Setup -> Manage Rules &
        # Webhooks -> Webservice API and clicking the Generate Python Record Model Wrappers for System Data Types
        # button. This will
        # generate a Python file that you can import into your project, containing a class for each data type in your
        # system with the name [data type name]Model. Given that we queried samples, we then want to make use of the
        # SampleModel wrapper.
        sample_models: list[SampleModel] = self.inst_man.add_existing_records_of_type(samples, SampleModel)

        # Now that the samples are wrapped as record models, we have specific functions for each of the fields on the
        # sample data type.
        for sample in sample_models:
            # Since record models have specific functions for each field, these functions can also tell you what the
            # object type of the field value is. In this case, we know from the function signatures that these two
            # functions return strings.
            sample_id: str = sample.get_SampleId_field()
            sample_status: str = sample.get_ExemplarSampleStatus_field()
            print(f"Updating sample {sample_id} with status {sample_status}.")
            # We also know when setting field values what the object type of the input should be.
            sample.set_Volume_field(10)
            # This means that the IDE will warn you if you're setting a field to the wrong object type, such as
            # setting a string value to a float field.
            sample.set_Concentration_field("20")

        # You can create new record models using the instance manager, but unlike the data record manager, this doesn't
        # make a webservice call and create the record in the system. This means that should this webhook fail part
        # way through, this will not leave an incomplete record in the system.
        new_plate: PlateModel = self.inst_man.add_new_record_of_type(PlateModel)

        # Record model objects can directly add parents or children from themselves instead of needing a separate
        # manager class to do that.
        new_plate.add_children(sample_models)
        # And unlike with the data record manager, you have access to functions for adding parents of a record.
        new_batch: BatchModel = self.inst_man.add_new_record_of_type(BatchModel)
        new_plate.add_parent(new_batch)

        # You can also get parent/child relationships directly from a record, but you must first use the
        # relationship manager to load the records into your cache. In this case, the relationship manager does all
        # the querying and potential paging itself you would have needed to handle when doing this with the data record
        # manager.
        self.rel_man.load_children_of_type(sample_models, SampleModel)
        aliquots: dict[SampleModel, list[SampleModel]] = {x: x.get_children_of_type(SampleModel) for x in sample_models}

        # Since the parents/children of a record can be accessed directly from its record model, you don't necessarily
        # need to deal with dictionaries of relationships. You could instead just load the relationships, then grab
        # the related record(s) as you iterate over a list.
        self.rel_man.load_parents_of_type(sample_models, RequestModel)
        for sample in sample_models:
            request: RequestModel | None = sample.get_parent_of_type(RequestModel)
            if request:
                request.set_CompletedDate_field(TimeUtil.now_in_millis())
                print(f"Sample {sample.get_SampleId_field()} is under request {request.get_RequestId_field()}")
            else:
                print(f"Sample {sample.get_SampleId_field()} is not under a request.")

        # When you want to load a large number of relationships at once, you can make use of the load_path_of_type
        # function of the relationship manager. The relationship path class that you provide as input then defines
        # the different types of relationships to load, using the input list of record models as a starting point
        # to load from.
        # Perhaps you have a pool sample, and you want to find the original samples that led to that pool, but there
        # are a number of aliquots between the pool and the original sample that you must load and traverse through.
        # Using a path load, that would look like this:
        pool: SampleModel = self.inst_man.add_existing_record_of_type(context.data_record, SampleModel)
        self.rel_man.load_path_of_type([pool], RelationshipPath().parent_type(SampleModel)
                                       .parent_type(SampleModel).parent_type(SampleModel))
        parents: list[SampleModel] = pool.get_parents_of_type(SampleModel)
        grandparents: list[SampleModel] = []
        for parent in parents:
            grandparents.extend(parent.get_parents_of_type(SampleModel))
        sources: list[SampleModel] = []
        for grandparent in grandparents:
            sources.extend(grandparent.get_parents_of_type(SampleModel))

        # And now let's finally commit all the record model changes made during this webhook. This will update any
        # fields we set, create the new plate and batch, and update the relationships between records that we set all
        # in one go. If we were using the data record manager, that would be at least four different webservice calls.
        self.rec_man.store_and_commit()
        return SapioWebhookResult(True)


class RecordHandlerExample(CommonsWebhookHandler):
    """
    While using record models can be less verbose than using data records, there are a few actions that require multiple
    steps to achieve that could be collapsed into one function call. That's where the record handler class from
    sapiopycommons comes in.

    The record handler is effectively a combination data record manager and record model instance manager that
    streamlines various common record model related actions into single, shorter functions.
    """
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # Let's initialize a record handler and use it to streamline some of the actions from the previous webhook
        # example.
        rec_handler = RecordHandler(context)

        # The record handler has various methods for querying records and then returning them as wrapped record models,
        # instead of requiring you to query and wrap separately.
        # This particular call also shows off another feature of record model wrappers, that being that they contain
        # constants that can be used to retrieve the name and type of each field on a data type, in this case retrieving
        # the SampleId field's name.
        samples: list[SampleModel] = rec_handler.query_models(SampleModel, SampleModel.SAMPLEID__FIELD_NAME.field_name,
                                                              ["00000", "00001", "00001"])

        # The record handler can also be used to traverse long hierarchies in a single call, assuming you only care
        # about the endpoint. Using the same pool sources example from the previous webhook, let's say that you only
        # cared about the source samples and didn't want to bother with every record in between. In that case, you can
        # use one of the record handler's path traversal functions. First, create a relationship path to load a series
        # of relationships to a list of source records, then call a path traversal function using that same path
        # to retrieve the records at the end of the path.
        pool: SampleModel = self.inst_man.add_existing_record_of_type(context.data_record, SampleModel)
        path = RelationshipPath().parent_type(SampleModel).parent_type(SampleModel).parent_type(SampleModel)
        self.rel_man.load_path_of_type([pool], path)
        relationships: dict[SampleModel, list[SampleModel]] = rec_handler.get_branching_path([pool], path, SampleModel)
        sources: list[SampleModel] = relationships.get(pool)

        # The record handler also has various other quality of life functions for you to make use of.
        oldest_source: SampleModel = rec_handler.get_oldest_record(sources)
        newest_source: SampleModel = rec_handler.get_newest_record(sources)
        total_source_volume: float = rec_handler.sum_of_field(sources, "Volume")
        sources_by_status: dict[str, list[SampleModel]] = rec_handler.map_by_field(sources, SampleModel.EXEMPLARSAMPLESTATUS__FIELD_NAME.field_name)
        # Play around with the record handler to see what else it offers.

        return SapioWebhookResult(True)
