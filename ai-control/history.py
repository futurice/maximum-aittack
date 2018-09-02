import collections
import errno
import json
import os
import re

IMAGE_HISTORY_WINDOW = 1
SENSOR_HISTORY_WINDOW = 10

IMG_KEY = 'cam/image_array'
THROTTLE_KEY = 'user/throttle'
ANGLE_KEY = 'user/angle'

basePath = './log/log_joku/'
# basePath = './log_small/'
resultPath = basePath + 'output/'
entries = [pos_json for pos_json in os.listdir(basePath) if (pos_json.endswith('.json') and pos_json != 'meta.json')]

# Sort files by the number in name, btw no error handling
entries = ((int(re.search('.+_(\d+).json', path).group(1)), path) for path in entries)

img_buffer = collections.deque(maxlen=IMAGE_HISTORY_WINDOW)
throttle_buffer = collections.deque(maxlen=SENSOR_HISTORY_WINDOW)
angle_buffer = collections.deque(maxlen=SENSOR_HISTORY_WINDOW)

if not os.path.exists(os.path.dirname(resultPath)):
    try:
        os.makedirs(os.path.dirname(resultPath))
    except OSError as exc:  # Guard against race condition
        if exc.errno != errno.EEXIST:
            raise



for cdate, file in sorted(entries):
    with open(basePath + file, 'r+') as f:
        data = json.load(f)
        aImg = data.get(IMG_KEY)
        aThrottle = data.get(THROTTLE_KEY)
        aAngle = data.get(ANGLE_KEY)
        if (len(img_buffer) < IMAGE_HISTORY_WINDOW or
                len(throttle_buffer) < SENSOR_HISTORY_WINDOW):
            print('Filling buffer')
        else:
            imgPath = basePath + data.get('cam/image_array')
            data['cam/prev_images'] = list(img_buffer)
            data['history/angle'] = list(angle_buffer)
            data['history/throttle'] = list(throttle_buffer)
            with open(resultPath + file, 'w') as outfile:
                json.dump(data, outfile)

        img_buffer.append(aImg)
        throttle_buffer.append(aThrottle)
        angle_buffer.append(aAngle)

with open(basePath + 'meta.json', 'r+') as f:
    data = json.load(f)
    data['inputs'].extend(['cam/prev_images', 'history/angle', 'history/throttle'])
    data['types'].extend(['custom/prev_image', 'custom/angle_array', 'custom/throttle_array'])
    with open(resultPath + 'meta.json', 'w') as outfile:
        json.dump(data, outfile)
