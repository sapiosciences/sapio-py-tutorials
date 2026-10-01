from sapiopylib.rest.DataMgmtService import DataMgmtServer
from sapiopylib.rest.DataRecordManagerService import DataRecordManager
from sapiopylib.rest.User import SapioUser
from sapiopylib.rest.pojo.DataRecord import DataRecord

# Task:
#   Use the Sapio REST API to add a sample to your system, then update its field values.
#   The code below is structured as a script that is run on demand, similar to how an external integration would behave.
#   This is not structured as a webhook that can be called from within the Sapio system.
# Training Topics:
#   REST API
#   Using sapiopylib
# System Config:
#   In the system, navigate to App Setup -> User Manager -> Add User and check the "API User Account" box if you have
#   not already created an API user. The script below logs in as this user, so it only has access to what that user
#   has access to.
# Relevant Classes:
#   SapioUser: This class is initialized with the application URL and the login credentials necessary to interact with
#      the webservice API for the given URL.
#   DataMgmtServer: This is a class with static functions for initializing manager/service classes from sapiopylib.
#       These classes utilize a SapioUser object to determine what system to send REST API requests to, and to authorize
#       the requests.
#   DataRecordManager: A class with function for making API calls for creating and updating data records in the system.
#   DataRecord: A representation of a record in the system. Records have a record ID, data type name, and a dictionary
#       of field names and values. DataRecord objects can be manipulated in code, and the changes made to each object
#       can then be sent back to the server as a commit via the REST API, resulting in the record being updated in the
#       system.
# Other Info:
#   None.

# TODO: Replace the host below with the URL of your own Sapio system, keeping the /webservice/api suffix. The REST API
#  endpoints are located under that path.
url: str = "https://your-sapio-system.example.com/webservice/api"
# TODO: Input the username and password of an API user that exists in your system.
username: str = ""
password: str = ""

# Construct a user object using the provided credentials.
# Appending /webservice/api to the provided URL, as this is where the REST API endpoints are located.
print(f"Creating SapioUser object to communicate with the system {url} with the user {username}.")
user = SapioUser(url, username=username, password=password)

# Use the DataMgmtServer to instantiate a DataRecordManager, which can be used to call data record endpoints on the
# server.
dr_man: DataRecordManager = DataMgmtServer.get_data_record_manager(user)

# Create a Sample record in the system and set some of its fields.
print("Creating a sample in the system.")
# This add_data_record function call sends a REST API request to the system to create a new Sample record. The returned
# result is a DataRecord object representing the new Sample in the system with default field values.
sample: DataRecord = dr_man.add_data_record("Sample")
sample.set_field_value("OtherSampleId", f"{username}'s API Sample")
sample.set_field_value("Volume", 10.)
sample.set_field_value("Concentration", 20.)

# Commit the field changes to the server.
print("Committing field changes for this sample to the system.")
# This commit_data_records function call sends a second REST API request to the system, containing the DataRecord object
# from the first call, but now with updated fields.
dr_man.commit_data_records([sample])

# TODO: Run a search for samples in the system and observe how the above sample has been created. You can modify the
#  values of the above fields and re-run this script to create another sample each time.
print("Finished")
