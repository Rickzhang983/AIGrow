import datetime
import os,os.path
import sqlite3
import numpy as np
import cv2


def _get_image_area_old(img,debug=False):
    v = np.median(img)
    print ("v1 %d"%v)

    blur = cv2.GaussianBlur(img, (5, 5), 0)
    # Convert BGR to HSV
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    v2 = np.median(hsv)
    if v2 >65: l=70;lb=32;ub=90
    else: l=50;lb=24;ub=65
    print("v2 %d" % v2)
    # define range of blue color in HSV
    lower_green = np.array([lb,40, l]) #32; 40,int(v/3); int(2*v/3)])
    upper_green = np.array([ub, 255, 255])
    # Threshold the HSV image to get only green colors
    mask = cv2.inRange(hsv, lower_green, upper_green)

   # Bitwise-AND mask and original image
    res1 = cv2.bitwise_and(img, img, mask=mask)
    SIGMA = 0.6
    blur = cv2.GaussianBlur(res1, (5, 5), 0)
    lower = int(max(0, (1.0 - SIGMA) * v))
    upper = int(min(255, (1.0 + SIGMA) * v))
    print ("v %d lower %d upper %d"%(v,lower,upper))
    edges = cv2.Canny(blur, lower, upper)
    #edges = cv2.GaussianBlur(edges, (5, 5), 0.3)
    ret, edges = cv2.threshold(edges, v2, 180, cv2.THRESH_BINARY)
    #edges = cv2.bitwise_not(edges)

    if debug == True:
        cv2.imshow('original', img)
        cv2.imshow('blur', blur)
        cv2.imshow('mask', mask)
        cv2.imshow('res 1', res1)
        cv2.imshow('Edge %.2f'%SIGMA, edges)
        cv2.waitKey(0)


    #edges,
    cnts, hierarchy = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.ones(edges.shape[:2], dtype="uint8") * 255

    # loop over the contours to find out the suitable target
    font = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX
    i =0
    for c in cnts:
        # if the contour is bad, draw it on the mask
        i=i+1
        x, y, w, h = cv2.boundingRect(c)
     #   cv2.putText(edges, ("%d" % i), (x, y), font, 0.4, (255, 0, 0), 2)
        if _is_contour_bad(edges,i,c)==True:
            cv2.drawContours(mask, [c], -1, (0,0,0), 2,cv2.FILLED)
        cv2.putText(edges, ("%d" % i), (x, y), font, 0.4, (255, 0, 0), 1)
    # remove the contours from the image and show the resulting images


    #cv2.imshow('Mask', mask)
    #cv2.waitKey(0)

    image = cv2.bitwise_and(edges, mask, mask=mask)

    #edges,
    contours,hierarchy = cv2.findContours(image, 1, 2)
    the_max=0.0
    the_index=0
    for i in range(0,len(contours)):
        area = cv2.contourArea(contours[i])
        x, y, w, h = cv2.boundingRect(contours[i])
        if area> the_max:
            the_max = area;the_index = i
            print (" %d is more, area is %d"%(i+1,area))
    x, y, w, h = cv2.boundingRect(contours[the_index])
    print ("the biggest one is %3d x %d y %d w %3d h %3d area %d"%(the_index,x,y, w,h, the_max))
    blackscreen = np.zeros((edges.shape[0],edges.shape[1],3))
    cv2.drawContours(blackscreen, contours, the_index, (255,255,255), 2)
    #generate cropped contour for the plant only
    crop_contours = blackscreen[y:y + h, x:x + w]
    crop_img = res1[y:y + h, x:x + w]
    if debug == True:
        cv2.imshow('1', crop_contours)
        cv2.imshow("2", crop_img)
        cv2.waitKey(0)
    #area = cv2.contourArea(contours[the_index-1])
    return the_max, crop_img,crop_contours



