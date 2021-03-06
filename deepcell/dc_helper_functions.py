"""
dc_helper_functions.py

Functions for making training data

@author: David Van Valen
"""

"""
Import python packages
"""

import numpy as np
from numpy import array
import matplotlib
matplotlib.use('TkAgg')
matplotlib.get_backend()
import matplotlib.pyplot as plt
import shelve
from contextlib import closing

import os
import glob
import re
import numpy as np
import fnmatch
import tifffile as tiff
from numpy.fft import fft2, ifft2, fftshift
from skimage.io import imread
from scipy import ndimage
import threading
import scipy.ndimage as ndi
from scipy import linalg
import re
import random
import itertools
import h5py
import datetime

from skimage.measure import label, regionprops
from skimage.segmentation import clear_border
from scipy.ndimage.morphology import binary_fill_holes
from skimage import morphology as morph
from numpy.fft import fft2, ifft2, fftshift
from skimage.io import imread
from skimage.filters import threshold_otsu
import skimage as sk
from sklearn.utils.linear_assignment_ import linear_assignment
from sklearn.utils import class_weight
from scipy.ndimage.filters import uniform_filter


import tensorflow as tf
from tensorflow import keras
from tensorflow.python.keras import backend as K
from tensorflow.python.keras.layers import Layer, InputSpec, Input, Activation, Dense, Flatten, BatchNormalization, Conv2D, MaxPool2D, AvgPool2D, Concatenate
from tensorflow.python.keras.preprocessing.image import random_rotation, random_shift, random_shear, random_zoom, random_channel_shift, apply_transform, flip_axis, array_to_img, img_to_array, load_img, ImageDataGenerator, Iterator, NumpyArrayIterator, DirectoryIterator
from tensorflow.python.keras.callbacks import ModelCheckpoint, LearningRateScheduler
from tensorflow.python.keras import activations, initializers, losses, regularizers, constraints
from tensorflow.python.keras._impl.keras.utils import conv_utils

"""
Helper functions
"""

def cf(x,y,sample_image):
	numrows, numcols = sample_image.shape
	col = int(x+0.5)
	row = int(y+0.5)
	if col>= 0 and col<numcols and row>=0 and row<numrows:
		z = sample_image[row,col]
		return 'x=%1.4f, y=%1.4f, z=%1.4f'%(x,y,z)
	else:
		return 'x=%1.4f, y=1.4%f'%(x,y)

def axis_softmax(x, axis = 1):
	return activations.softmax(x, axis = axis)

def rotate_array_0(arr):
	return arr

def rotate_array_90(arr):
	axes_order = range(arr.ndim - 2) + [arr.ndim-1, arr.ndim-2]
	slices = [slice(None) for _ in range(arr.ndim-2)] + [slice(None),slice(None,None,-1)]
	return arr[tuple(slices)].transpose(axes_order)

def rotate_array_180(arr):
	slices = [slice(None) for _ in range(arr.ndim-2)] + [slice(None,None,-1), slice(None,None,-1)]
	return arr[tuple(slices)]

def rotate_array_270(arr):
	axes_order = range(arr.ndim-2) + [arr.ndim-1, arr.ndim-2]
	slices = [slice(None) for _ in range(arr.ndim-2)] + [slice(None,None,-1), slice(None)]
	return arr[tuple(slices)].transpose(axes_order)

def to_categorical(y, num_classes=None):
	"""Converts a class vector (integers) to binary class matrix.
	E.g. for use with categorical_crossentropy.
	# Arguments
		y: class vector to be converted into a matrix
		(integers from 0 to num_classes).
		num_classes: total number of classes.
	# Returns
		A binary matrix representation of the input.
	"""
	y = np.array(y, dtype='int').ravel()
	if not num_classes:
		num_classes = np.max(y) + 1
	n = y.shape[0]
	categorical = np.zeros((n, num_classes))
	categorical[np.arange(n), y] = 1
	return categorical


