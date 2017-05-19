import numpy as np
import kairos_face # https://github.com/ffmmjj/kairos-face-sdk-python
kairos_face.settings.app_id = "04803c1e"
kairos_face.settings.app_key = "e1177afcd324c68c8adb14034aca836a"
# https://www.kairos.com/docs/api/v1/
# https://www.kairos.com/docs/api/#post-enroll

class Sketch:
	def __init__(self, face=None, data=None, sketch=None):
		self.sketch = sketch
		if self.sketch is None and data is not None:
			ind = np.random.randint(0, len(data['test']))
			self.sketch = data['test'][ind]
		self.locate(face)
		self.pts = self.get_pts(self.sketch)

	def locate(self, face):
		self.scale = 1.0
		self.rot = 0.0
		self.center = [[0.0, 0.0]]
		self.linewidth = 1

	def rotate(self, sketch):
		theta = self.rot*np.pi/180
		R = [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
		return np.dot(sketch, np.array(R))

	def get_pts(self, sketch):
		ix = sketch[:,2] != 1
		pts = sketch[ix,:2].cumsum(axis=0)
		med = np.median(pts, axis=0)
		pts = self.scale*(pts - med)
		pts = self.rotate(pts)
		return self.center + pts

class Moustache(Sketch):
	def locate(self, face):
		# median of eye center and chin tip
		leye = (face['leftEyeCenterX'], face['leftEyeCenterY'])
		reye = (face['rightEyeCenterX'], face['rightEyeCenterY'])
		eyecent = np.median(np.array([leye, reye]), axis=0)
		chin = (face['chinTipX'], face['chinTipY'])
		self.center = np.median(np.array([eyecent.tolist(), chin]), axis=0)
		self.rot = face['roll']
		self.scale = 0.25
		self.linewidth = 4

class Glasses(Sketch):
	def locate(self, face):
		leye = (face['leftEyeCenterX'], face['leftEyeCenterY'])
		reye = (face['rightEyeCenterX'], face['rightEyeCenterY'])
		self.center = np.median(np.array([leye, reye]), axis=0)
		self.rot = face['roll']
		self.scale = 0.5
		self.linewidth = 1

def detect_faces(url):
	faces = kairos_face.detect_face(url=url)
	return faces['images'][0]['faces']

def load_data(datafiles):
	d = {}
	for name, infile in datafiles.iteritems():
		d[name] = np.load(infile)
	return d

from skimage import io
import matplotlib.pyplot as plt
def draw_on_face(infile, faces, data):
	image = io.imread(infile)
	fig, ax = plt.subplots(figsize=(10, 6))
	ax.imshow(image, cmap=plt.cm.gray)

	d = load_data(data)
	xs = []
	for face in faces:
		for name, data in d.iteritems():
			if 'moustache' in name:
				x = Moustache(face=face, data=data)
			elif 'glasses' in name:
				x = Glasses(face=face, data=data)
			else:
				continue
			ax.plot(x.pts[:,0], x.pts[:,1], 'k-', linewidth=x.linewidth)
	ax.set_axis_off()
	plt.tight_layout()
	plt.show()

# from skimage import io
# import matplotlib.pyplot as plt
# def draw_moustache(infile, mpos, gpos, roll, mus_data, gls_data):
# 	# should include "roll" as well as position
# 	image = io.imread(infile)

# 	fig, ax = plt.subplots(figsize=(10, 6))
# 	ax.imshow(image, cmap=plt.cm.gray)
# 	for i, p in enumerate(mpos):
# 		mus = get_drawing(mus_data, rot=roll[i], scale=0.1)
# 		xs = p[0] + mus[:,0]
# 		ys = p[1] + mus[:,1]
# 		ax.plot(xs, ys, 'k-', linewidth=1)
# 	for i, p in enumerate(gpos):		
# 		gls = get_drawing(gls_data, rot=roll[i], scale=0.5)
# 		xs = p[0] + gls[:,0]
# 		ys = p[1] + gls[:,1]
# 		# ax.plot(xs, ys, 'k-', linewidth=2)
# 	ax.set_axis_off()
# 	plt.tight_layout()
# 	plt.show()

def get_temp_data():
	mpos = [[ 295.5,  179.5], [ 182. ,  163.5]]
	gpos = [[ 292.,  136.], [ 196.,  124.]]
	roll = [-5, 19] # positive = clockwise
	infile = 'data/example.jpg'
	
	mpos = [[ 275.25,  255.25]]
	gpos = [[ 273.5,  228.5]]
	roll = [-4]
	infile = 'data/example2.jpg'

if __name__ == '__main__':
	data = {'moustache': 'data/moustache.npz', 'glasses': 'data/eyeglasses.npz'}
	url = 'http://pbs.twimg.com/media/DAMpysCUMAE3SlL.jpg'
	infile = 'data/example.jpg'
	faces = detect_faces(url)

	import cPickle
	cPickle.dump(faces, open('data/tmp.pickle', 'w'))
	
	draw_on_face(infile, faces, data)

	# datafile = 'data/moustache.npz'
	# mus_data = np.load(datafile)
	# datafile = 'data/eyeglasses.npz'
	# gls_data = np.load(datafile)
	# draw_moustache(infile, mpos, gpos, roll, mus_data, gls_data)
	
