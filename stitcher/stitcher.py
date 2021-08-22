import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from frames import extract_frames


def stitch_images(img_paths=[], base_path='', img_data=[]):
    use_read = len(img_paths) > 0
    if use_read:
        base_img = cv.imread(f"{base_path}{img_paths[0]}")
    else:
        base_img = img_data[0]

    for i in range(len(img_paths) + len(img_data) - 1):
        if use_read:
            stitch_img = cv.imread(f"{base_path}{img_paths[i + 1]}")
        else:
            stitch_img = img_data[i + 1]

        stitch_img_cvt = cv.cvtColor(stitch_img, cv.COLOR_BGR2GRAY)

        base_img_cvt = cv.cvtColor(base_img, cv.COLOR_BGR2GRAY)

        sift = cv.SIFT_create()

        stitch_kp, stitch_des = sift.detectAndCompute(stitch_img_cvt, None)
        base_kp, base_des = sift.detectAndCompute(base_img_cvt, None)

        # kp_img_left = cv.drawKeypoints(base_img, stitch_kp, None)
        # kp_img_right = cv.drawKeypoints(stitch_img, base_kp, None)
        # cv.imwrite(f"test_kp_left{i}.png", kp_img_left)
        # cv.imwrite(f"test_kp_right{i}.png", kp_img_right)

        match = cv.BFMatcher()
        matches = match.knnMatch(base_des, stitch_des, k=2)

        good = []
        for m, n in matches:
            if m.distance < .7 * n.distance:
                good.append(m)

        draw_params = dict(matchColor=(0, 255, 0),  # draw matches in green color
                           singlePointColor=None,
                           flags=2)
        match_img = cv.drawMatches(base_img, base_kp, stitch_img, stitch_kp, good, None, **draw_params)

        cv.imwrite(f"frames\\test_match_{i}.png", match_img)

        MIN_MATCH_COUNT = 5
        if len(good) >= MIN_MATCH_COUNT:
            src_pts = np.float32([base_kp[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            dst_pts = np.float32([stitch_kp[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
            M, mask = cv.findHomography(dst_pts, src_pts, cv.RANSAC, 5.0)
            # h, w = img1.shape
            # pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            # dst = cv.perspectiveTransform(pts, M)
            # img2 = cv.polylines(img2, [np.int32(dst)], True, 255, 3, cv.LINE_AA)
            # cv2.imshow("original_image_overlapping.jpg", img2)
        else:
            raise AssertionError("Can’t find enough keypoints.")

        dst = cv.warpPerspective(stitch_img, M, (base_img.shape[1] + stitch_img.shape[1], base_img.shape[0]))

        dst[0:base_img.shape[0], 0:base_img.shape[1]] = base_img

        def trim(frame):
            # crop top
            if not np.sum(frame[0]):
                return trim(frame[1:])
            # crop top
            if not np.sum(frame[-1]):
                return trim(frame[:-2])
            # crop top
            if not np.sum(frame[:, 0]):
                return trim(frame[:, 1:])
            # crop top
            if not np.sum(frame[:, -1]):
                return trim(frame[:, :-2])
            return frame

        cv.imwrite(f"frames\\stitched_{i}.png", dst)

        trimmed_img = trim(dst)

        cv.imwrite(f"frames\\trimmed_stitched_{i}.png", trimmed_img)

        base_img = trimmed_img

    return base_img


def stitch_image_matrix(img_mat, base_path=''):
    stitched_imgs = []

    for j in range(len(img_mat)):
        stitched_img = stitch_images(img_mat[j], base_path)
        rotated_img = rotate_image(stitched_img, 90)
        stitched_imgs.append(rotated_img)

    # cv.imwrite(f"frames\\final_rot_img_{0}.png", stitched_imgs[0])
    # cv.imwrite(f"frames\\final_rot_img_{1}.png", stitched_imgs[1])
    final_rot_img = stitch_images(img_data=stitched_imgs, base_path=base_path)
    # cv.imwrite(f"frames\\final_rot_img.png", final_rot_img)
    final_img = rotate_image(final_rot_img, -90)
    cv.imwrite(f"frames\\final_img.png", final_img)


def rotate_image(image, angle):
    # grab the dimensions of the image and then determine the
    # center
    (h, w) = image.shape[:2]
    (cX, cY) = (w // 2, h // 2)
    # grab the rotation matrix (applying the negative of the
    # angle to rotate clockwise), then grab the sine and cosine
    # (i.e., the rotation components of the matrix)
    M = cv.getRotationMatrix2D((cX, cY), -angle, 1.0)
    cos = np.abs(M[0, 0])
    sin = np.abs(M[0, 1])
    # compute the new bounding dimensions of the image
    nW = int((h * sin) + (w * cos))
    nH = int((h * cos) + (w * sin))
    # adjust the rotation matrix to take into account translation
    M[0, 2] += (nW / 2) - cX
    M[1, 2] += (nH / 2) - cY
    # perform the actual rotation and return the image
    return cv.warpAffine(image, M, (nW, nH))