def normalize(x, axis=-1, order=2):
	"""Normalizes a Numpy array.
	# Arguments
		x: Numpy array to normalize.
		axis: axis along which to normalize.
		order: Normalization order (e.g. 2 for L2 norm).
	# Returns
		A normalized copy of the array.
	"""
	l2 = np.atleast_1d(np.linalg.norm(x, order, axis))
	l2[l2 == 0] = 1
	return x / np.expand_dims(l2, axis)

def get_image_sizes(data_location, channel_names):
	img_list_channels = []
	for channel in channel_names:
		img_list_channels += [nikon_getfiles(data_location, channel)]
	img_temp = get_image(os.path.join(data_location, img_list_channels[0][0]))

	return img_temp.shape

def rate_scheduler(lr = .001, decay = 0.95):
	def output_fn(epoch):
		epoch = np.int(epoch)
		new_lr = lr * (decay ** epoch)
		return new_lr
	return output_fn

def window_stdev(arr, radius, epsilon = 1e-7):
    c1 = uniform_filter(arr, radius*2+1, mode='constant', origin=-radius)
    c2 = uniform_filter(arr*arr, radius*2+1, mode='constant', origin=-radius)
    return ((c2 - c1*c1)**.5) + epsilon

def process_image(channel_img, win_x, win_y, std = False, remove_zeros = False):
	if std:
		avg_kernel = np.ones((2*win_x + 1, 2*win_y + 1))
		channel_img -= ndimage.convolve(channel_img, avg_kernel)/avg_kernel.size
		# std = np.std(channel_img)
		std = window_stdev(channel_img, win_x)
		channel_img /= std
		return channel_img

	if remove_zeros:
		channel_img /= np.amax(channel_img)
		avg_kernel = np.ones((2*win_x + 1, 2*win_y + 1))
		channel_img -= ndimage.convolve(channel_img, avg_kernel)/avg_kernel.size
		return channel_img

	else:
		p50 = np.percentile(channel_img, 50)
		channel_img /= p50
		avg_kernel = np.ones((2*win_x + 1, 2*win_y + 1))
		channel_img -= ndimage.convolve(channel_img, avg_kernel)/avg_kernel.size
		return channel_img


def get_image(file_name):
	if '.tif' in file_name:
		im = np.float32(tiff.TIFFfile(file_name).asarray())
	else:
		im = np.float32(imread(file_name))
	return im

def format_coord(x,y,sample_image):
	numrows, numcols = sample_image.shape
	col = int(x+0.5)
	row = int(y+0.5)
	if col>= 0 and col<numcols and row>=0 and row<numrows:
		z = sample_image[row,col]
		return 'x=%1.4f, y=%1.4f, z=%1.4f'%(x,y,z)
	else:
		return 'x=%1.4f, y=1.4%f'%(x,y)

def nikon_getfiles(direc_name,channel_name):
	imglist = os.listdir(direc_name)
	imgfiles = [i for i in imglist if channel_name in i]

	def sorted_nicely(l):
		convert = lambda text: int(text) if text.isdigit() else text
		alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
		return sorted(l, key = alphanum_key)

	imgfiles = sorted_nicely(imgfiles)
	return imgfiles

def get_image_sizes(data_location, channel_names):
	img_list_channels = []
	for channel in channel_names:
		img_list_channels += [nikon_getfiles(data_location, channel)]
	img_temp = get_image(os.path.join(data_location, img_list_channels[0][0]))

	return img_temp.shape
	
def get_images_from_directory(data_location, channel_names):
	img_list_channels = []
	for channel in channel_names:
		img_list_channels += [nikon_getfiles(data_location, channel)]

	img_temp = get_image(os.path.join(data_location, img_list_channels[0][0]))

	n_channels = len(channel_names)
	all_images = []

	for stack_iteration in xrange(len(img_list_channels[0])):
		all_channels = np.zeros((1, n_channels, img_temp.shape[0],img_temp.shape[1]), dtype = 'float32')
		for j in xrange(n_channels):
			channel_img = get_image(os.path.join(data_location, img_list_channels[j][stack_iteration]))
			all_channels[0,j,:,:] = channel_img
		all_images += [all_channels]
	
	return all_images

