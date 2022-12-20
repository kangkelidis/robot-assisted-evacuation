import glob

import natsort
from PIL import Image
from typing import List

WORKSPACE_FOLDER = "/home/workspace/"
FRAME_FOLDER = WORKSPACE_FOLDER + "frames"  # type:str


def generate_video(simulation_id, frame_duration=200):
    # type: ( str, int) -> None
    search_string = "{}/view_{}_*png".format(FRAME_FOLDER, simulation_id)  # type: str
    frame_list = natsort.natsorted(glob.glob(search_string))  # type: List[str]
    number_of_frames = len(frame_list)  # type: int

    if number_of_frames == 0:
        print("No frames for GIF generation for simulation {}".format(simulation_id))
        return

    print("Generating GIF from {} frames for simulation...".format(number_of_frames, simulation_id))
    frames = []  # type: List[Image]
    for frame_file in frame_list:
        frame_as_image = Image.open(frame_file)  # type: Image
        frames.append(frame_as_image)

    output_file = WORKSPACE_FOLDER + "video/video_{}.gif".format(simulation_id)
    first_frame = frames[0]  # type: Image
    first_frame.save(output_file, format="GIF", append_images=frames,
                     save_all=True, duration=frame_duration)
    print("Animation generated at {}".format(output_file))
