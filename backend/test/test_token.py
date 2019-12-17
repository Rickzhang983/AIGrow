from backend.idm import tokenservice as tws
import time

s1 = time.time()
for i in range(1, 2):
    tokenJson = tws.generateToken(1, "Rick")
    # s2 = time.time()
    print("-----gernate token: ", tokenJson)
    # print (s2-s1)
    # s1 = time.time()
    # userid,  msg = getUseridByToken(tokenJson)
    userid, username, msg = tws.decodeToken(tokenJson)
    print(userid, msg)
s2 = time.time()
print(s2 - s1)
token = b'eyJhbGciOiJIUzUxMiIsImlhdCI6MTU1Njg3NDQwNywiZXhwIjozMTE1NTQ4ODE0LjQ4NzEyNDR9.eyJ1c2VyX2lkIjoiMSIsIm5hbWUiOiJSaWNrIiwiaXNzIjoiYWktZ3JvdyIsImV4cCI6MTU1ODY3NDQwNy40ODcxMjQ3LCJpYXQiOjE1NTY4NzQ0MDcuNDg3MTI0N30.23jG3reRryTI7KuSu710UkBoecSVSm2Z83J0-8-N08BD4J_p51z9xqUMV9IX2Kl4t9AVdzkONWTtsHPhJwoVjQ'
# token = tokenJson
userId, userName, msg = tws.decodeToken(token)
print("user", userId, userName, msg)
print ('key map',tws.keymap)