def _to_tensor(x, dtype):
	"""Convert the input `x` to a tensor of type `dtype`.
	# Arguments
		x: An object to be converted (numpy array, list, tensors).
		dtype: The destination type.
	# Returns
		A tensor.
	"""
	x = tf.convert_to_tensor(x)
	if x.dtype != dtype:
		x = tf.cast(x, dtype)
	return x

def categorical_crossentropy(target, output, class_weights = None, axis = None, from_logits=False):
	"""Categorical crossentropy between an output tensor and a target tensor.
	# Arguments
		target: A tensor of the same shape as `output`.
		output: A tensor resulting from a softmax
		(unless `from_logits` is True, in which
		case `output` is expected to be the logits).
		from_logits: Boolean, whether `output` is the
		result of a softmax, or is a tensor of logits.
	# Returns
		Output tensor.
	"""
	# Note: tf.nn.softmax_cross_entropy_with_logits
	# expects logits, Keras expects probabilities.
	if axis is None:
		axis = len(output.get_shape()) - 1
	if not from_logits:
		# scale preds so that the class probas of each sample sum to 1
		output /= tf.reduce_sum(output,
					axis=axis,
					keep_dims=True)
		# manual computation of crossentropy
		_epsilon = _to_tensor(K.epsilon(), output.dtype.base_dtype)
		output = tf.clip_by_value(output, _epsilon, 1. - _epsilon)
		if class_weights is None:
			return - tf.reduce_sum(target * tf.log(output), axis=axis)
		else:
			return - tf.reduce_sum(tf.multiply(target * tf.log(output), class_weights), axis=axis)

	else:
		return tf.nn.softmax_cross_entropy_with_logits(labels=target,
					logits=output)

def weighted_categorical_crossentropy(target, output, n_classes = 3, axis = None, from_logits=False):
	"""Categorical crossentropy between an output tensor and a target tensor.
	Automatically computes the class weights from the target image and uses
	them to weight the cross entropy

	# Arguments
		target: A tensor of the same shape as `output`.
		output: A tensor resulting from a softmax
		(unless `from_logits` is True, in which
		case `output` is expected to be the logits).
		from_logits: Boolean, whether `output` is the
		result of a softmax, or is a tensor of logits.
	# Returns
		Output tensor.
	"""
	# Note: tf.nn.softmax_cross_entropy_with_logits
	# expects logits, Keras expects probabilities.
	if axis is None:
		axis = len(output.get_shape()) - 1
	if not from_logits:
		# scale preds so that the class probas of each sample sum to 1
		output /= tf.reduce_sum(output,
					axis=axis,
					keep_dims=True)
		# manual computation of crossentropy
		_epsilon = _to_tensor(K.epsilon(), output.dtype.base_dtype)
		output = tf.clip_by_value(output, _epsilon, 1. - _epsilon)
		target_cast = tf.cast(target, K.floatx())
		class_weights = 1.0/np.float(n_classes)*tf.divide(tf.reduce_sum(target_cast), tf.reduce_sum(target_cast, axis = [0,1,2]))
		print class_weights.get_shape()
		return - tf.reduce_sum(tf.multiply(target * tf.log(output), class_weights), axis=axis)

	else:
		raise Exception("weighted_categorical_crossentropy cannot take logits")

def sample_categorical_crossentropy(target, output, class_weights = None, axis = None, from_logits=False):
	"""Categorical crossentropy between an output tensor and a target tensor. Only the sampled 
	pixels are used to compute the cross entropy
	# Arguments
		target: A tensor of the same shape as `output`.
		output: A tensor resulting from a softmax
		(unless `from_logits` is True, in which
		case `output` is expected to be the logits).
		from_logits: Boolean, whether `output` is the
		result of a softmax, or is a tensor of logits.
	# Returns
		Output tensor.
	"""
	# Note: tf.nn.softmax_cross_entropy_with_logits
	# expects logits, Keras expects probabilities.
	if axis is None:
		axis = len(output.get_shape()) - 1
	if not from_logits:
		# scale preds so that the class probabilities of each sample sum to 1
		output /= tf.reduce_sum(output,
					axis=axis,
					keep_dims=True)

		# Multiply with mask so that only the sampled pixels are used
		output = tf.multiply(output, target)

		# manual computation of crossentropy
		_epsilon = _to_tensor(K.epsilon(), output.dtype.base_dtype)
		output = tf.clip_by_value(output, _epsilon, 1. - _epsilon)
		if class_weights is None:
			return - tf.reduce_sum(target * tf.log(output), axis=axis)
		else:
			return - tf.reduce_sum(tf.multiply(target * tf.log(output), class_weights), axis=axis)

	else:
		return tf.nn.softmax_cross_entropy_with_logits(labels=target,
					logits=output)

