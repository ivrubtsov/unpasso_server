# Credits go to:
# https://www.facebook.com/permalink.php?id=120707754619074&story_fbid=389700354386478
# Fixed spacing (posting python on facebook is gr8 idea guys)
# Added generating passwords.

from hashlib import md5
import random

itoa64 = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'


def encode64(textInput,count):
    output = ''
    i = 0
    print(textInput)
    while i < count:
        i = i + 1
        print('i='+str(i))
        print('textInput[i-1]='+str(textInput)[i-1])
        value = ord(str(textInput)[i-1])
        output = output + itoa64[value & 63]
        if i < count :
            print('textInput[i]='+textInput[i])
            value = value | ord(str(textInput)[i]) << 8
        output = output + itoa64[(value >> 6) & 63]
        i = i + 1
        if i >= count:
            break
        if i < count:
            value = value | ord(str(textInput)[i]) <<16
            output = output + itoa64[(value >> 12) & 63]
            i = i + 1
        if i >= count:
            break
        output = output + itoa64[(value >> 18) & 63]

    return output


def crypt_private(plainText, wordpressHash=None):
    if not wordpressHash:
        # generate new salt:
        wordpressHash = '$P$' + random.choice(itoa64[10:14])
        for i in range(8):
            wordpressHash += random.choice(itoa64)

    output = '*0' # old type | not supported yet
    if wordpressHash[0:2] == output:
        output = '*1'
    if wordpressHash[0:3] != '$P$': # old type | not supported yet
        return output

    # get who many times will generate the hash
    count_log2 = itoa64.find(wordpressHash[3])
    if (count_log2 < 7) or (count_log2 > 30):
        return output

    count = 1 << count_log2 # get who many times will generate the hash

    salt = wordpressHash[4:12] # get salt from the wordpress hash
    if len(salt) != 8:
        return output
    # generate the first hash from salt and word to try
    strEncode = str(salt)+str(plainText)
    plainTextHash = md5(strEncode.encode('utf-8')).digest()
    print(plainTextHash)
    for i in range (count):
        # regenerate the hash
        strEncode = str(plainTextHash)+str(plainText)
        plainTextHash = md5(strEncode.encode('utf-8')).digest()
        print(plainTextHash)

    output = wordpressHash[0:12]
    print(plainTextHash)
    print('output')
    print(output)
    # get the first part of the wordpress hash (type,count,salt)
    output = output + encode64(plainTextHash,16) # create the new hash
    print(output)
    return output
