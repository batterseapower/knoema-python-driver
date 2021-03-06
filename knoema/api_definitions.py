"""This module contains metadata definitions for Knoema API"""

import json
from datetime import datetime

def isequal_strings_ignorecase(first, second):
    """The function compares strings ignoring case"""
    if first and second:
        return first.upper() == second.upper()
    else:
        return not (first or second)


class DimensionMember(object):
    """The class contains dimension member information"""

    def __init__(self, data):
        self.key = data['key']
        self.name = data['name']
        self.level = data['level']
        self.hasdata = data['hasData']
        self.fields = data['fields']


class DimensionModel(object):
    """The class contains dimension description"""

    def __init__(self, data):
        self.key = data['key']
        self.id = data['id']
        self.name = data['name']


class Dimension(DimensionModel):
    """The class contains dimension description and dimnesion items"""

    def __init__(self, data):
        super().__init__(data)
        self.items = [DimensionMember(item) for item in data['items']]

    def findmember_by_key(self, member_key):
        """The method searches member of dimension by given member key"""
        for item in self.items:
            if item.key == member_key:
                return item
        return None

    def findmember_by_id(self, member_id):
        """The method searches member of dimension by given member id"""
        for item in self.items:
            if 'id' in item.fields and isequal_strings_ignorecase(item.fields['id'], member_id):
                return item
        return None

    def findmember_by_name(self, member_name):
        """The method searches member of dimension by given member name"""
        for item in self.items:
            if isequal_strings_ignorecase(item.name, member_name):
                return item
        return None


class DateRange(object):
    """The class contains information about dataset's data range"""

    def __init__(self, data):
        self.start_date = datetime.strptime(data['startDate'], '%Y-%m-%dT%H:%M:%SZ')
        self.end_date = datetime.strptime(data['endDate'], '%Y-%m-%dT%H:%M:%SZ')
        self.frequencies = data['frequencies']


class Dataset(object):
    """The class contains dataset description"""

    def __init__(self, data):
        """The method loading data from json to class fields"""

        if 'id' not in data:
            raise ValueError(data)

        self.id = data['id']
        self.dimensions = [DimensionModel(dim) for dim in data['dimensions']]

    def find_dimension_by_name(self, dim_name):
        """the method searching dimension with a given name"""

        for dim in self.dimensions:
            if isequal_strings_ignorecase(dim.name, dim_name):
                return dim
        return None

    def find_dimension_by_id(self, dim_id):
        """the method searching dimension with a given id"""

        for dim in self.dimensions:
            if isequal_strings_ignorecase(dim.id, dim_id):
                return dim
        return None


class PivotItem(object):
    """The class contains pivot request item"""

    def __init__(self, dimensionid=None, members=None):
        self.dimensionid = dimensionid
        self.members = members


class PivotTimeItem(PivotItem):
    """The class contains pivot request item"""

    def __init__(self, dimensionid=None, members=None, uimode=None):
        super().__init__(dimensionid, members)
        self.uimode = uimode


class PivotRequest(object):
    """The class contains pivot request"""

    def __init__(self, dataset):
        self.dataset = dataset
        self.header = []
        self.stub = []
        self.filter = []
        self.frequencies = []

    def _get_item_array(self, items):
        arr = []
        for item in items:
            itemvalues = {
                'DimensionId': item.dimensionid,
                'Members': item.members
            }
            if isinstance(item, PivotTimeItem):
                itemvalues['UiMode'] = item.uimode
            arr.append(itemvalues)
        return arr

    def save_to_json(self):
        """The method saves data to json from object"""
        requestvalues = {
            'Dataset': self.dataset,
            'Header' : self._get_item_array(self.header),
            'Filter' : self._get_item_array(self.filter),
            'Stub' : self._get_item_array(self.stub),
            'Frequencies': self.frequencies
        }
        return json.dumps(requestvalues)


class PivotResponse(object):
    """The class contains pivot response"""

    def __init__(self, data):

        self.dataset = data['dataset']

        self.header = []
        for item in data['header']:
            self.header.append(PivotItem(item['dimensionId'], item['members']))

        self.stub = []
        for item in data['stub']:
            self.stub.append(PivotItem(item['dimensionId'], item['members']))

        self.filter = []
        for item in data['filter']:
            self.filter.append(PivotItem(item['dimensionId'], item['members']))

        self.tuples = data['data']


class FileProperties(object):
    """The class contains response from upload post request"""

    def __init__(self, data):
        self.size = data['Size'] if 'Size' in data else None
        self.name = data['Name'] if 'Name' in data else None
        self.location = data['Location'] if 'Location' in data else None
        self.type = data['Type'] if 'Type' in data else None


