import time

from sapiopycommons.webhook.webhook_handlers import CommonsWebhookHandler
from sapiopylib.rest.pojo.DataRecord import DataRecord
from sapiopylib.rest.pojo.webhook.WebhookContext import SapioWebhookContext
from sapiopylib.rest.pojo.webhook.WebhookDirective import FormDirective
from sapiopylib.rest.pojo.webhook.WebhookResult import SapioWebhookResult
from sapiopylib.rest.utils.autopaging import QueryDataRecordsAutoPager, GetChildrenSingleRecordAutoPager

from utilities.data_type_models import NotebookDirectoryModel, RequestModel, SampleModel


# Task:
#   These two webhooks show the difference in format and runtime between data records and record models.
#   Both webhooks execute the following actions:
#       1. Query the system for an existing Notebook Directory record with a particular name.
#       2. If no Notebook Directory with the given name exists, create one.
#       3. Determine how many Request records exist under this Notebook Directory.
#       4. Create a new Request record and name it.
#       5. Create 50 new Sample records and name them.
#       6. Add the Request as a child of the Notebook Directory.
#       7. Add the Samples as children of the Request.
#       8. Commit the record field changes.
#       9. Report the runtime of the webhook to the user.
#   Your task is to configure both of these webhooks to run in the Sapio system and run them to compare their runtimes.
# Training Topics:
#   Record models
# System Config:
#    These two webhooks have already been registered with endpoints in the server.py file, but they have not been
#    configured in the system. Navigate to App Setup -> Manage Rules & Webhooks -> Webhooks and add a new webhook.
#    Choose the invocation type "Main Toolbar" and set the URL to use the base URL pointed at your local server with
#    the "/data-record-timing-example" endpoint. Create a second webhook the same way but with the
#    "/record-model-timing-example" endpoint instead..
# Relevant Classes:
#   DataRecordManager: A class with function for making API calls for creating and updating data records in the system.
#       You can acquire a DataRecordManager by using self.dr_man, context.data_record_manager, or initializing one
#       using the DataMgmtServer class.
#   QueryDataRecordsAutoPager: DataRecordManager queries return pages of results instead of returning every record in
#       one large query when there are a large number of results. Auto pager classes such as this one are used to
#       navigate through the pages of records. This particular auto pager class is used to query records by their field
#       values.
#   GetChildrenSingleRecordAutoPager: This auto pager class is used for retrieving the children of a given record.
#   RecordModelManager: This class can be used for committing record model changes to the system. You can initialize a
#       RecordModelManager yourself, or by using self.rec_man if your webhook extends CommonsWebhookHandler. The
#       store_and_commit() function is what is used to commit record model changes.
#   RecordModelInstanceManager: This class can be used to create record models in your webhook cache without creating
#       them in the system until you commit the record model changes. You can retrieve one from an existing
#       RecordModelManager, or by using self.inst_man if your webhook extends CommonsWebhookHandler. The
#       add_new_records_of_type() function is what you would use to create new sample record models.
#   RecordModelRelationshipManager: This class can be used to load the relationships between record models. Loading
#       the children or parents of a given list of record models queries the system for those relationships and stores
#       them in the record model cache, allowing you to then retrieve the related records from a record model using the
#       get_child/get_children/get_parent/get_parents functions. You can retrieve a relationship manager from an
#       existing RecordModelManager, or by using self.rel_man if your webhook extends CommonsWebhookHandler.
# Other Info:
#   In this example, the record model webhook should run about 30% faster than the data record webhook. This
#   difference comes down to the additional API calls that need to be made when using data records, namely the
#   add_children_for_record calls that occur in steps 6 and 7 of the data records webhook, whereas the record models
#   webhook makes a singular API call to complete the tasks of steps 6, 7, and 8. Even with these simple webhooks,
#   there is a considerable gain in performance for using record models. For more complex webhooks with more information
#   to commit, the performance gain could be even larger. Aside from the performance difference, the record models
#   webhook is easier to write, with less lines and less verbosity within the existing lines.


