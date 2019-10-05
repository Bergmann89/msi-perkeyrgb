import math
import struct

NB_KEYS = 42
REGION_ID_CODES = {"alphanum": 0x2a, "enter": 0x0b, "modifiers": 0x18, "numpad": 0x24}


def make_key_colors_packet(region, colors_map, effect_map):

    packet = []

    region_hexcode = REGION_ID_CODES[region]
    header = [0x0e, 0x00, region_hexcode, 0x00]
    packet += header

    k = 0
    for keycode, blkobj in colors_map.items():

        if blkobj.mode == 1:
            effect_id = 0
        else:
            blkobj.color = [0x00, 0x00, 0x00]
            effect_id = effect_map[blkobj.effect_name].identifier

        key_fragment = blkobj.color + [0x00, 0x00, 0x00, 0x00, 0x00] + [effect_id] + [blkobj.mode] + [0x00] + [keycode]
        packet += key_fragment
        k += 1

    while k < NB_KEYS:

        packet += ([0x00] * 12)
        k += 1

    packet += [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x08, 0x39]

    return packet


def make_effect_packet(effect_entry):

    # see '0b_packet_information/msi_kb_effectdoc' for information on how this works.

    packet = []
    header = [0x0b, 0x00]
    packet += header
    period = 0

    current_color = [0x00, 0x00, 0x00]

    # begin transition blocks
    x = 0
    for transition in effect_entry.transition_list:
        if x == 0:
            packet += effect_entry.identifier.to_bytes(1, 'little')
            current_color = effect_entry.start_color
        else:
            packet += x.to_bytes(1, 'little')

        packet += [0x00]

        # Delta calculation.
        color_delta = calculate_color_delta(current_color, transition.color)
        packet += color_delta

        packet += [0x00]

        packet += transition.duration.to_bytes(2, 'little')
        period += transition.duration

        current_color = transition.color
        x += 1

    if x < 16:
        packet += [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00] * (16 - x)

    packet += [0x00, 0x00]

    packet += get_color_starting_bytes(effect_entry.start_color)

    packet += [0xff, 0x00, 0x00, 0x00, 0x00, 0x00]

    # this appear to correspond to additional effects, such as wave mode.
    # TODO: Decipher and implement.
    packet += [0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

    packet += [len(effect_entry.transition_list)]

    packet += [0x00, 0x00, 0x00, 0x00]

    # Final duration
    packet += period.to_bytes(2, 'little')

    # Final packet filler bytes
    packet += [0x00] * 366

    return packet


def calculate_color_delta(start, target):
    delta_red = math.floor((target[0] - start[0]) / 16)
    delta_green = math.floor((target[1] - start[1]) / 16)
    delta_blue = math.floor((target[2] - start[2]) / 16)

    if delta_red < 0:
        delta_red = 256 + delta_red
    if delta_green < 0:
        delta_green = 256 + delta_green
    if delta_blue < 0:
        delta_blue = 256 + delta_blue

    return [delta_red, delta_green, delta_blue]


def get_color_starting_bytes(color):
    color_bytes = []

    red = color[0]
    green = color[1]
    blue = color[2]

    color_bytes += [((red & 0b00001111) << 4), ((red & 0b11110000) >> 4)]
    color_bytes += [((green & 0b00001111) << 4), ((green & 0b11110000) >> 4)]
    color_bytes += [((blue & 0b00001111) << 4), ((blue & 0b11110000) >> 4)]

    return color_bytes


def make_refresh_packet():

    packet = [0x09] + [0x00] * 63

    return packet
