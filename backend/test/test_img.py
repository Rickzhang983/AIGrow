import PIL.Image
import PIL.ExifTags
import exifread

file_name = "c:\\users\\rick\\documents\\20191007085413.jpg" # "D:\\project\\greenway\\aigrow\\testimg\\IMG_20180713_065044.jpg"
FIELD = 'EXIF DateTimeOriginal'
with open(file_name, 'rb') as fd:
    tags = exifread.process_file(fd)
    print("exif tags",tags)
if FIELD in tags:
    #new_name = str(tags[FIELD]).replace(':', '').replace(' ', '')  # + os.path.splitext(filename)[1]
    print ("date", tags[FIELD])
else:
    # 通过 PIL.Image.open 读取图片
    img = PIL.Image.open(file_name)

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
