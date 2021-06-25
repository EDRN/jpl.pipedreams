from .template import Template
from openslide import OpenSlide

class Disk(Template):
    def __init__(self):
        super().__init__()
        self.description = 'create thumbnail using OpenSlide'

    def generate_thumbnail(self, image_filepath, thumbnail_filepath):
        '''
        Generates a thumbnail from the specified image.
        '''
        # open image with OpenSlide library
        image_file = OpenSlide(image_filepath)

        # extract image dimensions
        image_dims = image_file.dimensions

        # make thumbnail 100 times smaller
        thumb_dims = tuple((x / 100 for x in image_dims))

        # create thumbnail
        thumb_file = image_file.get_thumbnail(thumb_dims)

        # save file with desired path, format
        thumb_file.save(thumbnail_filepath, "png")

        # cleanup
        image_file.close()