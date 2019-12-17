
from werkzeug.datastructures import Headers

def func (**kwargs):
    kwargs['headers'] = ''
    headers = kwargs.get('headers')
    # 跨域控制
    origin = ('Access-Control-Allow-Origin', '*')
    header = ('Access-Control-Allow-Headers', 'Content-Type')
    methods = ('Access-Control-Allow-Methods', 'HEAD, OPTIONS, GET, POST, DELETE, PUT')
    if headers:
        headers.add(*origin)
        headers.add(*header)
        headers.add(*methods)
    else:
        headers = Headers([origin, header, methods])
    print (headers)


func()