import os
import json
import errno
import requests
from copy import copy
from logging import handlers
from logging import Formatter
import zipfile
import logging
import shutil
import importlib

__currentDir__ = os.getcwd() + '/'
__sourceDir__ = __currentDir__ + 'src/'
__configFile__ = __currentDir__ + 'config.json'
logger = logging.getLogger()

class ColoredFormatter(Formatter):
    def __init__(self, patern):
        Formatter.__init__(self, patern)

    def format(self, record):
        colored_record = copy(record)
        levelname = colored_record.levelname
        seq = {
            'DEBUG'   : 35,
            'INFO'    : 36,
            'WARNING' : 33,
            'ERROR'   : 31,
            'CRITICAL': 41,
        }.get(levelname, 37)
        colored_levelname = ('{0}{1}m{2}{3}') \
            .format('\033[', seq, levelname, '\033[0m')
        colored_record.levelname = colored_levelname
        return Formatter.format(self, colored_record)

def initLogger():
    logger.debug('START "initLogger()" METHOD')

    fileHandler = logging.FileHandler(config['logger']['path'], encoding='utf-8')
    fileHandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(ColoredFormatter('[%(asctime)s][%(levelname)s] %(message)s (%(filename)s:%(lineno)d)'))

    logger.setLevel(logging.getLevelName(config['logger']['level']))
    logger.addHandler(fileHandler)
    logger.addHandler(consoleHandler)

def mkdir(dir):
    logger.debug('START "mkdir(' + dir + ')" METHOD')
    try:
        os.makedirs(dir)
    except OSError as exc: 
        if exc.errno == errno.EEXIST and os.path.isdir(dir):
            pass

def moduleFile(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def checkUpdate():
    logger.debug('START "checkUpdate()" METHOD')
    headers = {
        'user-agent': __userAgent__
    }

    try:
        res = requests.get(config['remote']['baseURL'], headers=headers)
        res.raise_for_status()
        resJson = res.json()

        if resJson['status'] != 'success':
            logger.error('서비스 상태가 불안하여 서비스를 종료합니다.')

        if resJson['version'] == config['version']:
            logger.info('해당 버전은 최신 상태입니다. (현재버전: %s)' % config['version'])
        else:
            try:
                logger.info('새로운 업데이트가 있습니다. (현재버전: %s, 최신버전: %s' % (config['version'], resJson['version']))
                updateDir = __currentDir__ + 'tmpUpdate/'
                updateFile = updateDir + 'latest.zip'
                mkdir(updateDir)
                logger.info('업데이트 상태를 확인하고 있습니다.')
                updateReq = requests.get(resJson['url'], stream=True)
                res.raise_for_status()
                logger.debug('UPDATE FILE HAS NO PROBLEMS')
                logger.debug('START UPDATE FILE DOWNLOADING')
                logger.info('업데이트 파일을 다운로드 받고 있습니다..')
                with open(updateFile, 'wb') as f:
                    updateReq.raw.decode_content = True
                    shutil.copyfileobj(updateReq.raw, f)
                logger.debug('UPDATE DOWNLOAD SUCCESS')
                logger.debug('REMOVE OLD VERSION')
                logger.info('기존 설정을 삭제합니다.')
                if os.path.isdir(__sourceDir__):
                    shutil.rmtree(__sourceDir__)
                updateZip = zipfile.ZipFile(updateFile, 'r')
                updateZip.extractall(__currentDir__)
                updateZip.close()
                logger.info('업데이트 파일을 모두 다운로드하였습니다.')
                moduleFile('setup', __sourceDir__ + 'setup.py')
                logger.info('업데이트 추가 설정이 완료되었습니다.')
            except Exception as err:
                logger.error('업데이트할 수 없습니다.')
                logger.error(err)
            finally:
                shutil.rmtree(__currentDir__ + 'tmpUpdate/')
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        logger.error('서버에 연결할 수 없어 서비스를 종료합니다.')
    except requests.exceptions.HTTPError:
        logger.error('서비스 상태가 불안하여 서비스를 종료합니다.')

def runService():
    logger.debug('START "runService()" METHOD')
    logger.info('서비스를 시작하는 중입니다.')
    moduleFile('index', __sourceDir__ + 'index.py')

if __name__ == "__main__":
    logger.debug('START "init()" METHOD')
    if os.path.exists(__configFile__):
        with open(__configFile__) as res:
            config = json.load(res)
    else:
        print('설정 파일이 없어 시스템을 실행할 수 없습니다.')
        exit()

    __userAgent__ = 'Tunnelus/%s (%s)' % (config['version'], config['id'])
    initLogger()
    checkUpdate()
    runService()