class DataRecordTimingExample(CommonsWebhookHandler):
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # Measure the runtime of this webhook.
        start: float = time.perf_counter()

        # 1. Query the system for an existing Notebook Directory record with a particular name.
        directory_name: str = "Data Record Examples"
        pager = QueryDataRecordsAutoPager(NotebookDirectoryModel.DATA_TYPE_NAME,
                                          NotebookDirectoryModel.DIRECTORYNAME__FIELD_NAME.field_name,
                                          [directory_name],
                                          self.user)
        directories: list[DataRecord] = pager.get_all_at_once()

        # 2. If no Notebook Directory with the given name exists, create one.
        if not directories:
            directory: DataRecord = self.dr_man.add_data_record(NotebookDirectoryModel.DATA_TYPE_NAME)
            directory.set_field_value(NotebookDirectoryModel.DIRECTORYNAME__FIELD_NAME.field_name, directory_name)
            # 3. Determine how many Request records exist under this Notebook Directory.
            request_count: int = 1
        else:
            directory: DataRecord = directories[0]
            # 3. Determine how many Request records exist under this Notebook Directory.
            pager = GetChildrenSingleRecordAutoPager(directory.record_id,
                                                     RequestModel.DATA_TYPE_NAME,
                                                     self.user)
            existing_requests: list[DataRecord] = pager.get_all_at_once()
            request_count: int = len(existing_requests) + 1

        # 4. Create a new Request record and name it.
        request: DataRecord = self.dr_man.add_data_record(RequestModel.DATA_TYPE_NAME)
        request.set_field_value(RequestModel.REQUESTNAME__FIELD_NAME.field_name, f"Data Record Request {request_count}")

        # 5. Create 50 new Sample records and name them.
        samples: list[DataRecord] = self.dr_man.add_data_records(SampleModel.DATA_TYPE_NAME, 50)
        for i, sample in enumerate(samples, start=1):
            sample.set_field_value(SampleModel.OTHERSAMPLEID__FIELD_NAME.field_name, f"Example Sample {request_count}-{i}")

        # 6. Add the Request as a child of the Notebook Directory.
        self.dr_man.add_children_for_record(directory, [request])
        # 7. Add the Samples as children of the Request.
        self.dr_man.add_children_for_record(request, samples)
        # 8. Commit the record field changes.
        self.dr_man.commit_data_records([directory, request] + samples)

        # 9. Report the runtime of the webhook to the user.
        end: float = time.perf_counter()
        self.callback.ok_dialog("Data Record Timing", f"Total runtime: {(end - start) * 1000:.0f}ms")
        return SapioWebhookResult(True, directive=FormDirective(directory))


class RecordModelTimingExample(CommonsWebhookHandler):
    def execute(self, context: SapioWebhookContext) -> SapioWebhookResult:
        # Measure the runtime of this webhook.
        start: float = time.perf_counter()

        # 1. Query the system for an existing Notebook Directory record with a particular name.
        directory_name: str = "Record Model Examples"
        directories: list[NotebookDirectoryModel] = self.rec_handler.query_models(NotebookDirectoryModel,
                                                                                  NotebookDirectoryModel.DIRECTORYNAME__FIELD_NAME,
                                                                                  [directory_name])
        # 2. If no Notebook Directory with the given name exists, create one.
        if not directories:
            directory: NotebookDirectoryModel = self.inst_man.add_new_record_of_type(NotebookDirectoryModel)
            directory.set_DirectoryName_field(directory_name)
            # 3. Determine how many Request records exist under this Notebook Directory.
            request_count: int = 1
        else:
            directory: NotebookDirectoryModel = directories[0]
            # 3. Determine how many Request records exist under this Notebook Directory.
            self.rel_man.load_children_of_type([directory], RequestModel)
            existing_requests: list[RequestModel] = directory.get_children_of_type(RequestModel)
            request_count: int = len(existing_requests) + 1

        # 4. Create a new Request record and name it.
        request: RequestModel = self.inst_man.add_new_record_of_type(RequestModel)
        request.set_RequestName_field(f"Record Model Request {request_count}")

        # 5. Create 50 new Sample records and name them.
        samples: list[SampleModel] = self.inst_man.add_new_records_of_type(50, SampleModel)
        for i, sample in enumerate(samples, start=1):
            sample.set_OtherSampleId_field(f"Example Sample {request_count}-{i}")

        # 6. Add the Request as a child of the Notebook Directory.
        directory.add_child(request)
        # 7. Add the Samples as children of the Request.
        request.add_children(samples)
        # 8. Commit the record field changes.
        self.rec_man.store_and_commit()

        # 9. Report the runtime of the webhook to the user.
        end: float = time.perf_counter()
        self.callback.ok_dialog("Record Model Timing", f"Total runtime: {(end - start) * 1000:.0f}ms")
        return SapioWebhookResult(True, directive=FormDirective(directory.get_data_record()))
