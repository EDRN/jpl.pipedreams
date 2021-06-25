from .template import Template
import pandas as pd

class Excel(Template):
    def __init__(self):
        super().__init__()
        self.description = 'read metadata from excel files'

    def parse_metadata(self, content_bytes):
        xl = pd.ExcelFile(content_bytes)
        metadata_df = pd.read_excel(content_bytes, sheet_name=xl.sheet_names[0])
        metadata_df.fillna('', inplace=True)
        return {"metadata": metadata_df} # metadata_df.to_dict('records')}