import sys
import re

SUCCESS = 0
FAILURE = 128
MODULE_NOT_FOUND = 129
VERSION_NOT_FOUND = 130

def is_newer_or_same_version(version1, version2):
    def normalize(version):
        return [int(component) for component in re.sub(r'(\.0+)*$','', version).split(".")]
    version1 = normalize(version1)
    version2 = normalize(version2)
    for i in range(min(len(version1), len(version2))):
        if version1[i] > version2[i]:
            return True
        elif version1[i] < version2[i]:
            return False
    return True

def check_module(moduleName, requestedVersion):
    module = None
    try:
        module = __import__(moduleName, fromlist=[''])
    except ImportError as err:
        return MODULE_NOT_FOUND

    version = None
    try:
        version = module.__version__
    except AttributeError:
        if requestedVersion == '0':
            return SUCCESS
        else:
            return VERSION_NOT_FOUND
        
    if not is_newer_or_same_version(version, requestedVersion):
        return VERSION_NOT_FOUND
    else:
        return SUCCESS

def main(argv):
    if argv is not None and len(argv) == 2:
        return check_module(argv[0], argv[1])
    else:
        return FAILURE
    
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
