import cv2,os,re, datetime
import numpy as np
import matplotlib.pyplot as plt


VEG =1
CIVE=2


def _is_contour_bad(c):
    pic_h, pic_w = [720,960]
    min_h = int(pic_h*0.05)
    min_w = int(pic_w*0.05)
    # whether it's too small
    x, y, w, h = cv2.boundingRect(c)
    offset_x = x+w/2
    offset_y = y+h/2
    if ((pic_w / 3 > offset_x>(2 * pic_w) / 3)) and ((pic_h/3> offset_y>2*pic_h/3)):
        print (" is not in middle area, offset X  %d Y %d"%(x+w/2,y+h/2))
        return True
    if (w<min_w and h<min_h):
        print ("too small, w %3d h %3d at X %3d Y %3d"%(w,h,x,y))
        return True

    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
    if len(approx)==4 :
        print("is rectangle, approx %d w %d h %d"%(len(approx), w, h))
        if (len(c)<8):
            return True
        else:
            return False
    if abs(peri - 3.14159*(w+h))/peri >0.7:
        print("likely a noise, w %d h %d peri %d" % (w , h, peri))
        return True
    if abs(peri - 3.14159*(w+h))/peri <0.04:
        print (" likely a circle, diameter %d pixels"%((w+h)/2))
        return False
    # or a rectangle (the channel in the image)
    #print ("------------ Not bad w %d h %d"%( w, h))
    return False


def findEdge(img, method=CIVE, debug = False ):
    """Transfer a given image to excessive greenness and excessive red"""
    # convert to floating point representation [0, 1]
    mean = np.mean(img)
    print ("mean %d"%mean)
    img = img/ 255.0
    # split image into its r, g, and b channels
    r = img[:,:,0]
    g = img[:,:,1]
    b = img[:,:,2]

    if (method == VEG):
        # compute excessive green image ex_g
        ex_g = 2.0 * g - r - b
        # compute excessive red image
        ex_r = 1.4 * r - g
        # normalizeRange(ex_r, -2.4, 2)
        # compute vegetative image (excessive green - excessive red) veg
        result = ex_g - ex_r
        #result = 3*g - 2.4*r - b
        # noramlsie the image
        vmin = np.min(result)
        vmax = np.max(result)
        #normalizeRange(result, -2.4, 2.0)  # -2.4 is the minimum veg value (1, 0, 0) and 2.0 is maximum veg value (0, 1, 0)
        result = (result - vmin) / (vmax - vmin)
        result = result * 255
        result = result.astype(np.uint8)
        ret,ret3 = cv2.threshold(result,130,255,cv2.THRESH_TRUNC+cv2.THRESH_OTSU)

    else:
        #CIVE algorithm
        result = 0.441*r - 0.761*g + 0.385*b + 18.787
        vmin = np.min(result)
        vmax = np.max(result)
        print ("min %d max %d"%(vmin,vmax))
        #normalizeRange(result, -2.0, 2.0)  # -2.4 is the minimum veg value (1, 0, 0) and 2.0 is maximum veg value (0, 1, 0)
        result = (result - vmin) / (vmax - vmin)
        result = result * 255
        result = result.astype(np.uint8)
        _,ret3 = cv2.threshold(result,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

    kernel = np.ones((7, 7), np.uint8)
    ret4 = cv2.morphologyEx(ret3, cv2.MORPH_OPEN, kernel)


    ( cnts, _) = cv2.findContours(ret3, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=lambda k: cv2.contourArea(k), reverse=True)
    if (debug == True):
        images = [img,ret3] #[green, th3, th4,cive]
        plt.figure()
        for i in range(len(images)):
            plt.subplot(2,2,2*i+1)
            plt.imshow(images[i], 'gray')
            plt.subplot(2,2,2*i+2)
            plt.hist(images[i].ravel(), 256, [0, 256])
        plt.show()
    return ret3, cnts

def process_img(path, filename, debug=False):
    file = os.path.join(path,filename)
    if os.path.exists(file) == False:
        print ("file name",file)
        raise RuntimeError("The file is not exist!" )
    image = cv2.imread(file)
    # scale the image size to 960 *720 but remain the same width/height ratio
    h, w, ch = image.shape
    scale = min(320 / h, 320 / w)
    image = cv2.resize(image, (0, 0), fx=scale, fy=scale)

    #segment the green colors from the image. The sensitivity determinate the hue lightness range to be abstracted
    sensitivity = 26
    #image = adjustImage(image)
    img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    #print ("hsv mean %d max %d"%(np.mean(img_hsv),np.max(img_hsv)))
    # the second parameter determinates how the leaf area identified from low brightness.
    lower_green = np.array([60 - sensitivity, 16, 20])
    upper_green = np.array([60 + sensitivity, 255, 255]) # upper  bound
    mask = cv2.inRange(img_hsv, lower_green, upper_green)
    # remove the noise in the close area, but first apply open mask to isolate the background white color
    kernel = np.ones((7, 7), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    res1 = cv2.bitwise_and(image, image, mask=mask)

    edges, cnts = findEdge(res1,debug)
    cv2.imshow("2",edges)


    print ("count of contours %d"%len(cnts))
    #find the proper contour
    # loop over the contours to find out the suitable target
    i = 0
    found_contour = None
    for c in cnts:
        # if the contour is bad, draw it on the mask
        i = i + 1
        if i > 5: break
        if _is_contour_bad(c) == False:
            found_contour = c
            break

    if found_contour is None:
        #found_contour = cnts[0]
        raise RuntimeError("Can't find out proper contour from the photo!")
        # return -1,None,None,None

    #crop_img = cv2.bitwise_and(image, image, mask=found_contour)

    rows, cols, channels = image.shape
    for i in range(rows):
        for j in range(cols):
            image[i, j] = (255, 255, 255)

    crop_img = cv2.drawContours(image, [found_contour], 0, (50, 205, 50), -1)
    cv2.imshow("2", crop_img)
    cv2.waitKey()
    cv2.destroyAllWindows()
    #crop_img[np.where(edges == 0)] = 0
    crop_file = file.replace(".png", "-2.png")
    cv2.imwrite(crop_file, crop_img, [int( cv2.IMWRITE_JPEG_QUALITY), 95])

    return

process_img("C:\\Users\\Rick\\Pictures","aiviva-1.png",True)