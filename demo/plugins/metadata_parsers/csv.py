from .template import Template
import pandas as pd


class Csv(Template):
    def __init__(self):
        super().__init__()
        self.description = 'read metadata from csv files'

    def parse_metadata(self, content_bytes):
        metadata_df = pd.read_csv(content_bytes)
        metadata_df.fillna('', inplace=True)
        return {"metadata": metadata_df} # metadata_df.to_dict('records')}