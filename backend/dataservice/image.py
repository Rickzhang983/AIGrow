import cv2,os,exifread,re, datetime,logging
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger("Image")

def getTimeInfoFromFile(path, filename):
    FIELD = 'EXIF DateTimeOriginal'
    full_file_name = os.path.join(path, filename)
    with open(full_file_name, 'rb') as fd:
        tags = exifread.process_file(fd)
    if FIELD in tags:
        new_name = str(tags[FIELD]).replace(':', '').replace(' ', '') #+ os.path.splitext(filename)[1]
    else:
        new_name = filename.replace(":","").replace(" ","_").replace("-","")
        new_name = re.sub(r'\D', "", new_name)

    if (len(new_name)==14):
        year = int(new_name[0:4])
        month = int(new_name[4:6])
        day = int(new_name[6:8])
        hour = int(new_name[8:10])
        minute = int(new_name[10:12])
        sec = int(new_name[12:14])
        logger.debug ("The time identified as %s-%s-%s %d:%d:%d"%(year,month,day,hour,minute,sec))
        return True, datetime.datetime(year,month,day,hour,minute,sec).strftime("%Y-%m-%d %H:%M:%S")
    else:
        return False,None


def findRefCard(image,debug=False):
    CARD_PERI = 2.5
    img_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # lower mask (0-10)
    lower_red = np.array([0, 70, 40])
    upper_red = np.array([10, 255, 255])
    mask0 = cv2.inRange(img_hsv, lower_red, upper_red)

    # upper mask (170-180)
    lower_red = np.array([160, 70, 40])
    upper_red = np.array([180, 255, 255])
    mask1 = cv2.inRange(img_hsv, lower_red, upper_red)
    #mask = cv2.bitwise_or(mask1, mask0)
    # join my masks
    mask = mask0 + mask1

    kernel = np.ones((5, 5), np.uint8)
    #remove the noise near the red box area
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    cnts,_ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    if (debug == True):
        images = [image,mask] #[green, th3, th4,cive]
        plt.figure()
        for i in range(2):
            plt.subplot(2, 2, i + 1), plt.imshow(images[i], 'gray')
        plt.show()

    cnts = sorted(cnts, key=lambda k: cv2.contourArea(k), reverse=True)
    i = 0
    #find the rectangle box
    for c in cnts:
        i += 1
        # only first 5 contours are assessed
        if i> 5: break
        x, y, w, h = cv2.boundingRect(c)
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.06 * peri, True)
        # due to the quality of the picture, the w and h might not be equal, there shall be a tolarence saying 15%
        if len(approx) == 4 and (w > 20 or h > 20) and (abs(w-h)/max(w,h)<0.16):
            # we can't take the area of the contour directly, because the box might not be completed
            rect = cv2.minAreaRect(c)
            box = cv2.boxPoints(rect)
            box = np.int0(box)
            x, y, w, h = cv2.boundingRect(c)
            l = max (w,h)
            # the following 3 lines were deprecated on 16 Nov 2018.
            #area = cv2.contourArea(box)
            #peri = cv2.arcLength(box, True)
            #return area/(CARD_PERI*CARD_PERI),peri/(CARD_PERI*4),c
            return l*l/(CARD_PERI*CARD_PERI),l/CARD_PERI,mask
        else:
            logger.debug("This is not red card  approx %d w %d h %d" % (len(approx), w, h))
    raise RuntimeError("cant find the red card")



def normalizeRange(mat, min_val, max_val):
    """Normalise a specified numpy matrix"""
    # get the range
    range = max_val - min_val
    # as long as the range is not 0 then scale so that range is 1
    if range > 0:
        # subtract offset so min value is 0
        mat -= min_val
        # normalise so values are in range 0
        mat /= float(range)