def dice_coef(y_true, y_pred, smooth = 1):
	y_true_f = K.flatten(y_true)
	y_pred_f = K.flatten(y_pred)
	intersection = K.sum(y_true_f * y_pred_f)
	return (2. * intersection + smooth) / (K.sum(y_true_f) + K.sum(y_pred_f) + smooth)

def dice_coef_loss(y_true, y_pred, smooth = 1):
	return -dice_coef(y_true, y_pred, smooth)

def discriminative_instance_loss(y_true, y_pred, delta_v = 0.5, delta_d = 1.5, order = 2, gamma = 1e-3):
	
	def temp_norm(ten, axis = -1):
		return tf.sqrt(tf.constant(1e-4, dtype = K.floatx()) + tf.reduce_sum(tf.square(ten), axis = axis))

	# y_pred = tf.divide(y_pred, tf.expand_dims(tf.norm(y_pred, ord = 2, axis = -1), axis = -1))

	# Compute variance loss
	cells_summed = tf.tensordot(y_true, y_pred, axes = [[0,1,2],[0,1,2]])
	n_pixels = tf.cast(tf.count_nonzero(y_true, axis = [0,1,2]), dtype = K.floatx()) + K.epsilon()
	n_pixels_expand = tf.expand_dims(n_pixels, axis = 1)
	mu = tf.divide(cells_summed, n_pixels_expand)

	mu_tensor = tf.tensordot(y_true, mu, axes = [[-1], [0]])
	L_var_1 = y_pred - mu_tensor
	L_var_2 = tf.square(tf.nn.relu(temp_norm(L_var_1, axis = -1) - tf.constant(delta_v, dtype = K.floatx())))
	L_var_3 = tf.tensordot(L_var_2, y_true, axes = [[0,1,2],[0,1,2]]) 
	L_var_4 = tf.divide(L_var_3, n_pixels)
	L_var = tf.reduce_mean(L_var_4)

	# Compute distance loss

	mu_a = tf.expand_dims(mu, axis = 0)
	mu_b = tf.expand_dims(mu, axis = 1)


	diff_matrix = tf.subtract(mu_a, mu_b)
	L_dist_1 = temp_norm(diff_matrix, axis = -1)
	L_dist_2 = tf.square(tf.nn.relu(tf.constant(2*delta_d, dtype = K.floatx()) - L_dist_1))
	diag = tf.constant(0, shape = [51], dtype = K.floatx())
	L_dist_3 = tf.matrix_set_diag(L_dist_2, diag)
	L_dist = tf.reduce_mean(L_dist_3)

	# Compute regularization loss
	L_reg = gamma * temp_norm(mu, axis = -1)
	
	L = L_var + L_dist + L_reg

	# y_pred_square = tf.square(y_pred)
	# cells_square_summed = tf.tensordot(y_pred_square, y_true, axes = [[0,1,2],[0,1,2]]) + K.epsilon()
	# mu_square = tf.divide(cells_square_summed, n_pixels)

	# cells_var = mu_square - tf.square(mu)
	# L_var = tf.reduce_mean(cells_var)

	# num_of_cells = 20 #K.eval(tf.argmax(y_true))

	# cell_locs = []
	# cells = []
	# for cell_id in xrange(1, num_of_cells + 1):
	# 	cell_id_tensor = tf.constant(cell_id, dtype = K.floatx())
	# 	cell_loc = tf.where(tf.equal(y_true_flatten, cell_id_tensor))
	# 	cell_locs += [cell_loc] 
	# 	cells += [tf.gather(y_pred_flatten, cell_loc)]

	# mus = []
	# for cell in cells:
	# 	mus += [tf.reduce_mean(cell, axis = 0)]

	# Compute variance loss
	# L_var_cluster = []
	# for cell, mu in zip(cells, mus):
	# 	L_var_cluster += [tf.reduce_mean(tf.square(tf.nn.relu(tf.norm(-1*cell + mu, ord = 2, axis = 1) - delta_v)))]

	# L_var_stack = tf.squeeze(tf.stack(L_var_cluster, axis = 0))
	# L_var = tf.reduce_mean(L_var_stack, axis = 0)

	# Compute distance loss
	# L_dist_cluster = []
	# for i, mua in enumerate(mus):
	# 	for j, mub in enumerate(mus):
	# 		if i > j:
	# 			L_dist_cluster += [tf.square(tf.nn.relu(-tf.norm(mua-mub, ord = 2) + 2*delta_d))]
	# L_dist_stack = tf.squeeze(tf.stack(L_dist_cluster, axis = 0))
	# L_dist = tf.reduce_mean(L_dist_stack, axis = 0)

	# Compute regularization loss
	# L_reg_stack = tf.squeeze(tf.stack(mus, axis = 0))
	# L_reg = tf.reduce_mean(L_reg_stack, axis = 0)

	return L

