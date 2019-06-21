import os
import json
import importlib

__currentDir__ = os.getcwd() + '/'
__configFile__ = __currentDir__ + 'config.json'

if os.path.exists(__configFile__):
    with open(__configFile__) as res:    
        config = json.load(res)
else:
    print('설정 파일이 없어 시스템을 실행할 수 없습니다.')
    exit()

print(config)