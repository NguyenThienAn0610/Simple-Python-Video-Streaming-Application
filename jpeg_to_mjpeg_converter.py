import os
from os import path

folder_name = "Nature"
pic_path = 'C:\LaptopD\CodeBK\ComputerNetworks202\Assigment 1\Students\\' + folder_name
for index, file in enumerate(os.listdir(pic_path)):
    try:
        os.rename(os.path.join(pic_path, file), os.path.join(pic_path, ''.join([str(index), '.jpg'])))
    except:
        pass
video = open(folder_name + ".mjpeg", "wb")
for i in range(500):
    pic = open(os.path.join(pic_path, str(i) + '.jpg'), "rb")
    bytes = pic.read()
    print(str(len(bytes)).zfill(5).encode())
    # video.write(len(bytes).to_bytes(5, 'big'))
    video.write(str(len(bytes)).zfill(5).encode())
    video.write(bytes)
video.close()
