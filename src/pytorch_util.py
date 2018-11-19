import torch 
import torch.nn as nn
import torch.nn.functional as F 
from torch.autograd import Variable
import numpy as np
import cv2 


def unique(tensor):
	tensor_np = tensor.cpu().numpy()
	unique_np = np.unique(tensor_np)
	unique_tensor = torch.from_numpy(unique_np)

	tensor_res = tensor.new(unique_tensor.shape)
	tensor_res.copy_(unique_tensor)
	return tensor_res


def write_results(prediction, confidence, num_classes, nms_conf = 0.4):

	conf_mask = (prediction[:,:,4] > confidence).float().unsqueeze(2)
	prediction = prediction*conf_mask

	box_corner = prediction.new(prediction.shape)
	box_corner[:,:,0] = (prediction[:,:,0] - prediction[:,:,2]/2)
	box_corner[:,:,1] = (prediction[:,:,1] - prediction[:,:,3]/2)
	box_corner[:,:,2] = (prediction[:,:,0] + prediction[:,:,2]/2) 
	box_corner[:,:,3] = (prediction[:,:,1] + prediction[:,:,3]/2)
	prediction[:,:,:4] = box_corner[:,:,:4]

	batch_size = prediction.size(0)

	write = False

	for ind in range(batch_size):
		image_pred = prediction[ind]          #image Tensor
		#confidence threshholding 
		#NMS

		max_conf, max_conf_score = torch.max(image_pred[:,5:5+ num_classes], 1)
		max_conf = max_conf.float().unsqueeze(1)
		max_conf_score = max_conf_score.float().unsqueeze(1)
		seq = (image_pred[:,:5], max_conf, max_conf_score)
		image_pred = torch.cat(seq, 1)

		non_zero_ind =  (torch.nonzero(image_pred[:,4]))
		try: image_pred_ = image_pred[non_zero_ind.squeeze(),:].view(-1,7)
		except: continue

		#For PyTorch 0.4 compatibility
		#Since the above code with not raise exception for no detection 
		#as scalars are supported in PyTorch 0.4
		if image_pred_.shape[0] == 0: continue 

		#Get the various classes detected in the image
		img_classes = unique(image_pred_[:,-1]) # -1 index holds the class index


def predict_transform(prediction, inp_dim, anchors, num_classes, CUDA = True):

	batch_size = prediction.size(0)
	stride =  inp_dim // prediction.size(2)
	grid_size = prediction.size(2)
	bbox_attrs = 5 + num_classes
	num_anchors = len(anchors)

	prediction = prediction.view(batch_size, bbox_attrs*num_anchors, grid_size*grid_size)
	prediction = prediction.transpose(1,2).contiguous()
	prediction = prediction.view(batch_size, grid_size*grid_size*num_anchors, bbox_attrs)
	anchors = [(a[0]/stride, a[1]/stride) for a in anchors]

	#Sigmoid the  centre_X, centre_Y. and object confidencce
	prediction[:,:,0] = torch.sigmoid(prediction[:,:,0])
	prediction[:,:,1] = torch.sigmoid(prediction[:,:,1])
	prediction[:,:,4] = torch.sigmoid(prediction[:,:,4])

	#Add the center offsets
	grid = np.arange(grid_size)
	a,b = np.meshgrid(grid, grid)

	x_offset = torch.FloatTensor(a).view(-1,1)
	y_offset = torch.FloatTensor(b).view(-1,1)

	if CUDA:
		x_offset = x_offset.cuda()
		y_offset = y_offset.cuda()

	x_y_offset = torch.cat((x_offset, y_offset), 1).repeat(1,num_anchors).view(-1,2).unsqueeze(0)

	prediction[:,:,:2] += x_y_offset

	#log space transform height and the width
	anchors = torch.FloatTensor(anchors)

	if CUDA: anchors = anchors.cuda()

	anchors = anchors.repeat(grid_size*grid_size, 1).unsqueeze(0)
	prediction[:,:,2:4] = torch.exp(prediction[:,:,2:4])*anchors
	prediction[:,:,5: 5 + num_classes] = torch.sigmoid((prediction[:,:, 5 : 5 + num_classes]))
	prediction[:,:,:4] *= stride

	return prediction