import os, sys, time
from tkinter import *
from tkinter import ttk, filedialog
import queue, threading
from multiprocessing import Pool, Process, JoinableQueue, Queue, current_process

import matplotlib
matplotlib.use("Agg")

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from PIL import ImageTk, Image
import networkx as nx
import numpy as np
import pandas as pd

from scipy.ndimage import imread
from scipy.ndimage.filters import gaussian_filter
from scipy.ndimage.morphology import binary_fill_holes, binary_dilation

from skimage import img_as_float, measure
from skimage.exposure import equalize_adapthist, rescale_intensity
from skimage.filters import threshold_otsu
from skimage.color import gray2rgb, label2rgb
from skimage.restoration import (estimate_sigma, denoise_tv_chambolle, denoise_bilateral)

from main import analyse_image
import utilities as ut
from preprocessing import load_shg_pl, clip_intensities
from segmentation import draw_network
from figures import create_tensor_image, create_region_image, create_network_image


class pyfibre_gui:

	def __init__(self, master, n_proc, n_thread):

		"Set file locations"
		self.source_dir = os.path.dirname(os.path.realpath(__file__))
		self.pyfibre_dir = self.source_dir[:self.source_dir.rfind(os.path.sep)]
		self.current_dir = os.getcwd()

		"Initiatise program log, queue and input file list"
		self.Log = "Initiating PyFibre GUI\n"
		self.queue = Queue()
		self.input_files = []
		self.input_prefixes = []
		self.n_proc = n_proc
		self.n_thread = n_thread

		"Initialise option variables"
		self.ow_metric = BooleanVar()
		self.ow_segment = BooleanVar()
		self.ow_network = BooleanVar()
		self.ow_figure = BooleanVar()
		self.save_db = BooleanVar()
		self.sigma = DoubleVar()
		self.sigma.set(0.5)
		self.p0 = IntVar()
		self.p0.set(1)
		self.p1 = IntVar()
		self.p1.set(99)
		self.n = IntVar()
		self.n.set(2)
		self.m = IntVar()
		self.m.set(25)
		self.alpha = DoubleVar()
		self.alpha.set(0.5)

		"Define GUI objects"
		self.master = master
		self.master.geometry("700x720")
		self.master.configure(background='#d8baa9')
		self.master.protocol("WM_DELETE_WINDOW", lambda: quit())

		self.title = Frame(self.master)
		self.create_title(self.title)
		self.title.place(bordermode=OUTSIDE, height=200, width=300)

		self.options = Frame(self.master)
		self.options.configure(background='#d8baa9')
		self.options.options_button = Button(self.options, width=15,
				   text="Options",
				   command=self.create_options)
		self.options.options_button.pack()
		self.options.place(x=300, y=10, height=50, width=250)

		self.file_display = Frame(self.master)
		self.create_file_display(self.file_display)
		self.file_display.place(x=5, y=220, height=600, width=1200)

		self.image_display = Frame(self.master)
		self.image_display.configure(background='#d8baa9')
		self.image_display.display_button = Button(self.image_display, width=15,
				   text="Viewer",
				   command=self.create_image_display)
		self.image_display.display_button.pack()
		self.image_display.place(x=300, y=50, height=50, width=250)


	def create_title(self, frame):

		self.master.title("PyFibre - Python Fibrous Image Analysis Toolkit")

		image = Image.open(self.pyfibre_dir + '/img/icon.ico')
		image = image.resize((300,200))
		image_tk = ImageTk.PhotoImage(image)

		self.master.tk.call('wm', 'iconphoto', self.master._w, image_tk)
		frame.text_title = Label(frame, image=image_tk)
		frame.image = image_tk
		frame.text_title.pack(side = TOP, fill = "both", expand = "yes")


	def create_options(self):

		"Initialise option parameters"
		frame = Toplevel(self.master)
		frame.tk.call('wm', 'iconphoto', frame._w, self.title.image)
		frame.title('PyFibre - Options')
		frame.geometry('310x620-100+40')

		frame.title_sigma = Label(frame, text="Gaussian Std Dev (pix)")
		frame.title_sigma.configure(background='#d8baa9')
		frame.sigma = Scale(frame, from_=0, to=10, tickinterval=1, resolution=0.1, 
				length=300, orient=HORIZONTAL, variable=self.sigma)

		frame.title_sigma.grid(column=0, row=2, rowspan=1)
		frame.sigma.grid(column=0, row=3, sticky=(N,W,E,S))

		frame.title_p0 = Label(frame, text="Low Clip Intensity (%)")
		frame.title_p0.configure(background='#d8baa9')
		frame.p0 = Scale(frame, from_=0, to=100, tickinterval=10, 
				length=300, orient=HORIZONTAL, variable=self.p0)

		frame.title_p1 = Label(frame, text="High Clip Intensity (%)")
		frame.title_p1.configure(background='#d8baa9')
		frame.p1 = Scale(frame, from_=0, to=100,tickinterval=10, 
				length=300, orient=HORIZONTAL, variable=self.p1)

		frame.title_p0.grid(column=0, row=4, rowspan=1)
		frame.p0.grid(column=0, row=5)
		frame.title_p1.grid(column=0, row=6, rowspan=1)
		frame.p1.grid(column=0, row=7)

		frame.title_n = Label(frame, text="NL-Mean Neighbourhood 1 (pix)")
		frame.title_n.configure(background='#d8baa9')
		frame.n = Scale(frame, from_=0, to=100, tickinterval=10, 
				length=300, orient=HORIZONTAL, variable=self.n)
		frame.title_m = Label(frame, text="NL-Mean Neighbourhood 2 (pix)")
		frame.title_m.configure(background='#d8baa9')
		frame.m = Scale(frame, from_=0, to=100,tickinterval=10,
				length=300, orient=HORIZONTAL, variable=self.m)

		frame.title_n.grid(column=0, row=8, rowspan=1)
		frame.n.grid(column=0, row=9)
		frame.title_m.grid(column=0, row=10, rowspan=1)
		frame.m.grid(column=0, row=11)

		frame.title_alpha = Label(frame, text="Alpha network coefficient")
		frame.title_alpha.configure(background='#d8baa9')
		frame.alpha = Scale(frame, from_=0, to=1, tickinterval=0.1, resolution=0.01,
						length=300, orient=HORIZONTAL, variable=self.alpha)

		frame.title_alpha.grid(column=0, row=12, rowspan=1)
		frame.alpha.grid(column=0, row=13)

		frame.chk_metric = Checkbutton(frame, text="o/w metrics", variable=self.ow_metric)
		frame.chk_metric.configure(background='#d8baa9')
		frame.chk_metric.grid(column=0, row=14, sticky=(N,W,E,S))
		#frame.chk_anis.pack(side=LEFT)

		frame.chk_segment = Checkbutton(frame, text="o/w segment", variable=self.ow_segment)
		frame.chk_segment.configure(background='#d8baa9')
		frame.chk_segment.grid(column=0, row=15, sticky=(N,W,E,S))
		#frame.chk_graph.pack(side=LEFT)

		frame.chk_network = Checkbutton(frame, text="o/w network", variable=self.ow_network)
		frame.chk_network.configure(background='#d8baa9')
		frame.chk_network.grid(column=0, row=16, sticky=(N,W,E,S))
		#frame.chk_graph.pack(side=LEFT)
	
		frame.chk_figure = Checkbutton(frame, text="o/w figure", variable=self.ow_figure)
		frame.chk_figure.configure(background='#d8baa9')
		frame.chk_figure.grid(column=0, row=17, sticky=(N,W,E,S))
		#frame.chk_graph.pack(side=LEFT)

		frame.chk_db = Checkbutton(frame, text="Save Database", variable=self.save_db)
		frame.chk_db.configure(background='#d8baa9')
		frame.chk_db.grid(column=0, row=18, sticky=(N,W,E,S))

		frame.configure(background='#d8baa9')


	def create_file_display(self, frame):

		frame.select_im_button = Button(frame, width=12,
				   text="Load Files",
				   command=self.add_images)
		frame.select_im_button.grid(column=0, row=0)

		frame.select_dir_button = Button(frame, width=12,
				   text="Load Folder",
				   command=self.add_directory)
		frame.select_dir_button.grid(column=1, row=0)

		frame.key = Entry(frame, width=10)
		frame.key.configure(background='#d8baa9')
		frame.key.grid(column=3, row=0, sticky=(N,W,E,S))

		frame.select_dir_button = Button(frame, width=12,
				   text="Filter",
				   command=lambda : self.del_images([filename for filename in self.input_prefixes \
							if (filename.find(frame.key.get()) == -1)]))
		frame.select_dir_button.grid(column=2, row=0)

		frame.delete_im_button = Button(frame, width=12,
				   text="Delete",
				   command=lambda : self.del_images([self.file_display.file_box.get(idx)\
							 for idx in self.file_display.file_box.curselection()]))
		frame.delete_im_button.grid(column=4, row=0)

		frame.tree = ttk.Treeview(frame, columns=('shg', 'pl'))
		frame.tree.column("#0", minwidth=20)
		frame.tree.column('shg', width=5, minwidth=5, anchor='center')
		frame.tree.heading('shg', text='SHG')
		frame.tree.column('pl', width=5, minwidth=5, anchor='center')
		frame.tree.heading('pl', text='PL')
		frame.tree.grid(column=0, row=1, columnspan=5, sticky=(N,W,E,S))

		frame.run_button = Button(frame, width=40,
				   text="GO",
				   command=self.write_run)
		frame.run_button.grid(column=0, row=2, columnspan=3)

		frame.stop_button = Button(frame, width=20,
				   text="STOP",
				   command=self.stop_run, state=DISABLED)
		frame.stop_button.grid(column=2, row=2, columnspan=3)

		frame.progress = ttk.Progressbar(frame, orient=HORIZONTAL, length=400, mode='determinate')
		frame.progress.grid(column=0, row=3, columnspan=5)

		frame.configure(background='#d8baa9')


	def add_images(self):
		
		new_files = filedialog.askopenfilenames(filetypes = (("tif files","*.tif"), ("all files","*.*")))
		new_files = list(new_files)

		files, prefixes = ut.get_image_lists(new_files)

		self.add_files(files, prefixes)


	def add_directory(self):
		
		directory = filedialog.askdirectory()
		new_files = []
		for file_name in os.listdir(directory):
			if file_name.endswith('.tif'):
				if 'display' not in file_name: 
					new_files.append( directory + '/' + file_name)

		files, prefixes = ut.get_image_lists(new_files)

		self.add_files(files, prefixes)


	def add_files(self, files, prefixes):

		new_indices = [i for i, prefix in enumerate(prefixes)\
						 if prefix not in self.input_prefixes]
		new_files = [files[i] for i in new_indices]
		new_prefixes = [prefixes[i] for i in new_indices]

		self.input_files += new_files
		self.input_prefixes += new_prefixes

		for i, filename in enumerate(new_prefixes):
			self.file_display.tree.insert('', 'end', filename, text=filename)
			self.file_display.tree.set(filename, 'shg', 'X')
			if len(new_files[i]) == 1:
				if '-pl-shg' in new_files[i][0].lower():
					self.file_display.tree.set(filename, 'pl', 'X')
				else:
					self.file_display.tree.set(filename, 'pl', '')

			if len(new_files[i]) == 2:
				self.file_display.tree.set(filename, 'pl', 'X')

			self.update_log("Adding {}".format(filename))


	def del_images(self, file_list):

		for filename in file_list:
			index = self.input_prefixes.index(filename)
			self.input_files.remove(self.input_files[index])
			self.input_prefixes.remove(filename)
			self.file_display.file_box.delete(index)
			self.update_log("Removing {}".format(filename))


	def create_image_display(self):

		self.viewer = pyfibre_viewer(self)
		self.master.bind('<Double-1>', lambda e: self.viewer.display_notebook())
		

	def generate_db(self):

		global_database = pd.DataFrame()
		fibre_database = pd.DataFrame()
		cell_database = pd.DataFrame()

		for i, input_file_name in enumerate(self.input_prefixes):

			image_name = input_file_name.split('/')[-1]
			image_path = '/'.join(input_file_name.split('/')[:-1])
			data_dir = image_path + '/data/'
			metric_name = data_dir + ut.check_file_name(image_name, extension='tif')
			
			self.update_log("Loading metrics for {}".format(metric_name))

			try:
				data_global = pd.read_pickle('{}_global_metric.pkl'.format(metric_name))
				data_fibre = pd.read_pickle('{}_fibre_metric.pkl'.format(metric_name))
				data_cell = pd.read_pickle('{}_cell_metric.pkl'.format(metric_name))

				global_database = pd.concat([global_database, data_global], sort=True)
				fibre_database = pd.concat([fibre_database, data_fibre], sort=True)
				cell_database = pd.concat([cell_database, data_cell], sort=True)
				
			except (ValueError, IOError):
				self.update_log(f"{input_file_name} databases not imported - skipping")


		self.global_database = global_database
		self.fibre_database = fibre_database
		self.cell_database = cell_database

		#self.update_dashboard()


	def save_database(self):

		db_filename = filedialog.asksaveasfilename()
		db_filename = ut.check_file_name(db_filename, extension='pkl')
		db_filename = ut.check_file_name(db_filename, extension='xls')

		self.global_database.to_pickle(db_filename + '.pkl')
		self.global_database.to_excel(db_filename + '.xls')

		self.fibre_database.to_pickle(db_filename + '_fibre.pkl')
		self.fibre_database.to_excel(db_filename + '_fibre.xls')

		self.cell_database.to_pickle(db_filename + '_cell.pkl')
		self.cell_database.to_excel(db_filename + '_cell.xls')
		

		self.update_log("Saving Database files {}".format(db_filename))


	def write_run(self):

		self.file_display.run_button.config(state=DISABLED)	
		self.file_display.stop_button.config(state=NORMAL)
		self.file_display.progress['maximum'] = len(self.input_files)

		#"""Multi Processor version
		proc_count = np.min((self.n_proc, len(self.input_files)))
		index_split = np.array_split(np.arange(len(self.input_prefixes)),
						proc_count)

		self.processes = []
		for indices in index_split:

			batch_files = [self.input_files[i] for i in indices]
			batch_prefixes = [self.input_prefixes[i] for i in indices]

			process = Process(target=image_analysis, 
					args=(batch_files, batch_prefixes,
					(self.p0.get(), self.p1.get()),
					(self.n.get(), self.m.get()),
					self.sigma.get(), self.alpha.get(),
					self.ow_metric.get(), self.ow_segment.get(),
					 self.ow_network.get(), self.ow_figure.get(), 
					self.queue, self.n_thread))
			process.daemon = True
			self.processes.append(process)

		for process in self.processes: process.start()
		#"""

		"""Serial Version
		self.process = Process(target=image_analysis, args=(self.input_files, self.ow_metric.get(),
														self.ow_network.get(), self.queue))
		self.process.daemon = True
		self.process.start()
		"""
		self.process_check()


	def process_check(self):
		"""
		Check if there is something in the queue
		"""
		self.queue_check()

		#if self.process.exitcode is None:
		if np.any([process.is_alive() for process in self.processes]):
			self.master.after(500, self.process_check)
		else: 
			self.stop_run()
			self.generate_db()
			if self.save_db.get(): self.save_database()


	def queue_check(self):

		while not self.queue.empty():
			try:
				msg = self.queue.get(0)
				self.update_log(msg)
				self.file_display.progress.configure(value=self.file_display.progress['value'] + 1)
				self.file_display.progress.update()
			except queue.Empty: pass


	def stop_run(self):

		self.update_log("Stopping Analysis")
		for process in self.processes: process.terminate()
		self.file_display.progress['value'] = 0
		self.file_display.run_button.config(state=NORMAL)
		self.file_display.stop_button.config(state=DISABLED)


	def update_log(self, text):

		self.Log += text + '\n'