class UploadPostResponse(object):
    """The class contains response from upload post request"""

    def __init__(self, data):
        self.successful = data['Successful'] if 'Successful' in data else False
        self.error = data['Error'] if 'Error' in data else None
        self.properties = FileProperties(data['Properties'])


class UploadDatasetDetails(object):
    """The class contains dataset details from verify result response"""

    def __init__(self, data):
        self.dataset_id = data['DatasetId']
        self.dataset_name = data['DatasetName']
        self.source = data['Source']
        self.description = data['Description']
        self.dataset_ref = data['DatasetRef']
        self.publication_date = data['PublicationDate'] if 'PublicationDate' in data else None
        self.accessed_on = data['AccessedOn'] if 'AccessedOn' in data else None


class UploadVerifyResponse(object):
    """The class contains response from upload post request"""

    def __init__(self, data):
        self.successful = data['Successful'] if 'Successful' in data else False
        self.upload_format_type = data['UploadFormatType'] if 'UploadFormatType' in data else None
        self.errors = data['ErrorList'] if 'ErrorList' in data else None
        self.columns = data['Columns'] if 'Columns' in data else None
        self.flat_ds_update_options = data['FlatDSUpdateOptions'] if 'FlatDSUpdateOptions' in data else None
        self.metadata_details = UploadDatasetDetails(data['MetadataDetails']) if 'MetadataDetails' in data and data['MetadataDetails'] is not None else None


class DatasetUpload(object):
    """The class contains request for UploadSubmit"""

    def __init__(self, verify_result, upload_result, dataset=None, public = False):
        self.dataset = dataset

        self.upload_format_type = verify_result.upload_format_type
        self.columns = verify_result.columns
        self.file_property = upload_result.properties
        self.flat_ds_update_options = verify_result.flat_ds_update_options

        dataset_details = verify_result.metadata_details
        self.name = dataset_details.dataset_name if dataset_details and dataset_details.dataset_name else 'New dataset'
        self.description = dataset_details.description if dataset_details else None
        self.source = dataset_details.source if dataset_details else None
        self.publication_date = dataset_details.publication_date if dataset_details else None
        self.accessed_on = dataset_details.accessed_on if dataset_details else None
        self.dataset_ref = dataset_details.dataset_ref if dataset_details else None
        self.public = public

    def save_to_json(self):
        """The method saves DatasetUpload to json from object"""
        requestvalues = {
            'DatasetId': self.dataset,
            'Name': self.name,
            'Description': self.description,
            'Source': self.source,
            'PubDate': self.publication_date,
            'AccessedOn': self.accessed_on,
            'Url': self.dataset_ref,
            'UploadFormatType': self.upload_format_type,
            'Columns': self.columns,
            'FileProperty': self.file_property.__dict__,
            'FlatDSUpdateOptions': self.flat_ds_update_options,
            'Public': self.public
        }
        return json.dumps(requestvalues)


class DatasetUploadResponse(object):
    """The class contains response for UploadSubmit"""

    def __init__(self, data):
        self.submit_id = data['Id'] if 'Id' in data else None
        self.dataset = data['DatasetId'] if 'DatasetId' in data else None
        self.status = data['Status'] if 'Status' in data else 'failed'
        self.errors = data['Errors'] if 'Errors' in data else None


class DatasetUploadStatusResponse(object):
    """The class contains response for UploadSubmit"""

    def __init__(self, data):
        self.submit_id = data['id'] if 'id' in data else None
        self.dataset = data['datasetId'] if 'datasetId' in data else None
        self.status = data['status'] if 'status' in data else 'failed'
        self.errors = data['errors'] if 'errors' in data else None


class DatasetVerifyRequest(object):
    """The class contains dataset verification request"""

    def __init__(self, dataset, publication_date, source, refernce_url):
        self.dataset = dataset
        self.publication_date = publication_date
        self.source = source
        self.refernce_url = refernce_url

    def save_to_json(self):
        """The method saves data to json from object"""

        requestvalues = {
            'id': self.dataset,
            'publicationDate': self.publication_date.strftime('%Y-%m-%d'),
            'source': self.source,
            'refUrl': self.refernce_url,
        }        
        return json.dumps(requestvalues)


class DatasetVerifyResponse(object):
    """The class contains response from dataset verification request"""

    def __init__(self, data):
        self.status = data['status']
        self.errors = data['errors'] if 'errors' in data else None
