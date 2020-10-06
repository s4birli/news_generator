from PIL import Image, ImageChops, ImageStat, ImageFile
from io import BytesIO
from math import log
import shutil
import os
import piexif

# encoding: utf-8

# ============================[ General settings ]============================
SUPPORTED_FORMATS = ['png', 'jpg', 'jpeg']
DEFAULT_QUALITY = 80
DEFAULT_BG_COLOR = (255, 255, 255)
MIN_BIG_IMG_SIZE = 80_000
MIN_BIG_IMG_AREA = 800 * 600

# ====================[ iOS/Pythonista specific settings ]====================
IPAD_FONT_SIZE = 15
IPHONE_FONT_SIZE = 10
IOS_WORKERS = 2
IOS_FONT = "Menlo"


class optimization:
    def __init__(self, path):
        self.src_path = path
        self.max_w = 800
        self.max_h = 500
        self.quality = 80
        self.fast_mode = True
        self.keep_exif = False
        self.no_size_comparison = False
        self.conv_big = False
        self.convert_all = False
        self.bg_color = False
        self.grayscale = False
        self.force_del = False
        self.remove_transparency = False
        self.reduce_colors = False
        self.fast_mode = False

    def is_big_png_photo(self) -> bool:
        img = Image.open(self.src_path)
        orig_format = img.format
        orig_mode = img.mode

        if orig_format != 'PNG' or orig_mode in ['P', 'L', 'LA']:
            return False

        w, h = img.size
        if (w * h) >= MIN_BIG_IMG_AREA:
            unique_colors = {img.getpixel((x, y))
                             for x in range(w) for y in range(h)}
            if len(unique_colors) > 2 ** 16:
                img = img.convert("RGB")
                if w > h:
                    img, status = self.downsize_img(img, 1600, 0)
                else:
                    img, status = self.downsize_img(img, 0, 1600)

                tempfile = BytesIO()
                try:
                    img.save(tempfile, quality=80, format="JPEG")
                except IOError:
                    ImageFile.MAXBLOCK = img.size[0] * img.size[1]
                    img.save(tempfile, quality=80, format="JPEG")

                final_size = tempfile.getbuffer().nbytes
                return final_size > MIN_BIG_IMG_SIZE

        return False

    def compare_images(self, img1, img2):
        # Don't compare if images are of different modes or different sizes.
        if (img1.mode != img2.mode) \
                or (img1.size != img2.size) \
                or (img1.getbands() != img2.getbands()):
            return None

        # Generate diff image in memory.
        diff_img = ImageChops.difference(img1, img2)
        # Calculate difference as a ratio.
        stat = ImageStat.Stat(diff_img)
        diff_ratio = sum(stat.mean) / (len(stat.mean) * 255)

        return diff_ratio * 100

    def _diff_iteration_count(self, lo, hi):
        """Return the depth of the binary search tree for this range"""
        if lo >= hi:
            return 0
        else:
            return int(log(hi - lo, 2)) + 1

    def get_diff_at_quality(self, photo, quality):
        diff_photo = BytesIO()
        # optimize is omitted here as it doesn't affect
        # quality but requires additional memory and cpu
        photo.save(diff_photo, format="JPEG",
                   quality=quality, progressive=True)
        diff_photo.seek(0)
        img2 = Image.open(diff_photo)
        diff_score = self.compare_images(photo, img2)

        # print("================> DIFF1 == DIFF2? ", diff_score==diff_score2)

        if diff_score < 0:
            return -1 + diff_score / 100
        else:
            return 1 - diff_score / 100

    def jpeg_dynamic_quality(self, original_photo, use_dynamic_quality=True):
        diff_goal = 0.992
        hi = DEFAULT_QUALITY
        lo = hi - 5

        # working on a smaller size image doesn't give worse results but is faster
        # changing this value requires updating the calculated thresholds
        photo = original_photo.resize((400, 400))

        if not use_dynamic_quality:
            default_diff = self.get_diff_at_quality(photo, hi)
            return hi, default_diff

        # 95 is the highest useful value for JPEG. Higher values cause different behavior
        # Used to establish the image's intrinsic ssim without encoder artifacts
        normalized_diff = self.get_diff_at_quality(photo, 95)

        selected_quality = selected_diff = None

        # loop bisection. ssim/diff function increases monotonically so this will converge
        for i in range(self._diff_iteration_count(lo, hi)):
            curr_quality = (lo + hi) // 2
            curr_diff = self.get_diff_at_quality(photo, curr_quality)
            diff_ratio = curr_diff / normalized_diff

            if diff_ratio >= diff_goal:
                # continue to check whether a lower quality level also exceeds the goal
                selected_quality = curr_quality
                selected_diff = curr_diff
                hi = curr_quality
            else:
                lo = curr_quality

        if selected_quality:
            return selected_quality, selected_diff
        else:
            default_diff = self.get_diff_at_quality(photo, hi)
            return hi, default_diff

    def make_grayscale(self, img):
        orig_mode = img.mode
        if orig_mode in ["RGB", "CMYK", "YCbCr", "LAB", "HSV"]:
            return img.convert("L")
        elif orig_mode == "RGBA":
            return img.convert("LA").convert("RGBA")
        elif orig_mode == "P":
            # Using ITU-R 601-2 luma transform:  L = R * 299/1000 + G * 587/1000 + B * 114/1000
            pal = img.getpalette()
            for i in range(len(pal) // 3):
                # Using ITU-R 601-2 luma transform
                g = (pal[3 * i] * 299 + pal[3 * i + 1] *
                     587 + pal[3 * i + 2] * 114) // 1000
                pal[3 * i: 3 * i + 3] = [g, g, g]
            img.putpalette(pal)
            return img
        else:
            return img

    def downsize_img(self, img, max_w: int, max_h: int):
        w, h = img.size
        if not max_w:
            max_w = w
        if not max_h:
            max_h = h

        if (max_w, max_h) == (w, h):  # If no changes, do nothing
            return img, False

        img.thumbnail((max_w, max_h), resample=Image.LANCZOS)
        return img, True

    def optimize_jpg(self):
        try:
            img = Image.open(self.src_path)
            orig_format = img.format
            orig_mode = img.mode

            folder, filename = os.path.split(self.src_path)

            if folder == '':
                folder = os.getcwd()

            temp_file_path = os.path.join(folder + "/~temp~" + filename)
            orig_size = os.path.getsize(self.src_path)
            orig_colors, final_colors = 0, 0

            result_format = "JPEG"
            try:
                had_exif = True if piexif.load(self.src_path)[
                    'Exif'] else False
            except piexif.InvalidImageDataError:  # Not a supported format
                had_exif = False
            except ValueError:  # No exif info
                had_exif = False
            # TODO: Check if we can provide a more specific treatment of piexif exceptions.
            except Exception:
                had_exif = False

            if self.max_w or self.max_h:
                img, was_downsized = self.downsize_img(
                    img, self.max_w, self.max_h)
            else:
                was_downsized = False

            if self.grayscale:
                img = self.make_grayscale(img)

            # only use progressive if file size is bigger
            use_progressive_jpg = orig_size > 10000

            if self.fast_mode:
                quality = self.quality
            else:
                quality, jpgdiff = self.jpeg_dynamic_quality(img)

            try:
                img.save(
                    temp_file_path,
                    quality=quality,
                    optimize=True,
                    progressive=use_progressive_jpg,
                    format=result_format)
            except IOError:
                ImageFile.MAXBLOCK = img.size[0] * img.size[1]
                img.save(
                    temp_file_path,
                    quality=quality,
                    optimize=True,
                    progressive=use_progressive_jpg,
                    format=result_format)

            if self.keep_exif and had_exif:
                try:
                    piexif.transplant(
                        os.path.expanduser(self.src_path), temp_file_path)
                    has_exif = True
                except ValueError:
                    has_exif = False
                # TODO: Check if we can provide a more specific treatment of piexif exceptions.
                except Exception:
                    had_exif = False
            else:
                has_exif = False

            # Only replace the original file if compression did save any space
            final_size = os.path.getsize(temp_file_path)
            if self.no_size_comparison or (orig_size - final_size > 0):
                shutil.move(temp_file_path, os.path.expanduser(self.src_path))
                was_optimized = True
            else:
                final_size = orig_size
                was_optimized = False
                try:
                    os.remove(temp_file_path)
                except OSError as e:
                    details = 'Error while removing temporary file.'
                    self.show_img_exception(e, self.src_path, details)

            return self.src_path
        except Exception as e:
            print(e)

    def show_img_exception(self, exception: Exception, image_path: str, details: str = '') -> None:
        print("\nAn error has occurred while trying to optimize this file:")
        print(image_path)

        if details:
            print(f'\n{details}')

        print("\nThe following info may help to understand what has gone wrong here:\n")
        print(exception)

    def optimize_png(self):
        img = Image.open(self.src_path)
        orig_format = img.format
        orig_mode = img.mode

        folder, filename = os.path.split(self.src_path)

        if folder == '':
            folder = os.getcwd()

        temp_file_path = os.path.join(folder + "/~temp~" + filename)
        orig_size = os.path.getsize(self.src_path)
        orig_colors, final_colors = 0, 0

        had_exif = has_exif = False  # Currently no exif methods for PNG files
        if orig_mode == 'P':
            final_colors = orig_colors = len(img.getcolors())

        if self.convert_all or (self.conv_big and self.is_big_png_photo()):
            # convert to jpg format
            filename = os.path.splitext(os.path.basename(self.src_path))[0]
            conv_file_path = os.path.join(folder + "/" + filename + ".jpg")

            if self.max_w or self.max_h:
                img, was_downsized = downsize_img(img, self.max_w, self.max_h)
            else:
                was_downsized = False

            img = remove_transparency(img, self.bg_color)
            img = img.convert("RGB")

            if self.grayscale:
                img = make_grayscale(img)

            try:
                img.save(
                    conv_file_path,
                    quality=self.quality,
                    optimize=True,
                    progressive=True,
                    format="JPEG")
            except IOError:
                ImageFile.MAXBLOCK = img.size[0] * img.size[1]
                img.save(
                    conv_file_path,
                    quality=self.quality,
                    optimize=True,
                    progressive=True,
                    format="JPEG")

            # Only save the converted file if conversion did save any space
            final_size = os.path.getsize(conv_file_path)
            if self.no_size_comparison or (orig_size - final_size > 0):
                was_optimized = True
                if self.force_del:
                    try:
                        os.remove(self.src_path)
                    except OSError as e:
                        details = 'Error while replacing original PNG with the new JPEG version.'
                        show_img_exception(e, self.src_path, details)
            else:
                final_size = orig_size
                was_optimized = False
                try:
                    os.remove(conv_file_path)
                except OSError as e:
                    details = 'Error while removing temporary JPEG converted file.'
                    show_img_exception(e, self.src_path, details)

            result_format = "JPEG"
            return self.src_path

        # if PNG and user didn't ask for PNG to JPEG conversion, do this instead.
        else:
            result_format = "PNG"
            if self.remove_transparency:
                img = remove_transparency(img, self.bg_color)

            if self.max_w or self.max_h:
                img, was_downsized = downsize_img(img, self.max_w, self.max_h)
            else:
                was_downsized = False

            if self.reduce_colors:
                img, orig_colors, final_colors = do_reduce_colors(
                    img, self.max_colors)

            if self.grayscale:
                img = make_grayscale(img)

            if not self.fast_mode and img.mode == "P":
                img, final_colors = rebuild_palette(img)

            try:
                img.save(temp_file_path, optimize=True, format=result_format)
            except IOError:
                ImageFile.MAXBLOCK = img.size[0] * img.size[1]
                img.save(temp_file_path, optimize=True, format=result_format)

            final_size = os.path.getsize(temp_file_path)

            # Only replace the original file if compression did save any space
            if self.no_size_comparison or (orig_size - final_size > 0):
                shutil.move(temp_file_path, os.path.expanduser(self.src_path))
                was_optimized = True
            else:
                final_size = orig_size
                was_optimized = False
                try:
                    os.remove(temp_file_path)
                except OSError as e:
                    details = 'Error while removing temporary file.'
                    show_img_exception(e, self.src_path, details)

            return self.src_path

    def main(self):
        # src_path, max_w, max_h
        img = Image.open(self.src_path)
        try:
            if img.format.upper() == 'PNG':
                return self.optimize_png()
            elif img.format.upper() in ('JPEG', 'MPO'):
                return self.optimize_jpg()
        except Exception as e:
            print(e)
            return "error"

    def isImage(self):
        try:
            img = Image.open(self.src_path)
            try:
                if img.format.upper() == 'PNG':
                    return True
                elif img.format.upper() in ('JPEG', 'MPO'):
                    return True
            except Exception as e:
                return False
        except Exception as e:
            return False

    def isJPEG(self):
        try:
            img = Image.open(self.src_path)
            try:
                if img.format.upper() in ('JPEG', 'MPO'):
                    return True
                else:
                    return False

            except Exception as e:
                return False
        except Exception as e:
            return False


def image_optimize(path):
    opt = optimization(path)
    return opt.main()


def isImage(path):
    opt = optimization(path)
    return opt.isImage()


def isJPEG(path):
    opt = optimization(path)
    return opt.isJPEG()
