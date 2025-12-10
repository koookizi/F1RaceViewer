import fastf1 as ff1
from fastf1 import plotting
from fastf1 import utils
import fastf1.legacy
import fastf1 as ff1
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib import cm
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import matplotlib as mpl
colormap = mpl.cm.plasma

background_color = "#FFFFFF"
circle_color = "#5c409b"
line_color = "#d2a263"
text_color = "#FFFFFF"
title_color = "#5c409b"

year= 2025
gp = 'United Kingdom'
event = 'Race'

session_event = ff1.get_session(year, gp, event)
session_event.load()

circuit_info = session_event.get_circuit_info()
lap = session_event.laps.pick_fastest()
pos = lap.get_pos_data()

fig, ax = plt.subplots(figsize=(10,5), facecolor=background_color)

def rotate(xy, *, angle):
    rot_mat = np.array([[np.cos(angle), np.sin(angle)],
                        [-np.sin(angle), np.cos(angle)]])
    return np.matmul(xy, rot_mat)

track = pos.loc[:, ('X', 'Y')].to_numpy()

track_angle = circuit_info.rotation / 180 * np.pi

offset_vector = [500, 0]  

rotated_track = rotate(track, angle=track_angle)
plt.plot(rotated_track[:, 0], rotated_track[:, 1], color ='tab:orange')

# Iterate over all corners.
for _, corner in circuit_info.corners.iterrows():
    # Create a string from corner number and letter
    txt = f"{corner['Number']}{corner['Letter']}"

    # Convert the angle from degrees to radian.
    offset_angle = corner['Angle'] / 180 * np.pi

    # Rotate the offset vector so that it points sideways from the track.
    offset_x, offset_y = rotate(offset_vector, angle=offset_angle)

    # Add the offset to the position of the corner
    text_x = corner['X'] + offset_x
    text_y = corner['Y'] + offset_y

    # Rotate the text position equivalently to the rest of the track map
    text_x, text_y = rotate([text_x, text_y], angle=track_angle)

    # Rotate the center of the corner equivalently to the rest of the track map
    track_x, track_y = rotate([corner['X'], corner['Y']], angle=track_angle)

    # Draw a circle next to the track.
    plt.scatter(text_x, text_y, color=circle_color, s=140)

    # Draw a line from the track to this circle.
    plt.plot([track_x, text_x], [track_y, text_y], color=line_color)

    # Finally, print the corner number inside the circle.
    plt.text(text_x, text_y, txt,
             va='center_baseline', ha='center', size='small', color=text_color)
    
    plot_title = f"{year} | {gp} | {session_event.event['Location']} "

plt.title(plot_title, color=title_color, fontsize = 16)
plt.xticks([])
plt.yticks([])
plt.axis('equal')

plt.show()

