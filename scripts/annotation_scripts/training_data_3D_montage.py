"""
training_data_3D_montage.py

Code for creating montages of 3D image stacks to aid image annotaters

@author: David Van Valen
"""

"""
Import python packages
"""

from deepcell import get_image, get_images_from_directory
import numpy as np
import skimage as sk
import os
import tifffile as tiff
from scipy import ndimage
import scipy


"""
Load images
"""

cell_types = ["MouseBrain"]
list_of_number_of_sets = [2]
channel_names = ["nuclear"]

base_direc = "/home/vanvalen/Data/training_data/nuclear/"
save_subdirec = "Montage"
data_subdirec = "Processed"

for cell_type, number_of_sets, channel_name in zip(cell_types, list_of_number_of_sets, channel_names):
	for set_number in xrange(number_of_sets):
		direc = os.path.join(base_direc, cell_type, "set" + str(set_number))
		save_direc = os.path.join(direc, save_subdirec)
		directory = os.path.join(direc, data_subdirec)

		# Check if directory to save images is made. If not, then make it
		if os.path.isdir(save_direc) is False:
			os.mkdir(save_direc)

		images = get_images_from_directory(directory, [channel_name])

		print directory, images[0].shape

		number_of_images = len(images)

		image_size = images[0].shape

		crop_size_x = image_size[2]/4
		crop_size_y = image_size[3]/4

		for i in xrange(4):
			for j in xrange(4):
				list_of_cropped_images = []
				for stack_number in xrange(number_of_images):
					img = images[stack_number][0,0,:,:]
					cropped_image = img[i*crop_size_x:(i+1)*crop_size_x, j*crop_size_y:(j+1)*crop_size_y]
					list_of_cropped_images += [cropped_image]

				list_0 = list_of_cropped_images[0:10]
				list_1 = list_of_cropped_images[10:20]
				list_2 = list_of_cropped_images[20:30]

				montage_0 = np.concatenate(list_0, axis = 1)
				montage_1 = np.concatenate(list_1, axis = 1)
				montage_2 = np.concatenate(list_2, axis = 1)

				list_3 = [montage_0, montage_1, montage_2]
				montage = np.concatenate(list_3, axis = 0)

				montage_name = os.path.join(save_direc, "montage_" + str(i) + "_" + str(j) + ".png")
				scipy.misc.imsave(montage_name, montage)




