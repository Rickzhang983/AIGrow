from backend.dataservice import image
import cv2

def test():

    # Image data
    import glob,os

    imagefiles = []
    for file in glob.glob("crops//crop-2018-07-1*.??.jpg"):
        imagefiles.append(file)
    for file in glob.glob("crops//crop-2018-07-2*.??.jpg"):
        imagefiles.append(file)
    for file in glob.glob("crops//crop-2018-07-3*.??.jpg"):
        imagefiles.append(file)
    for file in glob.glob("crops//crop-2018-08*.??.jpg"):
        imagefiles.append(file)
    imagefiles.sort()

    files =['crop-2018-07-29-09.22.50.jpg', 'crop-2018-07-13-09.34.13.jpg','crop-2018-07-24-14.28.28.jpg','IMG_20180713_065038.jpg', \
            'crop-2018-07-13-09.36.30.jpg','IMG_20180713_065044.jpg','crop-2018-07-13-12.48.13.jpg',\
            'IMG_20180713_085759.jpg','crop-2018-07-13-13.17.13.jpg','IMG_20180713_085811.jpg', 'crop-2018-07-13-09.30.14.jpg',\
            'crop-2018-07-24-18.06.35.jpg']
    files2 = ['crop-2018-07-29-09.16.42.jpg','crop-2018-07-29-09.18.59.jpg','crop-2018-07-29-09.20.44.jpg','crop-2018-07-29-09.22.50.jpg',\
            'crop-2018-08-02-08.04.24.jpg','crop-2018-08-02-08.04.40.jpg','crop-2018-08-03-17.18.04.jpg']
    files += files2

    failed =[\
    'crops\crop-2018-07-29-09.22.50.jpg',\
'crops\crop-2018-07-16-11.02.25.jpg',\
'crops\crop-2018-07-16-11.05.58.jpg',\
'crops\crop-2018-07-16-19.44.34.jpg',\
'crops\crop-2018-07-16-19.45.01.jpg',\
'crops\crop-2018-07-16-19.48.26.jpg',\
'crops\crop-2018-07-16-19.50.09.jpg',\
'crops\crop-2018-07-16-19.50.27.jpg',\
'crops\crop-2018-07-16-19.50.47.jpg',\
'crops\crop-2018-07-16-19.51.16.jpg',\
'crops\crop-2018-07-16-19.53.45.jpg',\
'crops\crop-2018-07-22-08.10.04.jpg',\
'crops\crop-2018-07-22-08.10.17.jpg',\
'crops\crop-2018-07-22-08.10.30.jpg',\
'crops\crop-2018-07-22-08.13.44.jpg',\
'crops\crop-2018-07-22-08.14.33.jpg']

    #imagefiles =["crops\crop-2018-07-29-19.43.18.jpg","crops\crop-2018-07-19-14.22.11.jpg",\
    #             "crops\crop-2018-07-29-19.42.27.jpg","crops\crop-2018-07-29-19.37.34.jpg","crops\crop-2018-08-01-18.19.47.jpg",\
    #             "crops\crop-2018-08-01-18.20.09.jpg","crops\crop-2018-07-23-19.20.08.jpg","crops\crop-2018-07-29-19.36.23.jpg"]

    err = open("error.txt","w+")
    result = open("result.csv","w+")
    result.write('--------file_name-----------  area    diameter\n')
    err.write("Total %d files\n"%len(imagefiles))
    import time

    start_time = time.clock()
    i=0
    for file in imagefiles:
        if file in failed:
            continue
        try:
            print('******** file name %s ********' % (file))
            area, max_diameter, crop_img = image.process_img(file,False)
            path = './results'
            filename = os.path.split(file)[1]
            result.write ('%s, %.3f, %.3f\n'%(filename, area,max_diameter))
            cv2.imwrite(os.path.join(path, filename), crop_img)
            #cv2.imshow(filename,crop_img)

        except Exception as e:
            print (e)
            i += 1
            err.write("'%s : %s',\\\n"%(file,str(e)))
            path = './failed'
            filename = os.path.split(file)[1]
            from shutil import copyfile
            copyfile(file, os.path.join(path, filename))
            continue
    print ("%d/%d file failed" % (i,len(imagefiles)))
    err.write("%d/%d file failed: " % (i,len(imagefiles)))
    print(" time elapsed %.3f"%(time.clock()-start_time))
    err.write(" time elapsed %.3f"%(time.clock()-start_time))
    result.close()
    err.close()
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

if __name__ == '__main__':
    test()