# return excessive green representation of a provided image
# @param img: RGB image needs to be converted (np.uint8)
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
        logger.debug (" is not in middle area, offset X  %d Y %d"%(x+w/2,y+h/2))
        return True
    if (w<min_w and h<min_h):
        logger.debug ("too small, w %3d h %3d at X %3d Y %3d"%(w,h,x,y))
        return True

    peri = cv2.arcLength(c, True)
    approx = cv2.approxPolyDP(c, 0.04 * peri, True)
    if len(approx)==4 :
        logger.debug("is rectangle, approx %d w %d h %d"%(len(approx), w, h))
        if (len(c)<8):
            return True
        else:
            return False
    if abs(peri - 3.14159*(w+h))/peri >0.7:
        logger.debug("likely a noise, w %d h %d peri %d" % (w , h, peri))
        return True
    if abs(peri - 3.14159*(w+h))/peri <0.04:
        logger.debug (" likely a circle, diameter %d pixels"%((w+h)/2))
        return False
    # or a rectangle (the channel in the image)
    logger.debug ("------------ Not bad w %d h %d"%( w, h))
    return False


def findEdge(img, method=CIVE, debug = False ):
    """Transfer a given image to excessive greenness and excessive red"""
    # convert to floating point representation [0, 1]
    mean = np.mean(img)
    logger.debug ("mean %d"%mean)
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
        logger.debug ("min %d max %d"%(vmin,vmax))
        #normalizeRange(result, -2.0, 2.0)  # -2.4 is the minimum veg value (1, 0, 0) and 2.0 is maximum veg value (0, 1, 0)
        result = (result - vmin) / (vmax - vmin)
        result = result * 255
        result = result.astype(np.uint8)
        _,ret3 = cv2.threshold(result,0,255,cv2.THRESH_BINARY_INV+cv2.THRESH_OTSU)

    kernel = np.ones((7, 7), np.uint8)
    ret4 = cv2.morphologyEx(ret3, cv2.MORPH_OPEN, kernel)

    #fig, (ax1, ax2,ax3) = plt.subplots(ncols=3, nrows=1)
    #ax1.set_title('VEG', fontsize=12)
    #ax1.imshow(result)
    #plt.subplot(4, 1, 1), plt.imshow(result, cmap='gray')
    #plt.title('VEG')
    #plt.subplot(4, 1, 2), plt.hist(result.ravel(), 150)
    #plt.subplot(4, 1, 3), plt.imshow(ret3, cmap='gray'),    plt.title('ret3')
    #plt.subplot(4, 1, 4), plt.hist(ret4.ravel(), 150),   plt.title('ret4')
    #plt.show()

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
            #color = ('b', 'g', 'r')
            #for j, col in enumerate(color):
            #    histr = cv2.calcHist([images[i]], [j], None, [256], [0, 256])
            #    plt.plot(histr, color=col)
            #    plt.xlim([0, 256])
        plt.show()
    return ret3, cnts

def process_img(path, filename, debug=False):
    file = os.path.join(path,filename)
    if os.path.exists(file) == False:
        raise RuntimeError("The file is not exist!" )
    res, t_datetime = getTimeInfoFromFile( path,filename )
    if res == False:
        raise RuntimeError("The file has no time info identified")
    image = cv2.imread(file)
    # scale the image size to 960 *720 but remain the same width/height ratio
    h, w, ch = image.shape
    scale = min(720 / h, 960 / w)
    image = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    cv2.imwrite(file,image)

    # get the scales from the reference red card recognization
    area_ratio, peri_ratio,red_edge = findRefCard(image,debug)
    logger.debug("area ratio %.3f, peri_ratio %.3f" % (area_ratio, peri_ratio))
    #img2 = cv2.GaussianBlur(image, (5, 5), 0)
    image[np.where(red_edge == 255)] = 127

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
    logger.debug ("count of contours %d"%len(cnts))
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

    x, y, w, h = cv2.boundingRect(found_contour)
    max_diameter = max(w, h) / peri_ratio
    #crop_contours = mask2[y:y + h, x:x + w]

    #crop_img = cv2.bitwise_and(image, image, mask=found_contour)
    crop_img = cv2.drawContours(image, [found_contour], 0, (0, 0, 255), 1, cv2.LINE_8) #cv2.FILLED)
    #crop_img[np.where(edges == 0)] = 0
    crop_img = crop_img[y:y + h, x:x + w]
    crop_file = file.replace(".jpg", "-2.jpg")
    cv2.imwrite(crop_file, crop_img, [int( cv2.IMWRITE_JPEG_QUALITY), 60])

    return cv2.contourArea(found_contour)/area_ratio, max_diameter, t_datetime

