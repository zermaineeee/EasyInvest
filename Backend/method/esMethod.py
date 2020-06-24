import uuid
from datetime import *

from elasticsearch_dsl import Search


# Create new indices
def create_new_indices(client, index):
    try:
        client.indices.create(index)
        return "Create Indices: [" + index + "]"
    except:
        if client.indices.exists(index):
            return "Error - Already Created: [" + index + "]"
        else:
            return "Error - Fail to create indices: [" + index + "]"


# Delete indices
def delete_indices(client, index):
    try:
        client.indices.delete(index)
        return "Deleted Indices: [" + index + "]"
    except:
        if client.indices.exists(index):
            return "Error - Fail to create indices: [" + index + "]"
        else:
            return "Error - Indices does not exisit: [" + index + "]"


# Index single entry json without defining UUID, must be in a list
def create_without_uuid(client, index, json_data):
    client.index(index=index, doc_type="_doc", body=json_data, refresh=True)
    return "Index jsonArray for Indices: [" + index + "]"


# Get all data from indices
def match_all_from_indices(client, index):
    try:
        s = Search()[0:9999].using(client).index(index).query("match_all")
        response = s.execute()
        response_list = []

        for hit in response.hits:
            hits_dict = {}
            hit_uuid = hit.meta.id
            hit_body = hit.to_dict()
            hits_dict['uuid'] = hit_uuid
            hits_dict['body'] = hit_body
            response_list.append(hits_dict)

        if len(response_list) == 0:
            return "Error - SearchError: No match found"
        else:
            return response_list
    except:
        raise Exception('Error - SearchError: Invalid Syntax / Indices')


# Index single entry json with defining UUID
def create_with_uuid(client, index, json_data, uuid):
    client.index(index=index, doc_type="_doc", id=uuid, body=json_data, refresh=True)
    return "Index jsonArray using UUID for Indices: [" + index + "] & [" + uuid + "]"


# Add asset to existing user with asset by using the UUID
def add_asset(client, index, json_data, user_uuid):
    s = Search().using(client).index(index).query("match", _id=user_uuid)
    response = s.execute()
    if len(response.hits) > 0:
        # Should only be 1 result cause search by UUID
        for hit in response.hits:
            # Get the asset list
            asset_list = hit.to_dict()["asset"]

        to_insert = json_data["asset"]
        for element in to_insert:
            # Create UUID for asset
            asset_uuid = {"uuid": str(uuid.uuid1())}
            # Append uuid to asset
            element.update(asset_uuid)
            # Add the asset to be stored in new list
            asset_list.append(element)

        doc_update = {
            "doc": {
            }
        }
        doc_update['doc']['asset'] = asset_list
        client.update(index=index, doc_type='_doc', id=user_uuid, body=doc_update, refresh=True)
        return "Added Asset with UUID tag: [" + index + "] & [" + user_uuid + "]"
    else:
        to_insert = json_data["asset"]
        update_list = []
        for element in to_insert:
            # Create UUID for asset
            asset_uuid = {"uuid": str(uuid.uuid1())}
            # Append uuid to asset
            element.update(asset_uuid)
            # Add the asset to be stored in new list
            update_list.append(element)
        json_data["asset"] = update_list
        create_with_uuid(client=client, index=index, json_data=json_data, uuid=user_uuid)
        # create_with_uuid(client=client, index=index, json_data=e, uuid)
        return "Created and Added Asset with UUID tag: [" + index + "] & [" + user_uuid + "]"


# Delete asset to existing user with asset by using the UUID
def delete_asset(client, index, json_data, uuid):
    # Get the doc that store the asset data using UUID
    data = client.get(index=index, doc_type="_doc", id=uuid)["_source"]
    # Get the asset list
    asset_list = data["asset"]

    to_delete = json_data["asset"]

    # Delete asset, using the whole element, but can be change to using UUID only
    for element in to_delete:
        if asset_list.count(element) > 0:
            asset_list.remove(element)
        else:
            return "Error - Fail Delete Asset UUID (Asset does not exist): [" + index + "] index of UUID [" + uuid + "]"

    doc_update = {
        "doc": {
        }
    }
    doc_update['doc']['asset'] = asset_list
    client.update(index=index, doc_type='_doc', id=uuid, body=doc_update, refresh=True)
    return "Delete Asset with UUID: [" + index + "] index of UUID [" + uuid + "]"


# Update asset, amount field can only be updated with 1 element.
def update_asset(client, index, json_data, user_uuid):
    today = date.today()
    # Today month/year datetime
    str_today_month_year = str(today.month) + "/" + str(today.year)
    today_month_year = datetime.strptime(str_today_month_year, "%m/%Y")
    # 1 year ago Today month/year datetime
    str_today_minus1year_month_year = str(today.month) + "/" + str(today.year - 1)
    today_minus1year_month_year = datetime.strptime(str_today_minus1year_month_year, "%m/%Y")

    # Get the doc that store the asset data using UUID
    data = client.get(index=index, doc_type="_doc", id=user_uuid)["_source"]
    # Get the asset list
    asset_list = data["asset"]
    # Get asset to be updated
    to_update = json_data["asset"][0]
    to_update_uuid = to_update["uuid"]
    to_update_amount = to_update["amount"][0]

    # Get datetime in need to update to compare with today datetime
    to_update_amount_date = datetime.strptime(to_update_amount["date"], "%d/%m/%Y").date()
    str_update_date_month_year = str(to_update_amount_date.month) + "/" + str(to_update_amount_date.year)
    to_update_amount_date_month_year = datetime.strptime(str_update_date_month_year, "%m/%Y")
    # Check if within 1 year from today
    if today_minus1year_month_year <= to_update_amount_date_month_year <= today_month_year:
        for element in asset_list:
            # Get the correct element to update
            if element["uuid"] == to_update_uuid:
                element_amount = element["amount"]
                # element_amount.sort(key=lambda x: datetime.strptime(x["date"], "%d/%m/%Y").date())

                new_list = []
                for amount in element_amount:
                    # Get datetime in database to compare with today datetime
                    amount_date = datetime.strptime(amount["date"], "%d/%m/%Y").date()
                    str_date_month_year = str(amount_date.month) + "/" + str(amount_date.year)
                    date_month_year = datetime.strptime(str_date_month_year, "%m/%Y")
                    print(date_month_year)

                    if today_minus1year_month_year <= date_month_year <= today_month_year:
                        if date_month_year == to_update_amount_date_month_year:
                            new_list.append(to_update["amount"][0])
                        else:
                            new_list.append(amount)
                    else:
                        print("Error - Invalid update as Datetime is out of range")

        element["amount"] = new_list
        doc_update = {
            "doc": {
            }
        }
        doc_update['doc']['asset'] = asset_list
        client.update(index=index, doc_type='_doc', id=user_uuid, body=doc_update, refresh=True)
        return "Updated Asset with UUID: [" + index + "] index of UUID [" + user_uuid + "]"
    else:
        return "Error - Invalid update as Datetime is out of range"

# Put mapping for indices
# def addMapping(client, indices, mapping):
#     try:
#         print(indices)
#         print(type(mapping))
#         resp=client.indices.put.mapping(
#             index=indices,
#             body=mapping,
#         )
#         print(resp)
#         return "[" + indices + "] mapping done"
#     except:
#         if client.indices.exists(indices):
#             return "Fail to put mapping at [" + indices + "] indices"
#         else: 
#             return "[" + indices + "] does not exist"
