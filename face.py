import glob
import tempfile
import numpy as np
from skimage import io
from skimage.transform import rescale, rotate
import matplotlib.pyplot as plt
import kairos_face # https://github.com/ffmmjj/kairos-face-sdk-python
kairos_face.settings.app_id = "04803c1e"
kairos_face.settings.app_key = "e1177afcd324c68c8adb14034aca836a"
# https://www.kairos.com/docs/api/v1/
# https://www.kairos.com/docs/api/#post-enroll

class Sketch:
    def __init__(self, face=None, sketch=None):
        self.sketch = sketch
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
        sketch = rescale(sketch, 2*self.scale)
        if len(sketch.shape) > 2:
            sketch = rotate(sketch, -90-self.rot)
            return sketch
        pts = np.vstack(np.where(sketch <= 0.01)).T
        if self.doCenter:
            med = np.min(pts, axis=0) + 0.5*(np.max(pts, axis=0) - np.min(pts, axis=0))
        else:
            med = np.max(pts, axis=0)
            med[0] = np.min(pts[:,0], axis=0) + 0.5*(np.max(pts[:,0], axis=0) - np.min(pts[:,0], axis=0))
        pts = (pts - med)
        pts = self.rotate(pts)
        return [pts + c for c in self.centers]

    def draw(self):
        if len(self.sketch.shape) > 2:
            for cent in self.centers:
                im = plt.imshow(self.pts)
        else:
            for pts in self.pts:
                plt.scatter(pts[:,0], pts[:,1], c='k', s=1)

class Moustache(Sketch):
    def locate(self, face):
        # median of eye center and chin tip
        leye = (face['leftEyeCenterX'], face['leftEyeCenterY'])
        reye = (face['rightEyeCenterX'], face['rightEyeCenterY'])
        eyecent = np.median(np.array([leye, reye]), axis=0)
        chin = (face['chinTipX'], face['chinTipY'])
        self.centers = [np.median(np.array([eyecent.tolist(), chin]), axis=0)]
        self.rot = face['roll']
        self.scale = face['eyeDistance']/100.
        self.linewidth = 1

class Nose(Sketch):
    def locate(self, face):
        # median of eye center and chin tip
        leye = (face['leftEyeCenterX'], face['leftEyeCenterY'])
        reye = (face['rightEyeCenterX'], face['rightEyeCenterY'])
        eyecent = np.median(np.array([leye, reye]), axis=0)
        chin = (face['chinTipX'], face['chinTipY'])
        self.centers = [np.median(np.array([eyecent.tolist(), chin]), axis=0)]
        # self.centers = [eyecent]
        self.rot = face['roll']
        self.scale = face['eyeDistance']/100.
        self.linewidth = 1
        self.doCenter = False

class Glasses(Sketch):
    def locate(self, face):
        leye = (face['leftEyeCenterX'], face['leftEyeCenterY'])
        self.centers = [np.median(np.array([leye, reye]), axis=0)]
        self.rot = face['roll']
        self.scale = 0.5
        self.linewidth = 1

class Bird(Sketch):
    def locate(self, face):
        self.centers = [(face['topLeftX'], face['topLeftY'])]
        self.rot = face['roll']
        self.scale = face['eyeDistance']/120.
        self.linewidth = 1

class Hat(Sketch):
    def locate(self, face):
        ltop = (face['topLeftX'], face['topLeftY'])
        self.centers = [(face['topLeftX'] + face['width']/2, face['topLeftY'] - face['height']/5)]
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
    if type(faces) is dict and 'images' in faces:
        faces = faces['images']
    if len(faces) > 0:
        return faces[0]['faces']

def load_sketch(globfile):
    fls = glob.glob(globfile)
    infile = fls[np.random.randint(0, len(fls))]
    img = io.imread(infile)
    img = rescale(img, 0.8)
    img = rotate(img, 90)
    img = img.round()
    if len(img.shape) == 3:
        img = (1-img[:,:,-1].round())
    return img

def draw_on_face(infile, faces, data, outfile=None):
    image = io.imread(infile)
    fig = plt.imshow(image, cmap=plt.cm.gray)
    for face in faces:
        print '.'
        for globfile, cls in data:
            sketch = load_sketch(globfile)
            cls(face=face, sketch=sketch).draw()
    plt.axis('off')
    fig.axes.get_xaxis().set_visible(False)
    fig.axes.get_yaxis().set_visible(False)
    plt.tight_layout()
    if outfile is None:
        plt.show()
    else:
        plt.savefig(outfile, bbox_inches='tight', pad_inches=0)

def update_image(infile, url):
    faces = detect_faces(url)
    if faces is None:
        return None
    data = [('data/moustaches/*.png', Moustache), ('data/hats/*.png', Hat), ('data/eyes/*.png', Eyes)]
    f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    outfile = f.name
    draw_on_face(infile, faces, data, outfile)
    return outfile

def test():
    data = [('data/moustaches/*.png', Moustache), ('data/hats/*.png', Hat), ('data/eyes/*.png', Eyes)]
    # data = [('data/eyes/4.png', Eyes)]
    # data = [('data/moustache.npz', Moustache), ('data/hat.npz', Hat), 
        # ('data/eye.npz', Eyes)]
    url = 'http://pbs.twimg.com/media/DAMpysCUMAE3SlL.jpg'
    url = 'https://scontent.fphl2-1.fna.fbcdn.net/v/t1.0-9/553988_3811036804045_1886663415_n.jpg?oh=c117d5b58989aec57e95cb797f7e2f2d&oe=59A39B93'
    url = 'https://scontent.fphl2-1.fna.fbcdn.net/v/t1.0-9/207146_1003361253911_9728_n.jpg?oh=77696385c0ed2002eb50f1c32bfd67f2&oe=59AB05A4'
    # faces = detect_faces(url)

    import cPickle
    # cPickle.dump(faces, open('data/tmp3.pickle', 'w'))
    infile = 'data/example.jpg'
    faces = cPickle.load(open('data/tmp.pickle'))  
    draw_on_face(infile, faces, data)#, outfile='data/tmp.png')
    
if __name__ == '__main__':
    infile = 'data/example.jpg'
    url = 'http://pbs.twimg.com/media/DAMpysCUMAE3SlL.jpg'
    outfile = update_image(infile, url)
    img = io.imread(outfile)
    plt.imshow(img)
    plt.show()
