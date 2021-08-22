import cv2 as cv
import os
import subprocess


def extract_frames(video_path, frames_dir, overwrite=False, start=-1, end=-1, every=1):
    """
    Extract frames from a video using OpenCVs VideoCapture
    :param video_path: path of the video
    :param frames_dir: the directory to save the frames
    :param overwrite: to overwrite frames that already exist?
    :param start: start frame
    :param end: end frame
    :param every: frame spacing
    :return: array with name of the images
    """

    video_path = os.path.normpath(video_path)  # make the paths OS (Windows) compatible
    frames_dir = os.path.normpath(frames_dir)  # make the paths OS (Windows) compatible

    video_dir, video_filename = os.path.split(video_path)  # get the video path and filename from the path

    assert os.path.exists(video_path)  # assert the video file exists

    capture = cv.VideoCapture(video_path)  # open the video using OpenCV

    if start < 0:  # if start isn't specified lets assume 0
        start = 0
    if end < 0:  # if end isn't specified assume the end of the video
        end = int(capture.get(cv.CAP_PROP_FRAME_COUNT))

    capture.set(1, start)  # set the starting frame of the capture
    frame = start  # keep track of which frame we are up to, starting from start
    while_safety = 0  # a safety counter to ensure we don't enter an infinite while loop (hopefully we won't need it)
    saved_count = 0  # a count of how many frames we have saved

    images = []

    while frame < end:  # lets loop through the frames until the end

        _, image = capture.read()  # read an image from the capture

        if while_safety > 500:  # break the while if our safety maxs out at 500
            print("safety")
            break

        # sometimes OpenCV reads None's during a video, in which case we want to just skip
        if image is None:  # if we get a bad return flag or the image we read is None, lets not save
            while_safety += 1  # add 1 to our while safety, since we skip before incrementing our frame variable
            continue  # skip

        if frame % every == 0:  # if this is a frame we want to write out based on the 'every' argument
            while_safety = 0  # reset the safety count
            save_path = os.path.join(frames_dir, "{:010d}.png".format(frame))  # create the save path
            if not os.path.exists(save_path) or overwrite:  # if it doesn't exist or we want to overwrite anyways
                test = cv.imwrite(save_path, image)  # save the extracted image
                saved_count += 1  # increment our counter by one
                name = "{:010d}.png".format(frame)
                images.append(name)
                print(name)

        frame += 1  # increment our frame count
    capture.release()  # after the while has finished close the capture

    return images  # and return the count of the images we saved


# doesn't work because of ffprobe command
def extract_i_frames(video_path, frames_dir, overwrite=False, start=-1, end=-1, every=1):
    if not os.path.exists(frames_dir):
        os.mkdir(frames_dir)
    command = 'ffprobe -v error -show_entries frame=pict_type -of default=noprint_wrappers=1'.split()
    print(command + [video_path])
    out = subprocess.check_output(command + [video_path], shell=True).decode()
    f_types = out.replace('pict_type=', '').split()
    frame_types = zip(range(len(f_types)), f_types)
    i_frames = [x[0] for x in frame_types if x[1] == 'I']
    if i_frames:
        cap = cv.VideoCapture(video_path)
        for frame_nr in i_frames:
            cap.set(cv.CAP_PROP_POS_FRAMES, frame_nr)
            ret, frame = cap.read()
            outname = frames_dir + f"i_{str(frame_nr)}.png"
            cv.imwrite(outname, frame)
        cap.release()