def data_generator(channels, batch, feature_dict = None, mode = 'sample', labels = None, pixel_x = None, pixel_y = None, win_x = 30, win_y = 30):
	if mode == 'sample':
		img_list = []
		l_list = []
		for b, x, y, l in zip(batch, pixel_x, pixel_y, labels):
			img = channels[b,:, x-win_x:x+win_x+1, y-win_y:y+win_y+1]
			img_list += [img]
			l_list += [l]
		return np.stack(tuple(img_list),axis = 0), np.array(l_list)

	if mode == 'conv' or mode == 'conv_sample':
		img_list = []
		l_list = []
		for b in batch:
			img_list += [channels[b,:,:,:]]
			l_list += [labels[b,:,:,:]]
		img_list = np.stack(tuple(img_list), axis = 0).astype(K.floatx())
		l_list = np.stack(tuple(l_list), axis = 0)
		return img_list, l_list

	if mode == 'conv_gather':
		img_list = []
		l_list = []
		batch_list = []
		row_list = []
		col_list = []
		feature_dict_new = {}
		for b_new, b in enumerate(batch):
			img_list += [channels[b,:,:,:]]
			l_list += [labels[b,:,:,:]]
			batch_list = feature_dict[b][0] - np.amin(feature_dict[b][0])
			row_list = feature_dict[b][1]
			col_list = feature_dict[b][2]
			l_list = feature_dict[b][3]
			feature_dict_new[b_new] = (batch_list, row_list, col_list, l_list)
		img_list = np.stack(tuple(img_list), axis = 0).astype(K.floatx())

		return img_list, feature_dict_new

	if mode == 'movie':
		img_list = []
		l_list = []
		for b in batch:
			img_list += [channels[b,:,:,:,:]]
			l_list += [labels[b,:,:,:]]
		img_list = np.stack(tuple(img_list), axis = 0).astype(K.floatx())
		l_list = np.stack(tuple(l_list), axis = 0)
		return img_list, l_list