def _is_contour_bad(c):
    pic_h, pic_w = [720,960]
    min_h = int(pic_h*0.1)
    min_w = int(pic_w*0.1)
    # whether it's too small
    x, y, w, h = cv2.boundingRect(c)
    offset_x = x+w/2
    offset_y = y+h/2
    if ((pic_w / 3 > offset_x) or  (offset_x>(2 * pic_w) / 3)) and ((pic_h/3> offset_y) or (offset_y >2*pic_h/3)):
        print (" is not in middle area, offset X  %d Y %d"%(x+w/2,y+h/2))
        return True
    if (w<min_w and h<min_h):
        print ("too small, w %3d h %3d at X %3d Y %3d"%(w,h,x,y))
        return True

    peri = cv2.arcLength(c, True)
    if abs(peri - 3.14159*(w+h))/peri >0.4:
        print("likely a noise, w %d h %d peri %d" % (w , h, peri))
        return True
    if abs(peri - 3.14159*(w+h))/peri <0.05:
        print (" likely a circle, diameter %d pixels"%((w+h)/2))
        return False
    # or a rectangle (the channel in the image)
    approx = cv2.approxPolyDP(c, 0.05 * peri, True)
    if len(approx)==4 and (w ==960 or h==720):
        print("is rectangle, approx %d w %d h %d"%(len(approx), w, h))
        return True
    print ("------------ Not bad")
    return False


def findRedCard(img,debug=False):
    #range for red color in HSV system
    low_range = np.array([0,43,46])
    up_range = np.array([10,255,255])
    mask1 = cv2.inRange(img, low_range, up_range)
    #another range of red color
    low_range = np.array([155,50,46])
    up_range = np.array([180,255,255])
    mask2 = cv2.inRange(img, low_range, up_range)
    #combine them
    mask = cv2.bitwise_or(mask1, mask2)

    kernel = np.ones((5, 5), np.uint8)
    #remove the noise in the close area
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    cnts, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
#    print (len(cnts))
    #cv2.imwrite("/home/pi/myplot/plotapp/ui/static/crops/red_mask.jpg",mask)
    cnts = sorted(cnts, key=lambda k: cv2.contourArea(k), reverse=True)

    #if debug == True:
        #cv2.imshow('original', img)
        #cv2.imshow('mask', mask)
        #cv2.imshow('mask1', mask1)
        #cv2.imshow('mask2', mask2)
        #cv2.imshow('Edge ', edges)
        #cv2.waitKey(0)

    #find the rectangle box
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.05 * peri, True)
        if len(approx) == 4 and (w > 20 or h > 20) and (abs(w-h)/w<0.15):
            print("is rectangle w %d h %d"%(w,h))
            return cv2.contourArea(c)/(2*2),peri/(2*4)
        else:
            print("This is not red card  approx %d w %d h %d" % (len(approx), w, h))

    #print ("cant find the red card")
    raise RuntimeError ("cant find the red card")
    #return 0

