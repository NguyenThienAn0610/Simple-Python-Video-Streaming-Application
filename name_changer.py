import os
from os import path

folder_name = "Astronomia1"
pic_path = os.getcwd() + '\\' + folder_name
for index, file in enumerate(os.listdir(folder_name)):
    os.rename(os.path.join(pic_path, file), os.path.join(pic_path, ''.join([str(index+451), '.jpg'])))
