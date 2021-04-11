import os
from os import path

folder_name = "Astronomia"
pic_path = os.getcwd() + '\\' + folder_name

print(len(os.listdir(folder_name)))
video = open(folder_name + ".mjpeg", "wb")
for i in range(len(os.listdir(folder_name))):
    pic = open(os.path.join(pic_path, str(i) + '.jpg'), "rb")
    bytes = pic.read()
    # print(str(len(bytes)).zfill(5).encode())
    video.write(str(len(bytes)).zfill(5).encode())
    video.write(bytes)
video.close()
