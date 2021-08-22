from frames import extract_frames, extract_i_frames
from stitcher import stitch_images, stitch_image_matrix, rotate_image
import cv2 as cv

if __name__ == "__main__":
    images = extract_frames("test_material\\test_vid.mov", "frames", start=-1, end=601, every=20)
    # images = extract_i_frames("test_material\\short_panorama_video.mp4", "frames", every=300)
    for i in range(len(images)):
        img = cv.imread(f"frames\\{images[i]}")
        img = rotate_image(img, 90)
        cv.imwrite(f"frames\\{images[i]}", img)
    #
    stitch_images(images, "frames\\")

    # stitch_image_matrix([['pano_bottom_img_01.png', 'pano_bottom_img_02.png', 'pano_bottom_img_03.png',
    # 'pano_bottom_img_04.png', 'pano_bottom_img_05.png'],
    # ['pano_top_img_01.png', 'pano_top_img_02.png', 'pano_top_img_03.png',
    # 'pano_top_img_04.png', 'pano_top_img_05.png']], 'test_material\\')
    # stitch_images(['pano_top_img_01.png', 'pano_top_img_02.png'], 'test_material\\')
