import cv2

src = cv2.imread('yes.png', cv2.IMREAD_UNCHANGED)
cv2.imshow('test', src)
cv2.imwrite('yes2.png', src)
cv2.waitKey(0)