def get_data(file_name, mode = 'sample'):
	if mode == 'sample':
		training_data = np.load(file_name)
		channels = training_data["channels"]
		batch = training_data["batch"]
		labels = training_data["y"]
		pixels_x = training_data["pixels_x"]
		pixels_y = training_data["pixels_y"]
		win_x = training_data["win_x"]
		win_y = training_data["win_y"]

		total_batch_size = len(labels)
		num_test = np.int32(np.floor(np.float(total_batch_size)/10))
		num_train = np.int32(total_batch_size - num_test)
		full_batch_size = np.int32(num_test + num_train)

		"""
		Split data set into training data and validation data
		"""
		arr = np.arange(len(labels))
		arr_shuff = np.random.permutation(arr)

		train_ind = arr_shuff[0:num_train]
		test_ind = arr_shuff[num_train:num_train+num_test]

		X_test, y_test = data_generator(channels.astype(K.floatx()), batch[test_ind], pixel_x = pixels_x[test_ind], pixel_y = pixels_y[test_ind], labels = labels[test_ind], win_x = win_x, win_y = win_y)
		train_dict = {"channels": channels.astype(K.floatx()), "batch": batch[train_ind], "pixels_x": pixels_x[train_ind], "pixels_y": pixels_y[train_ind], "labels": labels[train_ind], "win_x": win_x, "win_y": win_y}
		
		return train_dict, (X_test, y_test)

	elif mode == "conv" or mode == "conv_sample":
		training_data = np.load(file_name)
		channels = training_data["channels"]
		labels = training_data["y"]
		if mode == "conv_sample":
			labels = training_data["y_sample"]
		class_weights = training_data["class_weights"]
		win_x = training_data["win_x"]
		win_y = training_data["win_y"]

		total_batch_size = channels.shape[0]
		num_test = np.int32(np.ceil(np.float(total_batch_size)/10))
		num_train = np.int32(total_batch_size - num_test)
		full_batch_size = np.int32(num_test + num_train)

		print total_batch_size, num_test, num_train

		"""
		Split data set into training data and validation data
		"""
		arr = np.arange(total_batch_size)
		arr_shuff = np.random.permutation(arr)

		train_ind = arr_shuff[0:num_train]
		test_ind = arr_shuff[num_train:]

		train_imgs, train_labels = data_generator(channels, train_ind, labels = labels, mode = mode)
		test_imgs, test_labels = data_generator(channels, test_ind, labels = labels, mode = mode)

		# test_labels = np.moveaxis(test_labels, 1, 3)
		train_dict = {"channels": train_imgs, "labels": train_labels, "class_weights": class_weights, "win_x": win_x, "win_y": win_y}

		# fig,ax = plt.subplots(labels.shape[0], labels.shape[1] + 1, squeeze = False)
		# max_plotted = labels.shape[0]

		return train_dict, (test_imgs, test_labels)

	elif mode == 'conv_gather':
		training_data = np.load(file_name)
		channels = training_data["channels"]
		labels = training_data["y"]
		win_x = training_data["win_x"]
		win_y = training_data["win_y"]
		feature_dict = training_data["feature_dict"]
		class_weights = training_data["class_weights"]

		total_batch_size = channels.shape[0]
		num_test = np.int32(np.ceil(np.float(total_batch_size)/10))
		num_train = np.int32(total_batch_size - num_test)
		full_batch_size = np.int32(num_test + num_train)

		print total_batch_size, num_test, num_train

		"""
		Split data set into training data and validation data
		"""
		arr = np.arange(total_batch_size)
		arr_shuff = np.random.permutation(arr)

		train_ind = arr_shuff[0:num_train]
		test_ind = arr_shuff[num_train:]

		train_imgs, train_gather_dict = data_generator(channels, train_ind, feature_dict = feature_dict, labels = labels, mode = mode)
		test_imgs, test_gather_dict = data_generator(channels, test_ind, feature_dict = feature_dict, labels = labels, mode = mode)


def transform_matrix_offset_center(matrix, x, y):
	o_x = float(x) / 2 + 0.5
	o_y = float(y) / 2 + 0.5
	offset_matrix = np.array([[1, 0, o_x], [0, 1, o_y], [0, 0, 1]])
	reset_matrix = np.array([[1, 0, -o_x], [0, 1, -o_y], [0, 0, 1]])
	transform_matrix = np.dot(np.dot(offset_matrix, matrix), reset_matrix)
	return transform_matrix

def flip_axis(x, axis):
	x = np.asarray(x).swapaxes(axis, 0)
	x = x[::-1, ...]
	x = x.swapaxes(0, axis)
	return x


