import os
import io
from .template import Template

class S3(Template):
    def __init__(self):
        super().__init__()
        self.description = 'for basic S3 file ops'

    def get_bytes(self, path, s3_bucket, s3_client):
        bytes_buffer = io.BytesIO()
        s3_client.download_fileobj(Bucket=s3_bucket, Key=path, Fileobj=bytes_buffer)
        bytes = bytes_buffer.getvalue()
        return bytes

    def read_str(self, path, s3_bucket, s3_client):
        bytes_buffer = io.BytesIO()
        s3_client.download_fileobj(Bucket=s3_bucket, Key=path, Fileobj=bytes_buffer)
        byte_value = bytes_buffer.getvalue()
        str_value = byte_value.decode()
        return {'str_value': str_value}

    def get_file_size(self, path, s3_bucket, s3_client):
        # TODO: Implement
        return 12212121212

    def isfile(self, path, s3_bucket, s3_client):
        if path.endswith('/'):
            path=path[:-1]
        resp = s3_client.list_objects(Bucket=s3_bucket, Prefix=path, Delimiter="/")
        if 'Contents' in resp and path in [x['Key'] for x in resp['Contents']]:
            return True
        return False

    def isdir(self, path, s3_bucket, s3_client):
        if path.endswith('/'):
            path=path[:-1]
        path_parent = os.path.dirname(path)
        if path_parent!='':
            path_parent=path_parent+'/'
        resp = s3_client.list_objects(Bucket=s3_bucket, Prefix=path_parent, Delimiter="/")
        # check if this dir is present in the prefixes for the parent
        if 'CommonPrefixes' in resp and path in [x['Prefix'][:-1] for x in resp['CommonPrefixes']]:
            return True

    def exists(self, path, s3_bucket, s3_client):
        if path.endswith('/'):
            path=path[:-1]
        resp = s3_client.list_objects(Bucket=s3_bucket,Prefix=path, Delimiter="/")
        if 'CommonPrefixes' in resp or 'Contents' in resp:
            return True
        return False

    def dir_walk(self, path, s3_bucket, s3_client):
        if not path.endswith('/'):
            path=path+'/'
        resp = s3_client.list_objects(Bucket=s3_bucket, Prefix=path, Delimiter="/")
        subdirs,files=[],[]
        if 'Contents' in resp :
            files=[x['Key'] for x in resp['Contents']]
        if 'CommonPrefixes' in resp:
            subdirs=[x['Prefix'][:-1] for x in resp['CommonPrefixes']]
        return subdirs,files

    def recurse(self, path, s3_bucket, s3_client):
        subdirs, files = self.dir_walk({'path':path, 's3_bucket': s3_bucket, 's3_client':s3_client})
        resource_children = subdirs + files
        for resource in resource_children:
            yield from self.recurse({'path':resource, 's3_bucket': s3_bucket, 's3_client':s3_client})
        yield path, resource_children

    def download(self, source_path, target_path, s3_bucket, s3_client):
        s3_client.download_file(s3_bucket, source_path, target_path)

    def search_file(self, dir_path, pattern):
        # TODO: implement
        pass
