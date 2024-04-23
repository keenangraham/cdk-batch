import json
import os


if __name__ == '__main__':
    print('helllo')
    print(os.environ.get('SA_SECRET', 'no secret'))
    print(json.loads(os.environ.get('SA_SECRET', '{}')))
