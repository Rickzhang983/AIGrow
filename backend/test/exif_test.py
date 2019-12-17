import os ,exifread,re, datetime
import PIL.Image


def getTimeInfoFromFile(full_file_name):
    FIELD = 'EXIF DateTimeOriginal'
    with open(full_file_name, 'rb') as fd:
        tags = exifread.process_file(fd)
    if FIELD in tags:
        new_name = str(tags[FIELD]).replace(':', '').replace(' ', '') #+ os.path.splitext(filename)[1]
    else:
        # 通过 PIL.Image.open 读取图片
        img = PIL.Image.open(full_file_name)

        try:
            # 生成手机参数数据字典
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in img._getexif().items()
                if k in PIL.ExifTags.TAGS
            }
            # 打印这些信息
            for info in exif:
                print(info, end=':')
                print(exif[info])
            new_name = ""
        except AttributeError:
            print("No exif information")
            new_name = full_file_name.replace(":", "").replace(" ", "_").replace("-", "")
            new_name = re.sub(r'\D', "", new_name)


    if (len(new_name)==14):
        year = int(new_name[0:4])
        month = int(new_name[4:6])
        day = int(new_name[6:8])
        hour = int(new_name[8:10])
        minute = int(new_name[10:12])
        sec = int(new_name[12:14])
        print ("The time identified as", year,month,day,hour,minute,sec)
        return True, datetime.datetime(year,month,day,hour,minute,sec)
    else:
        return False,None



imagefiles = []
path = "..//..//testimg"
for file in os.listdir(path):
    result, t = getTimeInfoFromFile(path+'//'+file)
    if result:
        print (t)
