import numpy as np

matrix = np.array([
    [1, 2, 3], 
    [4, 5, 6], 
    [7, 8, 9]
])

x_min = np.min(matrix)
x_max = np.max(matrix)
norma = (matrix - x_min) / (x_max - x_min)
print(norma)
