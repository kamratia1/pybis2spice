import numpy as np

arr = np.asarray([None, None, None])

print(arr)
if (arr[0] is None) and (arr[1] is None) and (arr[2] is None):
    arr = None


print(arr)
