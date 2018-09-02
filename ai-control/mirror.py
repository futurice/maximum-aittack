import os, json
from PIL import Image
import numpy as np
from skimage import io

basePath = './log/log_joku/'
json_files = [pos_json for pos_json in os.listdir(basePath) if pos_json.endswith('.json')]

for file in json_files:
    if file != 'meta.json':
        #print(file)
        with open(basePath + file) as f:
            data = json.load(f)
            index = data.get('cam/image_array').split('_')[1].split('.')[0]
            if (int(index) % 1000) == 0:
                print(index)
            #print(index)
            imgPath = basePath + data.get('cam/image_array')
            img = Image.open(imgPath)
            imgFlipped = np.fliplr(img)
            flippedImgName = 'shotflipped_' + index + '.png'
            io.imsave(basePath + flippedImgName, imgFlipped)
            data['cam/image_array'] = flippedImgName
            data['user/angle'] = data.get('user/angle') * -1
            with open(basePath + 'recordflipped_' + index + '.json', 'w') as outfile:
                json.dump(data, outfile)
