from .template import Template
from PIL import Image

# REDUCTION_FACTOR = 50
THUMBNAIL_SIZE = (100, 100)


class Disk(Template):
    def __init__(self):
        super().__init__()
        self.description = 'create thumbnail using PIL'

    def generate_thumbnail(self, image_filepath, thumbnail_filepath):
        image = Image.open(image_filepath)
        # image.thumbnail( (image.size[0]/REDUCTION_FACTOR, image.size[1]/REDUCTION_FACTOR) )
        image.thumbnail(THUMBNAIL_SIZE)
        image.save(thumbnail_filepath, "PNG")