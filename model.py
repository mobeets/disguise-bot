import dlib # https://elements.heroku.com/buildpacks/j-a-m-e-5/heroku14-buildpack-python-opencv-dlib
import numpy as np
from skimage import io

FACIAL_LANDMARKS = {
	"mouth": (48, 68),
	"right_eyebrow": (17, 22),
	"left_eyebrow": (22, 27),
	"right_eye": (36, 42),
	"left_eye": (42, 48),
	"nose": (27, 35),
	"jaw": (0, 17)
}

def draw_moustaches(image, centers):
	return image

def shape_to_np(shape, dtype="int"):
	coords = np.zeros((68, 2), dtype=dtype)
	for i in range(0, 68):
		coords[i] = (shape.part(i).x, shape.part(i).y)
	return coords

def find_nose_mouth_center(shape):
	(j, k) = FACIAL_LANDMARKS["nose"]
	nose = shape[j:k]
	(j, k) = FACIAL_LANDMARKS["mouth"]
	mouth = shape[j:k]
	return np.median(np.median(nose), np.median(mouth))

def choose_moustache_locations(shapes):
	centers = []
	for shape in shapes:
		centers.append(find_nose_mouth_center(shape))
	return centers

def detect_faces(image):
	detector = dlib.get_frontal_face_detector()
	predictor = dlib.shape_predictor(args["shape_predictor"])

	# detect faces in the image
	shapes = []
	rects = detector(image, 1)
	for (i, rect) in enumerate(rects):
		# determine facial landmarks for the face region
		# then convert facial landmark (x, y)-coordinates to np array
		shape = predictor(image, rect)
		shape = shape_to_np(shape) # [68 x 2]
		shapes.append(shape)
	return shapes

def preprocess(image, width=500):
	# image = cv2.imread(image)
	# image = imutils.resize(image, width=width)
	# image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	image = io.imread(image)
	return image

def update_image(infile):
	image = preprocess(infile)
	shapes = detect_faces(image)
	centers = choose_moustache_locations(shapes)
	image = draw_moustaches(image, centers)
	return image

if __name__ == '__main__':
	update_image()
