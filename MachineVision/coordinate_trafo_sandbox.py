import numpy as np

class CoordinateTransformator():
    def __init__(self, theta_rad, x, y):
        # Define the rotation matrix
        R = np.array([
            [np.cos(theta_rad), -np.sin(theta_rad)],
            [np.sin(theta_rad), np.cos(theta_rad)]
        ])

        # Define the translation vector
        t = np.array([x, y])

        # Combine into the homogeneous transformation matrix
        self.T = np.eye(3)
        self.T[:2, :2] = R
        self.T[:2, 2] = t
        print(f"CoordinateTransformator - the tranformation vector is=\n{self.T}\n")

    def transform_point(self, x, y):
        # Define the point in homogeneous coordinates
        point = np.array([x, y, 1])

        # Transform the point
        transformed_point = self.T @ point

        return transformed_point[:2]
    
def transform_point_A_to_B(point_A, B_origin_in_A, theta):
    """
    Transforms a point from coordinate system A to B, where B has its origin and rotation
    relative to A.
    
    Args:
    - point_A: A tuple (P_A^x, P_A^y) representing the point in system A.
    - B_origin_in_A: A tuple (B0_x, B0_y) representing the origin of B in system A.
    - theta: Rotation angle from A to B in degrees (counterclockwise).
    
    Returns:
    - point_B: A tuple (P_B^x, P_B^y) representing the coordinates in system B.
    """
    # Convert theta from degrees to radians
    theta_rad = np.radians(theta)
    
    # Translate point A by subtracting the origin of B in A
    translated_point = (point_A[0] - B_origin_in_A[0], point_A[1] - B_origin_in_A[1])
    
    # Create the inverse rotation matrix (rotate by -theta)
    cos_theta = np.cos(-theta_rad)
    sin_theta = np.sin(-theta_rad)
    rotation_matrix = np.array([
        [cos_theta, -sin_theta],
        [sin_theta, cos_theta]
    ])
    
    # Convert the translated point to a column vector
    translated_point_vector = np.array(translated_point).reshape(2, 1)
    
    # Apply the rotation matrix
    point_B_vector = np.dot(rotation_matrix, translated_point_vector)
    
    # Flatten the resulting vector and return as a tuple
    return tuple(point_B_vector.flatten())

# Example usage:
point_A = (1, 1)             # Coordinates in system A
theta = -90                    # Rotation angle in degrees
translation = (0, 0)         # Translation from system A to B

#point_B = CoordinateTransformator(np.radians(theta), translation[0], translation[1]).transform_point(point_A[0], point_A[1])
point_B = transform_point_A_to_B(point_A, translation, theta)
print("Coordinates in system B:", point_B)

