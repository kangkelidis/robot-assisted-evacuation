"""
This module provides functionality for generating GIF animations from simulation frames.
"""


import glob
import os

import natsort
from core.utils.paths import FRAMES_FOLDER, VIDEO_FOLDER, get_experiment_folder
from PIL import Image  # type: ignore


def generate_video(simulation_id: str, frame_duration: int = 200) -> None:
    """ Generates a GIF animation from the frames of a simulation.

    It searches for the frames in the "frames" folder and creates an animation
    with the specified frame duration.

    Args:
        simulation_id: The ID of the simulation.
        frame_duration: The duration of each frame in milliseconds. Defaults to 200.
    """
    search_string = "{}view_{}_*png".format(FRAMES_FOLDER, simulation_id)
    frame_list = natsort.natsorted(glob.glob(search_string))
    number_of_frames = len(frame_list)

    if number_of_frames == 0:
        print("No frames for GIF generation for simulation {}".format(simulation_id))
        return

    print("Generating GIF from {} frames for simulation {}".format(number_of_frames, simulation_id))
    frames = []
    for frame_file in frame_list:
        frame_as_image = Image.open(frame_file)
        frames.append(frame_as_image)

    experiment_folder_name = get_experiment_folder()
    experiment_folder_path = os.path.join(VIDEO_FOLDER, experiment_folder_name)
    if not os.path.exists(experiment_folder_path):
        os.makedirs(experiment_folder_path)

    output_file = experiment_folder_path + "/video_{}.gif".format(simulation_id)
    first_frame = frames[0]
    first_frame.save(output_file, format="GIF", append_images=frames,
                     save_all=True, duration=frame_duration)
    print("Animation generated at {}".format(output_file))
