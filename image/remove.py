from PIL import Image
import os
from pathlib import Path


def remove_images():
    try:
        for file_path in os.listdir():
            if isImage(file_path):
                os.remove(file_path)
    except OSError as e:
        details = 'Error while removing temporary file.'


def isImage(file_path):
    try:
        img = Image.open(file_path)
        if img is not None:
            return True
        else:
            return False
    except Exception as e:
        return False
