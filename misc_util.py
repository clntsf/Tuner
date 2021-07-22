from math import log

# Stores notes of the chromatic scale for referencing
notes=['A','A#','B','C','C#','D','D#','E','F','F#','G','G#']

# Constructs a major scale starting from a given number note
default_scales ={
    'maj_scale': ['Maj. Scale',[0,2,4,5,7,9,11]],
    # 'natural_min_scale': ['Min. Natural Scale', [0,2,3,5,7,8,10]],
    # 'harmonic_min_scale': ['Harmonic Min. Scale', [0,2,3,5,7,8,11]],
    # 'melodic_min_scale': ['Melodic Min. Scale', [0,2,3,5,7,9,11]]
}
def construct_default_scale(note: int, scale_key: str) -> list:
    return [(note+n)%12 or 12 for n in default_scales[scale_key][1]]

# Converts notes in string form to their number equivalents, with A as key 1
def str_scale_to_numbers(scale):
    return sorted([notes.index(note.upper())+1 for note in scale])

# Converts notes in number form to their string equivalents, with A as key 1
def num_scale_to_strs(scale):
    return [notes[note-1] for note in sorted(scale)]

# Converts note number to frequency
def to_freq(note):
    return 27.5 * (2 ** ((note - 1) / 12))

# Converts frequency to note number
def to_note(freq):
    return log(freq/27.5, 2**(1/12))+1

# Get closest element to a target item in a list
def get_closest(pool: list, target: int or float):
    return min(pool, key=lambda x: abs(x-target))

# Get all valid note frequencies given a scale of notes
def construct_note_freqs(scale):
    try: return [to_freq((12*i)+j) for i in range(8) for j in scale if 12*i+j<=88]
    except TypeError: print(scale, [repr(n) for n in scale])

# Sanitizes the output filepath for subprocess.run
def sanitize_filepath(filepath):
	for n in ['\\',"'",' ','"']: filepath = filepath.replace(n, f'\{n}')
	return filepath

# Custom floor and ceil functions
def qceil(n:float) -> int: return int(n)+bool(n%1)
def qfloor(n:float) -> int: return int(n)-bool(n%1)
