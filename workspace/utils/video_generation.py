"""
This module provides functionality for generating GIF animations from simulation frames.
"""


import glob

import natsort  # type: ignore
from PIL import Image, ImageDraw  # type: ignore
from utils.paths import FRAMES_FOLDER


def generate_video(simulation_id: str, video_path: str, frame_duration: int = 200) -> None:
    """ Generates a GIF animation from the frames of a simulation.

    It searches for the frames in the "frames" folder and creates an animation
    with the specified frame duration.

    Args:
        simulation_id: The ID of the simulation.
        video_path: The path to save the generated animation.
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
    for i, frame_file in enumerate(frame_list):
        frame_as_image = Image.open(frame_file)
        frames.append(frame_as_image)
        draw = ImageDraw.Draw(frame_as_image)
        label = f'tick:{i}'
        draw.text((10, 10), label, fill='black')

    output_file = video_path + f"/video_{simulation_id}.gif"
    first_frame = frames[0]
    first_frame.save(output_file, format="GIF", append_images=frames,
                     save_all=True, duration=frame_duration)
    print("Animation generated at {}".format(output_file))
