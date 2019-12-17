# _*_coding:utf-8_*_
import time
from flask import jsonify
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature, BadData


# jwt配置
jwt_cnf = {
    'typ': 'JWT',
    'alg': 'HS256',
    'salt': b'ai-grow',
    'key_len':8,
    'timeout':1800000
}
sec_key = "ExgxGDbA"
keymap={}


""" token is generated as the JWT protocol (RFC 7519)
"""
def generateToken( user_id,user_name):
    timestamp = time.time()
    expires = timestamp + jwt_cnf['timeout']

    s = Serializer(
        secret_key = sec_key,
        salt = jwt_cnf['salt'],
        expires_in = expires)

    token = s.dumps(
        {'user_id': user_id,
         'name': user_name,
         'iss': "aigrow",
         'exp': expires,
         'iat': timestamp})
    keymap[token] = user_id
    # print ("token generated, keymap ",keymap)
    return token

def decodeToken (token):
        # token decoding
    s = Serializer(
            secret_key = sec_key,
            salt = jwt_cnf['salt'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        msg = 'token expired'
        return [None, None, msg]
    except BadSignature as e:
        encoded_payload = e.payload
        if encoded_payload is not None:
            try:
                s.load_payload(encoded_payload)
            except BadData:
                # the token is tampered.
                msg = 'token tampered'
                return [None, None, msg]
        msg = 'badSignature of token'
        return [None, None, msg]
    except:
        msg = 'wrong token with unknown reason'
        return [None, None, msg]

    if ('user_id' not in data):
        msg = 'illegal payload inside'
        return [None, None, msg]
    msg = 'user(' + data['name'] + ') logged in by a token.'
    userId = data['user_id']
    userName = data['name']
    return userId, userName, msg

def getUseridByToken(token):
    # if it's in the same python instance, the user id shall be available.
    try:
        userid = keymap[token]
    except KeyError as e:
        userid = None
    # but the request might be sent to another one
    if userid:
        msg = ""
        # print ("user id %s found in keymap"%userid)
        return userid, msg
    else:
        #print("user id NOT found in keymap, hence decode it")
        userid,username ,msg = decodeToken (token)
        # add to keymap to improve the performance
        # print ("decoded userid is",userid)
        if userid:
            keymap[token] = userid
        return userid, msg


if __name__ == '__main__':
    #代码测试
    s1 = time.time()
    for i in range (1,2):
        tokenJson = generateToken("1","Rick")
    # s2 = time.time()
        #print ("-----gernate token: ",tokenJson)
    # print (s2-s1)
    # s1 = time.time()
        # userid,  msg = getUseridByToken(tokenJson)
        userid, username, msg = decodeToken(tokenJson)
        #print (userid, msg)
    s2 = time.time()
    print(s2 - s1)
    token = b'eyJhbGciOiJIUzUxMiIsImlhdCI6MTU1Njg3NDQwNywiZXhwIjozMTE1NTQ4ODE0LjQ4NzEyNDR9.eyJ1c2VyX2lkIjoiMSIsIm5hbWUiOiJSaWNrIiwiaXNzIjoiYWktZ3JvdyIsImV4cCI6MTU1ODY3NDQwNy40ODcxMjQ3LCJpYXQiOjE1NTY4NzQ0MDcuNDg3MTI0N30.23jG3reRryTI7KuSu710UkBoecSVSm2Z83J0-8-N08BD4J_p51z9xqUMV9IX2Kl4t9AVdzkONWTtsHPhJwoVjQ'
    #token = tokenJson
    userId, userName, msg = decodeToken(token)
    print ("user", userId,userName,msg)
    # print(tokenJson.get("access_token").decode())
    #eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdXRob3NfaWQiOiIxMDAwMyIsInVzZXJfbmFtZSI6IjE1N3h4eHg0NTA1IiwicGFzc193b3JkIjoiOWEyYWFjNjM0OWIwY2QwYWY1NjRmZGI5ZmZlOWU5YjUiLCJpYXQiOjE1MzQyNTY2MTYuNTkxMjY5LCJleHAiOjE1MzQyNTY2MTcuNTkxMjY5fQ.ydWFF_O60vRk6U0kjlGI_0_8fD41qvZ-yF1DBxIVdTQ
    #print(check_token(tokenJson.get("access_token").decode()))
    #(True, {'authos_id': '10003', 'user_name': '157xxxx4505', 'pass_word': '9a2aac6349b0cd0af564fdb9ffe9e9b5', 'iat': 1534256616.591269, 'exp': 1534256617.591269})