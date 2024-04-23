import base64
import json
import os


if __name__ == '__main__':
    print('helllo')
    secret = os.environ.get('SA_SECRET', '{}')
    print(secret)
    print(json.loads(base64.b64decode(secret).decode('utf-8')))
