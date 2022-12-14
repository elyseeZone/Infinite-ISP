import numpy as np

class AutoWhiteBalance:

    def __init__(self, img, sensor_info, parm_wbc, parm_awb):
        
        self.img = np.float32(img)
        self.enable = parm_wbc['isEnable']
        self.auto = parm_wbc['isAuto']
        self.sensor_info = sensor_info
        self.parm_awb = parm_awb
        self.algorithm = parm_awb['algorithm']
        self.is_debug = parm_awb['isDebug']
        

    def apply_gray_world(self):
        'Gray World White Balance'
        # Gray world algorithm calculates white balance (G/R and G/B)
        # by average values of RGB channels

        return np.mean(self.img, axis=(0,1))

    def apply_norm_2_gray_world(self):
        'Norm 2 Gray World White Balance'
        #Gray world algorithm calculates white balance (G/R and G/B)
        # by average values of RGB channels. Average values for each channel 
        # are calculated by norm-2

        return np.linalg.norm(self.img, axis=(0,1))

    def apply_pca_illuminant_estimation(self, pixel_percentage):
        'PCA Illuminant Estimation'

        # This algorithm gets illuminant estimation directly from the color distribution 
        # The method that chooses bright and dark pixels using a projection distance in the color
        # distribution and then applies principal component analysis to estimate the illumination direction

        
        # Img flattened to Nx3 numpy array where N = heightxwidth to get only the color dist
        flat_img = self.img.flatten().reshape(-1,3)
        size = len(flat_img)

        # mean_vector is the direction vector for mean RGB obtained by dividing mean RBG vector by its magnitude.
        mean_rgb = np.mean(flat_img, axis=0)
        mean_vector = mean_rgb / np.linalg.norm(mean_rgb)

        # To obtain dark and light pixels first distance projected of data on mean direction vector is calculated
        data_p = np.sum(flat_img*mean_vector, axis=1)

        # Projected distance array is sorted in the ascending order to obtain light and dark pixels 
        sorted_data = np.argsort(data_p)

        # Number of dark and light pixels are  calculated from pixel_percentage parameter
        index = int(np.ceil(size*(pixel_percentage/100)))

        # Index of selective pixels (dark and light) is obtained
        filtered_index = np.concatenate((sorted_data[0:index], sorted_data[-index: None]))

        # Selective pixels are retreived on the basis of index from 'data' array
        filtered_data = flat_img[filtered_index,:].astype(np.float32)

        # For first PCA a dot product of selected pixels data matrix with itself is calculated and 3x3 matrix is obtained
        sigma = np.dot(filtered_data.transpose(), filtered_data)

        # Eigenvalues and vectors of the 3x3 matrix (sigma) are calculated
        eig_value, eig_vector = np.linalg.eig(sigma)

        # Eigenvector with maximum eigen value is the direction of iluminated estimation
        eig_vector = eig_vector[:, np.argsort(eig_value)]
        return np.abs(eig_vector[:,2])
        

    def apply_white_balance_gain(self):
        
        # estimated illuminant RBG is obtained from selected algorithm
        if self.algorithm == 'norm_2':
            rgb = self.apply_norm_2_gray_world()
        elif self.algorithm == 'pca':
            pixel_percentage = self.parm_awb['percentage']
            rgb = self.apply_pca_illuminant_estimation(pixel_percentage)
        else:
            rgb = self.apply_gray_world()

        # white balance gains G/R and G/B are calculated from RGB returned from AWB Algorithm
        rgain = rgb[1]/rgb[0]
        bgain = rgb[1]/rgb[2]

        self.img[:, :, 0] *= rgain
        self.img[:, :, 2] *= bgain

        if self.is_debug:
            print('   - AWB - RGain = ', rgain)
            print('   - AWB - Bgain = ', bgain)

        return np.uint8(np.clip(self.img, 0, 255))


    def execute(self):
        print('Auto White balancing = ' + str(self.enable))

        # This module is enabled only when white balance 'enable' and 'auto' parameter both are true.
        if self.enable and self.auto:
            return self.apply_white_balance_gain()
        
        return self.img