def _get_image_area(img,debug=False):

    try:
        v1 = np.median(img)
        # Convert BGR to HSV
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        area_coef,diam_coef = findRedCard(hsv,debug)

        v2 = np.median(hsv)
        print("v1 %d V2 %d" % (v1,v2))
        if v2 > 65:
            lh = 32;uh = 80;vl = 60
        else:
            lh = 24;uh = 65;vl = 50

        # find the best paramter to filter the noises
        last_cn=999
        i=0
        stop_flag = False
        while True:
            s = int(v1/3)+i*3
            if s > v1: break
            lower_green = np.array([32, s, vl])
            upper_green = np.array([90, 255, 220])
            print(lower_green)
            # Threshold the HSV image to get only green colors
            mask = cv2.inRange(hsv, lower_green, upper_green)
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            cnts, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            current_cn=len(cnts)
            print ("contours in mask %d"%(len(cnts)))
            if stop_flag == True: break
            if (current_cn >60) and i<20:
                if (current_cn>last_cn):
                    i=i-1
                    stop_flag=True
                    continue
                i+=1
                if s>90: break
                print ("last cn %d current cn %d"%(last_cn,current_cn))
                last_cn = current_cn
            else:
                break
        # Bitwise-AND mask and original image
        res1 = cv2.bitwise_and(img, img, mask=mask)

        gs = cv2.cvtColor(res1, cv2.COLOR_RGB2GRAY)
        ret_otsu, im_bw_otsu = cv2.threshold(gs, 50, 180, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        kernel = np.ones((10, 10), np.uint8)
        edges = cv2.morphologyEx(im_bw_otsu, cv2.MORPH_CLOSE, kernel)


        cnts, hierarchy = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts, key=lambda k: cv2.contourArea(k),reverse=True)

        mask2 = np.ones(edges.shape[:2], dtype="uint8") * 255
        if debug == True:
            cv2.imshow('original', img)
            cv2.imshow('mask', mask)
            cv2.imshow('res 1', res1)
            cv2.imshow('Edge' , edges)
            cv2.waitKey(0)

        # loop over the contours to find out the suitable target
        i = 0
        found_contour = None
        for c in cnts:
            # if the contour is bad, draw it on the mask
            i = i + 1
            if i>3: break
            print (i)
            if _is_contour_bad(c) == False:
                cv2.drawContours(mask2, [c], -1, (0, 0, 0), 2, cv2.FILLED)
                found_contour =c
                break
            x, y, w, h = cv2.boundingRect(c)

            if h>20 and w>20 and debug:
                crop_contours = edges[y:y + h, x:x + w]
                cv2.imshow('mask2 %d'%i , crop_contours)
                cv2.waitKey(0)

        if found_contour is None:
            found_contour = cnts[0]
            #raise RuntimeError("Can't find out proper contour from the photo!")
            #return -1,None,None,None

        x, y, w, h = cv2.boundingRect(found_contour)
        max_diameter = max(w,h)/diam_coef
        crop_contours = mask2[y:y + h, x:x + w]
        crop_img = res1[y:y + h, x:x + w]
    except Exception as e:
        raise (e)

    if debug == True:
        cv2.imshow('contours', crop_contours)
        cv2.imshow("cropped img", crop_img)
        cv2.waitKey(0)
    # area = cv2.contourArea(contours[the_index-1])
    return cv2.contourArea(found_contour)/area_coef, max_diameter, crop_img, crop_contours


def capture_img(dir):
    import subprocess
    result = False
    t = datetime.datetime.now()
    current_time = t.strftime("%d/%m/%Y %H:%M:%S")
    file_name = "crop-"+ t.strftime("%Y-%m-%d-%H.%M.%S") +".jpg"
    try:
        path = dir+file_name
        subprocess.run('sudo fswebcam -r 960x720  -D 1 '+path, shell=True,  check=True)
        #os.system('sudo fswebcam -r 960x720  -D 1 '+path)
    #    if  os.path.exists(path) ==False:
    #        print("file %s is not exist!"%path)
    #        return result
        #print ("path %s"%path)
        image = cv2.imread(path)  # failed to take a picture
    except FileNotFoundError as e:
        print ("capture img failed")
        raise RuntimeError(e.strerror)
    if (np.average(image) < 50):
        print(path + " is too dark!")
        os.remove(path)

    result = True
    return result,file_name,current_time

def process_img(path,file_name,debug=False):
    area = -1
    try:
        if os.path.exists(path+file_name) == False :
            print ("file is not exist!")
            raise RuntimeError("The file %s is not exist!"%(path+file_name))
            #return -1,0
        image = cv2.imread(path+file_name)  # failed to take a picture
        if (np.average(image) < 50):
            print(path + " is too dark!")
            raise RuntimeError("The photo named %s is too dark!"%path)
            #return -1,0
        h,w,ch =image.shape
        scale = min(720/h,960/w)
        if scale != 1:
            image = cv2.resize(image, (0, 0), fx=scale, fy=scale)

        image=cv2.normalize(image, image, 64, 196, cv2.NORM_MINMAX)
        # cv2.normalize(image,image,0,1,cv2.NORM_RELATIVE)
        if debug == True:
            #cv2.imshow('image1', image1)
            cv2.imshow("image", image)
            cv2.waitKey(0)
        area, diameter, cropped, cont = _get_image_area(image,debug)
        if area > 0:
            #get_new(image)
            crop_file = path+file_name.replace(".jpg","-1.jpg")
            cont_file = path+file_name.replace(".jpg", "-2.jpg")
            cv2.imwrite(crop_file,cropped)
            cv2.imwrite(cont_file,cont)
        else:
            return -1,0
    except Exception as e:
        print (e)
        raise(e)
        #return -1,0

    print ("area %.3f diameter %.3f"%(area,diameter))
    return area,diameter

