# Task:
#   Create a selection list webhook that populates a new selection list field on a sample. The contents of the list
#   is up to you. Make it so that the contents of the list changes depending on the value of a field on the sample.
#   For example, perhaps the selection list has a different set of options depending on the value of the
#   ExemplarSampleStatus field. You can then use the button from the previous exercise to change the sample's status,
#   then observe how that changes the selection list values according to how your webhook defined them.
# Training Topics:
#   Selection list webhooks
# Webhook Context:
#   Like form toolbar buttons, selection list webhooks contain the data record and data type of the record that the
#   selection list field is on. They additionally have a context.data_field_name variable that contains the name of the
#   selection list field that the webhook was invoked from.
# System Config:
#   Create a new webhook and select "Data Type Record Selection List Field" as the invocation type.
#   In the Data Designer, create a new field on sample, set its field type to "Selection List", configure the field to
#   use "Populate List Using: Webhook" and select the webhook you configured. Then go to Layouts and add this new field
#   to the sample layout. Confirm that you can see the new field when you go to a sample record after making the layout
#   change.
# Relevant Classes:
#   SapioWebhookResult: Every webhook must end by returning a SapioWebhookResult object. At the very least this object
#       must return True or False to let the server know whether the webhook passed or failed. We've already previously
#       discussed the directive and display_text parameters, but there are various other parameters for other purposes.
#       In this case, we'll be making use of the list_values parameter. This parameter takes a list of strings that is
#       used to populate the list that is displayed to the user for the selection list field. That's all there is to it.
# Other Info:
#   Given how simple this webhook is, try also creating the webhook class from scratch.

# TODO: Create and implement the webhook.
