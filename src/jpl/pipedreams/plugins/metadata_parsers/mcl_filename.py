# encoding: utf-8

from .template import Template
from jpl.pipedreams.utils.misc_utils import get_file_ext, camel_case_split


class MCL_filename(Template):
    def __init__(self):
        super().__init__()
        self.description = 'read metadata from mcl file name'

    def parse_metadata(self, filename):
        metadata = {}
        file_ext = get_file_ext(filename)
        parts = filename.replace('.' + file_ext, '').split('_')
        StudyID, InstitutionID, FileContent, DateFileGenerated, Version, DataUploadType = parts
        FileContent = camel_case_split(FileContent)
        metadata['StudyID'] = StudyID
        metadata['InstitutionID'] = InstitutionID
        metadata['FileContent'] = FileContent
        metadata['DateFileGenerated'] = DateFileGenerated
        metadata['Version'] = Version
        metadata['DataUploadType'] = DataUploadType
        return {"metadata": metadata}
