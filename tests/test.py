import sys, os
import numpy as np

from skimage import data
from scipy.ndimage.filters import gaussian_filter

source_dir = os.path.dirname(os.path.realpath(__file__))
pyfibre_dir = source_dir[:source_dir.rfind(os.path.sep)]
sys.path.append(pyfibre_dir + '/src/')

THRESH = 1E-7

def create_images(N=50):

	test_images = {}

	"Make ringed test image"
	image_grid = np.mgrid[:N, :N]
	for i in range(2): image_grid[i] -= N * np.array(2 * image_grid[i] / N, dtype=int)
	image_grid = np.fft.fftshift(np.sqrt(np.sum(image_grid**2, axis=0)))
	test_images['test_image_rings'] = np.sin(10 * np.pi * image_grid / N ) * np.cos(10 * np.pi * image_grid / N)

	"Make circular test image"
	image_grid = np.mgrid[:N, :N]
	for i in range(2): image_grid[i] -= N * np.array(2 * image_grid[i] / N, dtype=int)
	image_grid = np.fft.fftshift(np.sqrt(np.sum(image_grid**2, axis=0)))
	test_images['test_image_circle'] = 1 - gaussian_filter(image_grid, N / 4, 5)

	"Make linear test image"
	test_image = np.zeros((N, N))
	for i in range(4): test_image += np.eye(N, N, k=5-i)
	test_images['test_image_line'] = test_image

	"Make crossed test image"
	test_image = np.zeros((N, N))
	for i in range(4): test_image += np.eye(N, N, k=5-i)
	for i in range(4): test_image += np.rot90(np.eye(N, N, k=5-i))
	test_images['test_image_cross'] = np.where(test_image != 0, 1, 0)

	"Make noisy test image"
	test_images['test_image_noise'] = np.random.random((N, N))

	"Make checkered test image"
	test_images['test_image_checker'] = data.checkerboard()

	return test_images


def test_string_functions():

	from utilities import check_string, check_file_name

	string = "/dir/folder/test_file_SHG.pkl"

	assert check_string(string, -2, '/', 'folder') == "/dir/test_file_SHG.pkl"
	assert check_file_name(string, 'SHG', 'pkl') == "/dir/folder/test_file"


def test_numeric_functions():

	from utilities import unit_vector, numpy_remove, nanmean, ring, matrix_split

	vector = np.array([-3, 2, 6])
	answer = np.array([-0.42857143,  0.28571429,  0.85714286])
	u_vector = unit_vector(vector)

	assert np.sum(u_vector - answer) <= THRESH

	vector_array = np.array([[3, 2, 6], [1, 2, 5], [4, 2, 5], [-7, -1, 2]])

	u_vector_array = unit_vector(vector_array)

	assert np.array(vector_array).shape == u_vector_array.shape

	array_1 = np.arange(50)
	array_2 = array_1 + 20
	answer = np.arange(20)

	edit_array = numpy_remove(array_1, array_2)

	assert abs(answer - edit_array).sum() <= THRESH

	array_nan = np.array([2, 3, 1, np.nan])

	assert nanmean(array_nan) == 2

	ring_answer = np.array([[0, 0, 0, 0, 0, 0],
						 [0, 1, 1, 1, 0, 0],
						 [0, 1, 0, 1, 0, 0],
						 [0, 1, 1, 1, 0, 0],
						 [0, 0, 0, 0, 0, 0],
						 [0, 0, 0, 0, 0, 0]])

	ring_filter = ring(np.zeros((6, 6)), [2, 2], [1], 1)

	assert abs(ring_answer - ring_filter).sum() <= THRESH

	split_filter = matrix_split(ring_answer, 2, 2)

	assert abs(split_filter[0] - np.array([[0, 0, 0], [0, 1, 1], [0, 1, 0]])).sum() <= THRESH
	assert abs(split_filter[1] - np.array([[0, 0, 0], [1, 0, 0], [1, 0, 0]])).sum() <= THRESH
	assert abs(split_filter[2] - np.array([[0, 1, 1], [0, 0, 0], [0, 0, 0]])).sum() <= THRESH
	assert abs(split_filter[3] - np.array([[1, 0, 0], [0, 0, 0], [0, 0, 0]])).sum() <= THRESH


def test_FIRE():

	from extraction import (check_2D_arrays, distance_matrix, branch_angles, 
						cos_sin_theta_2D)

	pos_2D = np.array([[1, 3],
					   [4, 2],
					   [1, 5]])

	indices = check_2D_arrays(pos_2D, pos_2D + 1.5, 2)
	assert indices[0] == 2
	assert indices[1] == 0

	answer_d_2D = np.array([[[0, 0], [3, -1], [0, 2]],
							[[-3, 1], [0, 0], [-3, 3]],
							[[0, -2], [3, -3], [0, 0]]])
	answer_r2_2D = np.array([[0, 10, 4], 
							 [10, 0, 18], 
							 [4, 18, 0]])
	d_2D, r2_2D = distance_matrix(pos_2D)

	assert abs(answer_d_2D - d_2D).sum() <= THRESH
	assert abs(answer_r2_2D - r2_2D).sum() <= THRESH

	direction = np.array([1, 0])
	vectors = d_2D[([2, 0], [0, 1])]
	r = np.sqrt(r2_2D[([2, 0], [0, 1])])

	answer_cos_the = np.array([0, 0.9486833])
	cos_the = branch_angles(direction, vectors, r)
	assert abs(answer_cos_the - cos_the).sum() <= THRESH


def test_image():

	from main import analyse_image
	from utilities import get_image_lists, check_analysis
	from preprocessing import load_shg_pl, clip_intensities, nl_means
	from skimage.exposure import equalize_adapthist

	input_files = [pyfibre_dir + '/tests/stubs/test-pyfibre-pl-shg-Stack.tif']
	files, prefixes = get_image_lists(input_files)

	assert len(files[0]) == 1
	assert prefixes[0] ==  pyfibre_dir + '/tests/stubs/test-pyfibre'

	for i, input_file_names in enumerate(files):
		image_path = '/'.join(prefixes[i].split('/')[:-1])
		prefix = prefixes[i]

		image_name = prefix.split('/')[-1]
		#filename = '{}'.format(data_dir + image_name)

		assert image_name == 'test-pyfibre'
			
		"Load and preprocess image"
		image_shg, image_pl, image_tran = load_shg_pl(input_file_names)

		assert image_shg.shape == image_pl.shape == image_tran.shape == (200, 200)
		assert abs(image_shg.mean() - 0.08748203125) <= THRESH
		assert abs(image_pl.mean() - 0.1749819688) <= THRESH
		assert abs(image_tran.mean() - 0.760068620443) <= THRESH

		shg_analysis, pl_analysis = check_analysis(image_shg, image_pl, image_tran)

		assert shg_analysis
		assert pl_analysis
	
		image_shg = clip_intensities(image_shg, p_intensity=(1, 99))
		image_pl = clip_intensities(image_pl, p_intensity=(1, 99))

		assert abs(image_shg.mean() - 0.17330076923) <= THRESH
		assert abs(image_pl.mean() - 0.290873620689) <= THRESH

		image_shg = equalize_adapthist(image_shg)

		assert abs(image_shg.mean() - 0.2386470675) <= THRESH

		image_nl = nl_means(image_shg)

		assert abs(image_nl.mean() - 0.222907340231) <= THRESH

		#assert not True
