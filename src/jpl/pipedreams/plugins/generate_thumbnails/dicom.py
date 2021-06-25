from .template import Template

import numpy as np
import png
import pydicom
from PIL import Image, ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True
THUMBNAIL_SIZE = 50

class DICOM(Template):
    def __init__(self):
        super().__init__()
        self.description = 'create thumbnail using DICOM'

    def generate_thumbnail(self, image_filepath, thumbnail_filepath):
        ds = pydicom.dcmread(image_filepath)

        if hasattr(ds, 'pixel_array'):
            shape = ds.pixel_array.shape

            # Convert to float to avoid overflow or underflow losses.
            image_2d = ds.pixel_array.astype(float)

            # Rescaling grey scale between 0-255
            image_2d_scaled = (np.maximum(image_2d, 0) / image_2d.max()) * 255.0

            # Convert to uint
            image_2d_scaled = np.uint8(image_2d_scaled)

            # Write the PNG file
            with open(thumbnail_filepath, 'wb') as png_file:
                w = png.Writer(shape[1], shape[0], greyscale=True)
                w.write(png_file, image_2d_scaled)

            # Convert current file to thumbnail - will overwrite previous
            size = THUMBNAIL_SIZE, THUMBNAIL_SIZE * (shape[0] / shape[1])
            size = (int(round(size[0])), int(round(size[1])))
            im = (Image.open(thumbnail_filepath))
            im = im.resize(size, Image.ANTIALIAS)
            im.save(thumbnail_filepath, "PNG")

        else:
            print("WARNING: could not find PixelData to create thumbnail for DICOM file: %s" % image_filepath)