def store_data(current_time,area,diameter,file_name):
    try:
        conn = sqlite3.connect('/home/pi/myplot/myplot.db')
        c = conn.cursor()
        # Insert a row of data
        sql_statement = 'insert into datarecord (time, place, name, value1, unit1,value2) values ("'\
                        + current_time +'","plot", "growth",' + '%.3f'%area +',"cm^2","' + file_name+'")'
        print (sql_statement)
        c.execute(sql_statement)

        # Save (commit) the changes
        conn.commit()
        conn.close()
    except Exception as e:
        print (e)
        raise (e)
        return -1

def reprocessAndUpdateData(path,file_name):
    area = process_img(path,file_name)
    if area == -1:
        print("failed to process img")
    try:
        conn = sqlite3.connect('../myplot.db')
        c = conn.cursor()
        # Insert a row of data
        sql_statement = 'update datarecord set value1 =%.3f where (value2 = "%s")'%(area,file_name)
        print (sql_statement)
        c.execute(sql_statement)

        # Save (commit) the changes
        conn.commit()
        conn.close()
    except Exception as e:
        raise(e)
        print (e)
        return -1



def test():
    path ='D:\\project\\greenway\\aigrow\\frontend\\static\\crops\\'
    #file = path + 'crop-2018-06-30-16.30.49.jpg' #bad
    #file = path + 'crop-2018-06-30-16.08.33.jpg'  #area is smaller
    #file = path + 'crop-2018-07-01-07.55.32.jpg'
    #file = path + 'crop-2018-07-01-13.17.04.jpg'  #V 93,87
    #file = path + 'crop-2018-07-01-16.08.58.jpg' #bad
    #file = path + "crop-2018-07-03-18.39.05.jpg"
    #file = path + "crop-2018-07-03-18.39.47.jpg"
    #file = path + "crop-2018-07-03-18.39.05.jpg"
    #file = path + 'crop-2018-07-03-18.48.45.jpg'
    #file = path + "IMG_20180713_065038.jpg"
    #file = path + "IMG_20180713_065044.jpg"
    #file = path + "IMG_20180713_085759.jpg"
    file = path + "crop-2018-07-13-09.36.30.jpg"
    file = path + "crop-2018-07-13-09.34.13.jpg"
    #file = path + "crop-2018-07-13-13.17.13.jpg"
    #file = path + "crop-2018-07-24-18.06.35.jpg"
    #file = path + "crop-2018-07-29-09.22.50.jpg"
    #get_new(image)

    area,diameter = process_img("",file,debug=True)


    #reprocessAndUpdateData(path, 'crop-2018-06-30-16.30.49.jpg')

def get_img_reading():
    try:
        path = '/home/pi/myplot/plotapp/ui/static/crops/'  #don't forget the "/" in the end
        ret, file_name, time = capture_img(path)
        if ret == False:
            os.remove(path + file_name)
            exit (-1)
        print("now process img")
        area,diameter = process_img(path,file_name)
        if area == -1:
            print("failed to process img")
            #os.remove(path + file_name)
            exit(-1)
        if store_data(time,area,diameter,file_name)== -1:
            print ("failed to store data")
            os.remove(path + file_name)
            exit(-1)
    except Exception as e:
        raise (e)

if __name__ == '__main__':

    test()
    exit(0)

    #get_reading()