def image_analysis(input_files, input_prefixes, p_intensity, p_denoise, sigma, alpha, 
			ow_metric, ow_segment, ow_network, ow_figure, 
			queue, threads):

	for input_file_names, prefix in zip(input_files, input_prefixes):

		image_path = '/'.join(prefix.split('/')[:-1])

		try:
			analyse_image(input_file_names, prefix, image_path,
					scale=1, p_intensity=p_intensity,
					p_denoise=p_denoise, sigma=sigma,
					alpha=alpha,
					ow_metric=ow_metric, ow_segment=ow_segment,
					ow_network=ow_network, ow_figure=ow_figure,
					threads=threads)
			queue.put("Analysis of {} complete".format(prefix))

		except Exception as err: queue.put("{} {}".format(err.message, prefix))


class pyfibre_viewer:

	def __init__(self, parent, width=750, height=650):

		self.parent = parent

		self.frame = Toplevel(self.parent.master)
		self.frame.tk.call('wm', 'iconphoto', self.frame._w, self.parent.title.image)
		self.frame.title('PyFibre - Viewer')
		self.frame.geometry(f"{width}x{height}-100+40")

		self.notebook = ttk.Notebook(self.frame)

		self.shg_image_tab = ttk.Frame(self.notebook)
		self.pl_image_tab = ttk.Frame(self.notebook)
		self.tensor_tab = ttk.Frame(self.notebook)
		self.network_tab = ttk.Frame(self.notebook)
		self.segment_tab = ttk.Frame(self.notebook)
		self.fibre_tab = ttk.Frame(self.notebook)
		self.cell_tab = ttk.Frame(self.notebook)
		self.metric_tab = ttk.Frame(self.notebook)

		self.tab_dict = {'SHG Image' : self.shg_image_tab,
						 'PL Image'  : self.pl_image_tab,
						 'Tensor Image': self.tensor_tab,
						 'Network' : self.network_tab,
						 'Network Segment' : self.segment_tab,
						 'Fibre' :  self.fibre_tab,
						 'Cell Segment' : self.cell_tab}
		
		for key, tab in self.tab_dict.items():
			self.notebook.add(tab, text=key)
			tab.canvas = Canvas(tab, width=width, height=height,
									scrollregion=(0,0,675,700))  
			tab.scrollbar = Scrollbar(tab, orient=VERTICAL, 
								command=tab.canvas.yview)
			tab.scrollbar.pack(side=RIGHT,fill=Y)
			tab.canvas['yscrollcommand'] = tab.scrollbar.set
			tab.canvas.pack(side = LEFT, fill = "both", expand = "yes")

		
		self.notebook.add(self.metric_tab, text='Metrics')
		self.metric_tab.metric_dict = {
			'No. Fibres' : {"info" : "Number of extracted fibres", "metric" : IntVar(), "tag" : "content"},
			'SHG Angle SDI' : {"info" : "Angle spectrum SDI of total image", "metric" : DoubleVar(), "tag" : "texture"},
			'SHG Pixel Anisotropy' : {"info" : "Average anisotropy of all pixels in total image", "metric" : DoubleVar(), "tag" : "texture"},
			'SHG Anisotropy' : {"info" : "Anisotropy of total image", "metric" : DoubleVar(), "tag" : "texture"},
			'SHG Intensity Mean' : {"info" : "Average pixel intensity of total image", "metric" : DoubleVar(), "tag" : "texture"},
			'SHG Intensity STD' : {"info" : "Pixel intensity standard deviation of total image", "metric" : DoubleVar(), "tag" : "texture"},
			'SHG Intensity Entropy' : {"info" : "Average Shannon entropy of total image", "metric" : DoubleVar(), "tag" : "texture"},						
			'Fibre GLCM Contrast' : {"info" : "SHG GLCM angle-averaged contrast", "metric" : DoubleVar(), "tag" : "texture"},
			'Fibre GLCM Homogeneity' : {"info" : "SHG GLCM angle-averaged homogeneity", "metric" : DoubleVar(), "tag" : "texture"},
			'Fibre GLCM Dissimilarity' : {"info" : "SHG GLCM angle-averaged dissimilarity", "metric" : DoubleVar(), "tag" : "texture"},
			'Fibre GLCM Correlation' : {"info" : "SHG GLCM angle-averaged correlation", "metric" : DoubleVar(), "tag" : "texture"},
			'Fibre GLCM Energy' : {"info" : "SHG GLCM angle-averaged energy", "metric" : DoubleVar(), "tag" : "texture"},
			'Fibre GLCM IDM' : {"info" : "SHG GLCM angle-averaged inverse difference moment", "metric" : DoubleVar(), "tag" : "texture"},
			'Fibre GLCM Variance' : {"info" : "SHG GLCM angle-averaged variance", "metric" : DoubleVar(), "tag" : "texture"},
			'Fibre GLCM Cluster' : {"info" : "SHG GLCM angle-averaged clustering tendency", "metric" : DoubleVar(), "tag" : "texture"},
			'Fibre GLCM Entropy' : {"info" : "SHG GLCM angle-averaged entropy", "metric" : DoubleVar(), "tag" : "texture"},
			'Fibre Area' : {"info" : "Average number of pixels covered by fibres", "metric" : DoubleVar(), "tag" : "content"},			
			'Fibre Coverage' : {"info" : "Ratio of image covered by fibres", "metric" : DoubleVar(), "tag" : "content"},
			'Fibre Linearity' : {"info" : "Average fibre segment linearity", "metric" : DoubleVar(), "tag" : "shape"},
			'Fibre Eccentricity' : {"info" : "Average fibre segment eccentricity", "metric" : DoubleVar(), "tag" : "shape"},
			'Fibre Density' : {"info" : "Average image fibre density", "metric" : DoubleVar(), "tag" : "texture"},
			'Fibre Hu Moment 1'  : {"info" : "Average fibre segment Hu moment 1", "metric" : DoubleVar(), "tag" : "shape"},
			'Fibre Hu Moment 2'  : {"info" : "Average fibre segment Hu moment 2", "metric" : DoubleVar(), "tag" : "shape"},
			'Fibre Waviness' : {"info" : "Average fibre waviness", "metric" : DoubleVar(), "tag" : "content"},
			'Fibre Lengths' : {"info" : "Average fibre pixel length", "metric" : DoubleVar(), "tag" : "content"},
			'Fibre Cross-Link Density' : {"info" : "Average cross-links per fibre", "metric" : DoubleVar(), "tag" : "content"},
			'Network Degree' : {"info" : "Average fibre network number of edges per node", "metric" : DoubleVar(), "tag" : "network"},
			'Network Eigenvalue' : {"info" : "Max Eigenvalue of network", "metric" : DoubleVar(), "tag" : "network"},
			'Network Connectivity' : {"info" : "Average fibre network connectivity", "metric" : DoubleVar(), "tag" : "network"},

			'No. Cells' : {"info" : "Number of cell segments", "metric" : IntVar(), "tag" : "content"},
			'PL Angle SDI' : {"info" : "Angle spectrum SDI of total image", "metric" : DoubleVar(), "tag" : "texture"},
			'PL Pixel Anisotropy' : {"info" : "Average anisotropy of all pixels in total image", "metric" : DoubleVar(), "tag" : "texture"},
			'PL Anisotropy' : {"info" : "Anisotropy of total image", "metric" : DoubleVar(), "tag" : "texture"},
			'PL Intensity Mean' : {"info" : "Average pixel intensity of total image", "metric" : DoubleVar(), "tag" : "texture"},
			'PL Intensity STD' : {"info" : "Pixel intensity standard deviation of total image", "metric" : DoubleVar(), "tag" : "texture"},
			'PL Intensity Entropy' : {"info" : "Average Shannon entropy of total image", "metric" : DoubleVar(), "tag" : "texture"},						
			'Cell GLCM Contrast' : {"info" : "PL GLCM angle-averaged contrast", "metric" : DoubleVar(), "tag" : "texture"},
			'Cell GLCM Homogeneity' : {"info" : "PL GLCM angle-averaged homogeneity", "metric" : DoubleVar(), "tag" : "texture"},
			'Cell GLCM Dissimilarity' : {"info" : "PL GLCM angle-averaged dissimilarity", "metric" : DoubleVar(), "tag" : "texture"},
			'Cell GLCM Correlation' : {"info" : "PL GLCM angle-averaged correlation", "metric" : DoubleVar(), "tag" : "texture"},
			'Cell GLCM Energy' : {"info" : "PL GLCM angle-averaged energy", "metric" : DoubleVar(), "tag" : "texture"},
			'Cell GLCM IDM' : {"info" : "PL GLCM angle-averaged inverse difference moment", "metric" : DoubleVar(), "tag" : "texture"},
			'Cell GLCM Variance' : {"info" : "PL GLCM angle-averaged variance", "metric" : DoubleVar(), "tag" : "texture"},
			'Cell GLCM Cluster' : {"info" : "PL GLCM angle-averaged clustering tendency", "metric" : DoubleVar(), "tag" : "texture"},
			'Cell Area' : {"info" : "Average number of pixels covered by cells", "metric" : DoubleVar(), "tag" : "content"},
			'Cell Linearity' : {"info" : "Average cell segment linearity", "metric" : DoubleVar(), "tag" : "shape"}, 
			'Cell Coverage' : {"info" : "Ratio of image covered by cell", "metric" : DoubleVar(), "tag" : "content"},		
			'Cell Eccentricity' : {"info" : "Average cell segment eccentricity", "metric" : DoubleVar(), "tag" : "shape"},				
			'Cell Density' : {"info" : "Average image cell density", "metric" : DoubleVar(), "tag" : "texture"},						
			'Cell Hu Moment 1'  : {"info" : "Average cell segment Hu moment 1", "metric" : DoubleVar(), "tag" : "shape"},
			'Cell Hu Moment 2'  : {"info" : "Average cell segment Hu moment 2", "metric" : DoubleVar(), "tag" : "shape"}
										}

		self.metric_tab.titles = list(self.metric_tab.metric_dict.keys())

		self.notebook.metrics = [DoubleVar() for i in range(len(self.metric_tab.titles))]
		self.metric_tab.headings = []
		self.metric_tab.info = []
		self.metric_tab.metrics = []

		self.metric_tab.texture = ttk.Labelframe(self.metric_tab, text="Texture",
						width=width-50, height=height-50)
		self.metric_tab.content = ttk.Labelframe(self.metric_tab, text="Content",
						width=width-50, height=height-50)
		self.metric_tab.shape = ttk.Labelframe(self.metric_tab, text="Shape",
						width=width-50, height=height-50)
		self.metric_tab.network = ttk.Labelframe(self.metric_tab, text="Network",
						width=width-50, height=height-50)
		
		self.metric_tab.frame_dict = {"texture" : {'tab' : self.metric_tab.texture, "count" : 0},
									  "content" : {'tab' : self.metric_tab.content, "count" : 0},
									  "shape"  : {'tab' : self.metric_tab.shape, "count" : 0},
									  "network" : {'tab' : self.metric_tab.network, "count" : 0}}

		for i, metric in enumerate(self.metric_tab.titles):

			tag = self.metric_tab.metric_dict[metric]["tag"]

			self.metric_tab.headings += [Label(self.metric_tab.frame_dict[tag]['tab'], 
				text="{}:".format(metric), font=("Ariel", 8))]
			self.metric_tab.info += [Label(self.metric_tab.frame_dict[tag]['tab'], 
				text=self.metric_tab.metric_dict[metric]["info"], font=("Ariel", 8))]
			self.metric_tab.metrics += [Label(self.metric_tab.frame_dict[tag]['tab'], 
				textvariable=self.metric_tab.metric_dict[metric]["metric"], font=("Ariel", 8))]

			self.metric_tab.headings[i].grid(column=0, row=self.metric_tab.frame_dict[tag]['count'])
			self.metric_tab.info[i].grid(column=1, row=self.metric_tab.frame_dict[tag]['count'])
			self.metric_tab.metrics[i].grid(column=2, row=self.metric_tab.frame_dict[tag]['count'])
			self.metric_tab.frame_dict[tag]['count'] += 1

		self.metric_tab.texture.pack()
		self.metric_tab.content.pack()
		self.metric_tab.shape.pack()
		self.metric_tab.network.pack()
		
		self.log_tab = ttk.Frame(self.notebook)
		self.notebook.add(self.log_tab, text='Log')
		self.log_tab.text = Text(self.log_tab, width=675, height=650)
		self.log_tab.text.insert(END, self.parent.Log)
		self.log_tab.text.config(state=DISABLED)

		self.log_tab.scrollbar = Scrollbar(self.log_tab, orient=VERTICAL, 
							command=self.log_tab.text.yview)
		self.log_tab.scrollbar.pack(side=RIGHT,fill=Y)
		self.log_tab.text['yscrollcommand'] = self.log_tab.scrollbar.set

		self.log_tab.text.pack()

		self.notebook.pack()
		#frame.notebook.BFrame.configure(background='#d8baa9')


	def display_image(self, canvas, image):

		canvas.delete('all')

		canvas.create_image(40, 20, image=image, anchor=NW)
		canvas.image = image
		canvas.pack(side = LEFT, fill = "both", expand = "yes")

		self.parent.master.update_idletasks()


	def display_tensor(self, canvas, image):

		tensor_image = create_tensor_image(image) * 255.999

		image_tk = ImageTk.PhotoImage(Image.fromarray(tensor_image.astype('uint8')))
		self.display_image(canvas, image_tk)


	def display_network(self, canvas, image, networks, c_mode=0):

		image_network_overlay = create_network_image(image, networks, c_mode)

		image_tk = ImageTk.PhotoImage(Image.fromarray(image_network_overlay.astype('uint8')))
		self.display_image(canvas, image_tk)


	def display_regions(self, canvas, image, regions):

		image_label_overlay = create_region_image(image, regions) * 255.999

		image_pil = Image.fromarray(image_label_overlay.astype('uint8'))
		image_tk = ImageTk.PhotoImage(image_pil)

		self.display_image(canvas, image_tk)
		canvas.create_window()

	def update_log(self, text):

		self.log_tab.text.config(state=NORMAL)
		self.parent.Log += text + '\n'
		self.log_tab.text.insert(END, text + '\n')
		self.log_tab.text.config(state=DISABLED)


	def display_notebook(self):

		selected_file = self.parent.file_display.tree.selection()[0]

		image_name = selected_file.split('/')[-1]
		image_path = '/'.join(selected_file.split('/')[:-1])
		fig_name = ut.check_file_name(image_name, extension='tif')
		data_dir = image_path + '/data/'

		file_index = self.parent.input_prefixes.index(selected_file)
		image_shg, image_pl, _ = load_shg_pl(self.parent.input_files[file_index])

		shg_analysis = ~np.any(image_shg == None)
		pl_analysis = ~np.any(image_pl == None)

		if shg_analysis:
			self.image_shg = clip_intensities(image_shg, 
					p_intensity=(self.parent.p0.get(), self.parent.p1.get())) * 255.999
			shg_image_tk = ImageTk.PhotoImage(Image.fromarray(self.image_shg.astype('uint8')))
			self.display_image(self.shg_image_tab.canvas, shg_image_tk)
			self.update_log("Displaying SHG image {}".format(fig_name))

			self.display_tensor(self.tensor_tab.canvas, self.image_shg)
			self.update_log("Displaying SHG tensor image {}".format(fig_name))

		if pl_analysis:
			self.image_pl = clip_intensities(image_pl, 
					p_intensity=(self.parent.p0.get(), self.parent.p1.get())) * 255.999

			pl_image_tk = ImageTk.PhotoImage(Image.fromarray(self.image_pl.astype('uint8')))
			self.display_image(self.pl_image_tab.canvas, pl_image_tk)
			self.update_log("Displaying PL image {}".format(fig_name))

		try:
			networks = ut.load_region(data_dir + fig_name + "_network")
			self.display_network(self.network_tab.canvas, self.image_shg, networks)
			self.update_log("Displaying network for {}".format(fig_name))
		except IOError:
			self.update_log("Unable to display network for {}".format(fig_name))

		try:
			fibres = ut.load_region(data_dir + fig_name + "_fibre")
			fibres = ut.flatten_list(fibres)
			self.display_network(self.fibre_tab.canvas, self.image_shg, fibres, 1)
			self.update_log("Displaying segments for {}".format(fig_name))
		except IOError:
			self.update_log("Unable to display segments for {}".format(fig_name))

		try:
			segments = ut.load_region(data_dir + fig_name + "_fibre_segment")
			self.display_regions(self.segment_tab.canvas, self.image_shg, segments)
			self.update_log("Displaying segments for {}".format(fig_name))
		except IOError:
			self.update_log("Unable to display segments for {}".format(fig_name))
		
		try:	
			holes = ut.load_region(data_dir + fig_name + "_cell_segment")
			self.display_regions(self.cell_tab.canvas, self.image_pl, holes)
			self.update_log("Displaying holes for {}".format(fig_name))
		except IOError:
			self.update_log("Unable to display holes for {}".format(fig_name))

		try:
			loaded_metrics = pd.read_pickle('{}_global_metric.pkl'.format(data_dir + fig_name)).iloc[0]
			for i, metric in enumerate(self.metric_tab.metric_dict.keys()):
				value = round(loaded_metrics[metric], 2)
				self.metric_tab.metric_dict[metric]["metric"].set(value)
			self.update_log("Displaying metrics for {}".format(fig_name))

		except IOError:
			self.update_log("Unable to display metrics for {}".format(fig_name))
			for i, metric in enumerate(self.metric_tab.titles):
				self.metric_tab.metric_dict[metric]["metric"].set(0)

		self.parent.master.update_idletasks()



N_PROC = 1#os.cpu_count() - 1
N_THREAD = 8

root = Tk()
GUI = pyfibre_gui(root, N_PROC, N_THREAD)

root.mainloop()
