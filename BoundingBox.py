from utils import *
from MeshPly import MeshPly
import numpy as np
from matrixUtils import *

class BoundingBox:


	def __init__(self, mesh_name):
		self.i_c = get_camera_intrinsic()
		# Read object model information, get 3D bounding box corners
		self.mesh          = MeshPly(mesh_name)
		self.vertices      = np.c_[np.array(self.mesh.vertices), np.ones((len(self.mesh.vertices), 1))].transpose()
		self.corners3D     = get_3D_corners(self.vertices)
		idx = np.random.randint(self.vertices.shape[1], size=2000)
		self.reduced_vertices = self.vertices.T[idx,:].T
		# diam          = calc_pts_diameter(np.array(mesh.vertices))
		self.diam          = float(0.6536639)
		self.w = 640
		self.h = 480
		self.marked_points = []
		self.created_i = 0

	def add_clicked_point(self, point):
		self.marked_points.append(point)
		if (len(self.marked_points) == 4):
			self.marked_points = np.asarray(self.marked_points, dtype=float).T
			self.marked_points[0] = self.marked_points[0]
			self.marked_points[1] = self.marked_points[1]
			#all_points = np.array(np.transpose(self.corners3D[:3, :]), dtype='float32')
			# far right, far left, near right, near left
			#all_points = np.array([[0.072234, 0.205713, -0.097741], [-0.074296, 0.206448, -0.097032], [0.074358, 0.116048, -0.100746],[-0.075816, 0.116361, -0.105058]])
			# near right, far right, near left, far left
			all_points = np.array([[0.140487,0.085116,-0.094686],[0.155971,0.246529,-0.094677],[-0.140479,0.085057,-0.094924],[-0.156152,0.246414,-0.094853]])
			print(all_points)
			print(self.marked_points.T)
			R, t = pnp(all_points, self.marked_points.T, np.array(self.i_c, dtype='float32'))
			Rt = np.append(R, t, axis=1)
			proj_2d_p = compute_projection(self.corners3D, Rt, self.i_c)
			self.marked_points = []
			return rotationMatrixToEulerAngles(R), t
		return None
		
	def extractRange(self, xArr):	
		return np.max(xArr) - np.min(xArr)
	
	def draw_on_img(self, image, R, t, save=False):
		image_tmp = image.copy()
		Rt = np.append(R, t, axis=1)
		proj_2d_p = compute_projection(self.corners3D, Rt, self.i_c)
		
		proj_2d_p = proj_2d_p.astype(int)

		for c in self.marked_points:
			cv2.circle(image_tmp,(c[0], c[1]), 3, (0,255,0), -1)

		cv2.circle(image_tmp,(proj_2d_p[0,0], proj_2d_p[1,0]), 4, (255,0,0), -1)
		cv2.circle(image_tmp,(proj_2d_p[0,2], proj_2d_p[1,2]), 4, (255,0,0), -1)
		cv2.circle(image_tmp,(proj_2d_p[0,3], proj_2d_p[1,3]), 4, (255,0,0), -1)
		cv2.circle(image_tmp,(proj_2d_p[0,1], proj_2d_p[1,1]), 4, (255,0,0), -1)


		proj_2d_vert = compute_projection(self.reduced_vertices, Rt, self.i_c).astype(int).T
		for c in proj_2d_vert:
			if (c[0] < self.w and c[0] >= 0 and c[1] < self.h and c[1] >= 0):
				image_tmp[c[1], c[0]]=(0,255,0)

		# Draw lower base of 3d bb
		pts = np.array([[proj_2d_p[0,0], proj_2d_p[1,0]],[proj_2d_p[0,2], proj_2d_p[1,2]],[proj_2d_p[0,3], proj_2d_p[1,3]],[proj_2d_p[0,1], proj_2d_p[1,1]]], np.int32)
		cv2.polylines(image_tmp,[pts],True,(255,0,0))
		
		# Draw the front of the bounding box
		pts = np.array([[proj_2d_p[0,3], proj_2d_p[1,3]],[proj_2d_p[0,7], proj_2d_p[1,7]],[proj_2d_p[0,6], proj_2d_p[1,6]],[proj_2d_p[0,2], proj_2d_p[1,2]]], np.int32)
		cv2.polylines(image_tmp,[pts],True,(0,0,255))

		# Draw upper base of 3d bb
		pts = np.array([[proj_2d_p[0,4], proj_2d_p[1,4]],[proj_2d_p[0,6], proj_2d_p[1,6]],[proj_2d_p[0,7], proj_2d_p[1,7]],[proj_2d_p[0,5], proj_2d_p[1,5]]], np.int32)
		cv2.polylines(image_tmp,[pts],True,(0,255,255))

		# Draw -y side
		pts = np.array([[proj_2d_p[0,0], proj_2d_p[1,0]],[proj_2d_p[0,2], proj_2d_p[1,2]],[proj_2d_p[0,6], proj_2d_p[1,6]],[proj_2d_p[0,4], proj_2d_p[1,4]]], np.int32)
		cv2.polylines(image_tmp,[pts],True,(0,255,0))

		if (save == True):
			if not os.path.exists('./labels'):
				os.makedirs('./labels')
			self.created_i = len(sorted(os.listdir("./labels")))
			f_s = open(os.path.join('./labels',format(self.created_i, '06') + '.txt'), "w+")
			f_b = open('gt.yml', "a+")
			f_b_c = open('info.yml', "a+")

			proj_2d_p = proj_2d_p.astype(float)
			proj_2d_p[0] = proj_2d_p[0] / self.w
			proj_2d_p[1] = proj_2d_p[1] / self.h

			c_x = np.mean(proj_2d_p[0], axis=0)
			c_y = np.mean(proj_2d_p[1], axis=0)

			range_x = self.extractRange(proj_2d_p[0])
			range_y = self.extractRange(proj_2d_p[1])
			f_s.write("0 %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f %.6f" % (c_x, c_y, proj_2d_p[0][0], proj_2d_p[1][0], proj_2d_p[0][1], proj_2d_p[1][1], proj_2d_p[0][2], proj_2d_p[1][2], proj_2d_p[0][3], proj_2d_p[1][3], proj_2d_p[0][4], proj_2d_p[1][4], proj_2d_p[0][5], proj_2d_p[1][5], proj_2d_p[0][6], proj_2d_p[1][6], proj_2d_p[0][7], proj_2d_p[1][7], range_x, range_y))
			f_s.close()

			top = c_x - (range_x/2)
			left = c_y - (range_y/2)

			f_b.write(str(self.created_i) + ':\n')
			f_b.write('- cam_R_m2c: ' + np.array2string(R.flatten(), precision=8, separator=',', suppress_small=True) + '\n')
			f_b.write('  cam_t_m2c: ' + np.array2string(t.flatten() * 1000, precision=8, separator=',', suppress_small=True) + '\n')
			f_b.write('  obj_bb: ' + np.array2string(np.array([top*self.w,left*self.h,range_x*self.w,range_y*self.h], dtype=int), separator=',') + '\n')
			f_b.write('  obj_id: 1\n')
			f_b.close()

			f_b_c.write(str(self.created_i) + ':\n')
			f_b_c.write('  cam_K: ' + np.array2string(self.i_c.flatten().astype(int), precision=8, separator=',', suppress_small=True) + '\n')
			f_b_c.write('  depth_scale: 1.0\n')
			f_b_c.close()

			self.created_i += 1
		return image_tmp