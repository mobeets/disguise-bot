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
			lns = np.array([len(x) for x in data['test']])
			inds = np.arange(0, len(lns))[lns > np.median(lns)]
			ind = inds[np.random.randint(0, len(inds))]
			# ind = np.random.randint(0, len(data['test']))
			self.sketch = data['test'][ind]
		self.doCenter = True
		self.locate(face)
		self.pts = self.get_pts(self.sketch)

	def locate(self, face):
		self.scale = 1.0
		self.rot = 0.0
		self.center = [[0.0, 0.0]]
		self.linewidth = 1

	def rotate(self, sketch):
		theta = -self.rot*np.pi/180
		R = [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
		return np.dot(sketch, np.array(R))

	def get_pts(self, sketch):
		ix = sketch[:,2] != 1
		pts = sketch[ix,:2].cumsum(axis=0)
		# med = np.median(pts, axis=0)
		if self.doCenter:
			med = np.min(pts, axis=0) + 0.5*(np.max(pts, axis=0) - np.min(pts, axis=0))
		else:
			med = np.max(pts, axis=0)
		pts = self.scale*(pts - med)
		pts = self.rotate(pts)
		if hasattr(self, 'centers'):
			return [pts + c for c in self.centers]
		else:
			return [self.center + pts]

class Moustache(Sketch):
	def locate(self, face):
		# median of eye center and chin tip
		leye = (face['leftEyeCenterX'], face['leftEyeCenterY'])
		reye = (face['rightEyeCenterX'], face['rightEyeCenterY'])
		eyecent = np.median(np.array([leye, reye]), axis=0)
		chin = (face['chinTipX'], face['chinTipY'])
		self.center = np.median(np.array([eyecent.tolist(), chin]), axis=0)
		self.rot = face['roll']
		self.scale = face['eyeDistance']/120.
		self.linewidth = 1

class Glasses(Sketch):
	def locate(self, face):
		leye = (face['leftEyeCenterX'], face['leftEyeCenterY'])
		self.center = np.median(np.array([leye, reye]), axis=0)
		self.rot = face['roll']
		self.scale = 0.5
		self.linewidth = 1

class Bird(Sketch):
	def locate(self, face):
		self.center = (face['topLeftX'], face['topLeftY'])
		self.rot = face['roll']
		self.scale = face['eyeDistance']/120.
		self.linewidth = 1

class Hat(Sketch):
	def locate(self, face):
		ltop = (face['topLeftX'], face['topLeftY'])
		# rtop = (face['topRightX'], face['topRightY'])
		self.center = (face['topLeftX'] + face['width'], face['topLeftY'] - face['height']/5)
		# self.center = np.median(np.array([ltop, rtop]), axis=0)
		self.rot = face['roll']
		self.scale = face['eyeDistance']/80.
		self.linewidth = 1
		self.doCenter = False

class Eyes(Sketch):
	def locate(self, face):
		self.centers = [(face['leftEyeCenterX'], face['leftEyeCenterY']), (face['rightEyeCenterX'], face['rightEyeCenterY'])]
		self.rot = face['roll']
		self.scale = face['eyeDistance']/200.
		self.linewidth = 1

def detect_faces(url):
	faces = kairos_face.detect_face(url=url)
	return faces['images'][0]['faces']

def load_data(datafiles):
	d = []
	for infile, cls in datafiles:
		d.append((cls, np.load(infile)))
	return d

from skimage import io
import matplotlib.pyplot as plt
def draw_on_face(infile, faces, data, outfile=None):
	image = io.imread(infile)
	# fig, ax = plt.subplots(figsize=(10, 6))
	fig = plt.imshow(image, cmap=plt.cm.gray)

	d = load_data(data)
	xs = []
	for face in faces:
		for cls, data in d:
			x = cls(face=face, data=data)
			for pts in x.pts:
				plt.plot(pts[:,0], pts[:,1], 'r-', linewidth=x.linewidth)
	plt.axis('off')
	fig.axes.get_xaxis().set_visible(False)
	fig.axes.get_yaxis().set_visible(False)
	plt.tight_layout()
	if outfile is None:
		plt.show()
	else:
		plt.savefig(outfile, bbox_inches='tight', pad_inches=0)

if __name__ == '__main__':
	# data = [('data/moustache.npz', Moustache)]
	data = [('data/moustache.npz', Moustache), ('data/hat.npz', Hat), 
		('data/eye.npz', Eyes)]
	url = 'http://pbs.twimg.com/media/DAMpysCUMAE3SlL.jpg'
	url = 'https://scontent.fphl2-1.fna.fbcdn.net/v/t1.0-9/553988_3811036804045_1886663415_n.jpg?oh=c117d5b58989aec57e95cb797f7e2f2d&oe=59A39B93'
	url = 'https://scontent.fphl2-1.fna.fbcdn.net/v/t1.0-9/207146_1003361253911_9728_n.jpg?oh=77696385c0ed2002eb50f1c32bfd67f2&oe=59AB05A4'
	infile = 'data/example3.jpg'
	# faces = detect_faces(url)

	import cPickle
	# cPickle.dump(faces, open('data/tmp3.pickle', 'w'))
	faces = cPickle.load(open('data/tmp3.pickle'))	
	draw_on_face(infile, faces, data)#, outfile='data/tmp.png')
