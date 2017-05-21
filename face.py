import os
import glob
import tempfile
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from skimage import io
from skimage.transform import rescale, rotate
import kairos_face # https://github.com/ffmmjj/kairos-face-sdk-python

# https://www.kairos.com/docs/api/v1/
# https://www.kairos.com/docs/api/#post-enroll
kairos_face.settings.app_id = os.environ['KAIROS_APP_ID']
kairos_face.settings.app_key = os.environ['KAIROS_APP_KEY']

class Sketch:
    def __init__(self, face=None, sketch=None):
        self.sketch = sketch
        self.doCenter = True
        self.locate(face)
        self.sketch = self.process(self.sketch)

    def locate(self, face):
        self.scale = 1.0
        self.rot = 0.0
        self.center = [[0.0, 0.0]]
        self.linewidth = 1

    def rotate(self, sketch):
        theta = -self.rot*np.pi/180
        R = [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]]
        return np.dot(sketch, np.array(R))

    def process(self, sketch):
        sketch = rescale(sketch, 1.5*self.scale)
        sketch = rotate(sketch, -90-self.rot)
        return sketch

    def draw(self):
        for cent in self.centers:
            im = OffsetImage(self.sketch, zoom=1)
            ab = AnnotationBbox(im, (cent[0], cent[1]),
                    xycoords='data', frameon=False)
            plt.gca().add_artist(ab)

class Moustache(Sketch):
    def locate(self, face):
        # median of eye center and chin tip
        leye = (face['leftEyeCenterX'], face['leftEyeCenterY'])
        reye = (face['rightEyeCenterX'], face['rightEyeCenterY'])
        eyecent = np.median(np.array([leye, reye]), axis=0)
        chin = (face['chinTipX'], face['chinTipY'])
        self.centers = [np.median(np.array([eyecent.tolist(), chin]), axis=0)]
        self.rot = face['roll']
        self.scale = face['eyeDistance']/150.
        self.linewidth = 1

class Hat(Sketch):
    def locate(self, face):
        ltop = (face['topLeftX'], face['topLeftY'])
        self.centers = [(face['topLeftX'] + face['width']/2, face['topLeftY'] - face['height']/2)]
        self.rot = face['roll']
        self.scale = face['eyeDistance']/70.
        self.linewidth = 1
        self.doCenter = False

class Eyes(Sketch):
    def locate(self, face):
        self.centers = [(face['leftEyeCenterX'], face['leftEyeCenterY']), (face['rightEyeCenterX'], face['rightEyeCenterY'])]
        self.rot = face['roll']
        self.scale = face['eyeDistance']/250.
        self.linewidth = 1

def detect_faces(url):
    try:
        faces = kairos_face.detect_face(url=url)
    except Exception, e:
        print str(e)
        return None
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
    if len(img.shape) == 2:
        img = np.tile(img[:,:,None], 4)
        img[:,:,-1] = 0
        img[img[:,:,0] <= 0.1,-1] = 1
    return img

def draw_on_face(infile, faces, data, outfile=None):
    image = io.imread(infile)
    plt.close('all')
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

def get_data():
    return [('data/moustaches/*.png', Moustache), ('data/hats/*.png', Hat), ('data/eyes/*.png', Eyes)]
    
def update_image(infile, url):
    faces = detect_faces(url)
    if faces is None:
        return None
    f = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    outfile = f.name
    draw_on_face(infile, faces, get_data(), outfile)
    return outfile

def test0():
    import cPickle
    import urllib
    url = 'http://pbs.twimg.com/media/DAMpysCUMAE3SlL.jpg'
    # url = 'https://scontent.fphl2-1.fna.fbcdn.net/v/t1.0-9/553988_3811036804045_1886663415_n.jpg?oh=c117d5b58989aec57e95cb797f7e2f2d&oe=59A39B93'
    # url = 'https://scontent.fphl2-1.fna.fbcdn.net/v/t1.0-9/207146_1003361253911_9728_n.jpg?oh=77696385c0ed2002eb50f1c32bfd67f2&oe=59AB05A4'

    # faces = detect_faces(url)
    # cPickle.dump(faces, open('data/tmp.pickle', 'w'))
    faces = cPickle.load(open('data/tmp.pickle'))  
    
    infile, _ = urllib.urlretrieve(url)
    draw_on_face(infile, faces, get_data())#, outfile='data/tmp.png')
    
def test1():
    import urllib
    # url = 'http://pbs.twimg.com/media/DAMpysCUMAE3SlL.jpg'
    url = 'https://scontent.fphl2-1.fna.fbcdn.net/v/t1.0-9/553988_3811036804045_1886663415_n.jpg?oh=c117d5b58989aec57e95cb797f7e2f2d&oe=59A39B93'
    url = 'https://pbs.twimg.com/media/DAUQ5CXVoAAgtH_.jpg:large'
    url = 'https://pbs.twimg.com/media/DAUXgDHUwAU-S3U.jpg'
    infile, _ = urllib.urlretrieve(url)
    outfile = update_image(infile, url)
    img = io.imread(outfile)
    plt.imshow(img)
    plt.show()

if __name__ == '__main__':
    test1()
