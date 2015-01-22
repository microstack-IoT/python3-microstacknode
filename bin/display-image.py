import cv2  # TODO maybe do a check for this lib? tell user if not installed
import sys
from microstacknode.hardware.display.spirte import Sprite
from microstacknode.hardware.display.ssd1306 import SSD1306



def image_to_sprite(filename):
    """Returns a Sprite converted from the image at `filename`."""
    im_gray = cv2.imread(filename, cv2.CV_LOAD_IMAGE_GRAYSCALE)
    (thresh, im_bw) = cv2.threshold(im_gray,
                                    128,
                                    255,
                                    cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    height = len(im_bw)
    width = len(im_bw[0])
    sprite = Sprite(width, height)
    sprite.pixel_state = im_bw
    # sprite.rotate90(3)  # ???
    return sprite


if __name__ == '__main__':
    if len(sys.argv) < 1:
        print("")
        print("    usage: {} filename".format(sys.argv[0]))
        print("")
    else:
        sprite = image_to_sprite(sys.argv[1])
        print(sprite.pixel_state)
        # with SSD1306() as display:
        #     display.draw_sprite(0, 0, sprite)
