import os
import sys
import pip
import shutil
import configparser
import binascii
import artshowkeeper

def verify_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


if sys.argv[1] == '-install':
    dependencies=['flask', 'pillow', 'netifaces']
    for package in dependencies:
        pip.main(['install', package])

    data_dir = get_special_folder_path("CSIDL_APPDATA")
    print('data_dir: {0}'.format(data_dir)) #DEBUG

    deployment_dir = os.path.join(os.path.dirname(artshowkeeper.__file__), 'deployment')
    print('deployment_dir: {0}'.format(deployment_dir)) #DEBUG

    app_data_dir = verify_dir(os.path.join(data_dir, 'artshowkeeper'))
    print('deployment_dir: {0}'.format(app_data_dir)) #DEBUG

    data_dir = verify_dir(os.path.join(app_data_dir, 'Data'))
    verify_dir(os.path.join(data_dir, 'image'))
    custom_data_dir = verify_dir(os.path.join(app_data_dir, 'Custom'))

    print('custom_data_dir: {0}'.format(custom_data_dir)) #DEBUG
    config = configparser.ConfigParser()
    config['DEFAULT']['DEFAULT_LANGUAGE'] = 'cz'
    config['DEFAULT']['LOG_FILE'] = os.path.join(app_data_dir, 'artshow.log')
    config['DEFAULT']['DATA_FOLDER'] = data_dir
    config['DEFAULT']['CUSTOM_DATA_FOLDER'] = custom_data_dir
    config['DEFAULT']['CURRENCY'] = 'czk,eur,usd'
    config['DEFAULT']['LANGUAGES'] = 'cz,en,de'
    config['DEFAULT']['SECRET_KEY'] = str(binascii.hexlify(os.urandom(24)), 'ascii')

    ini_file = os.path.expanduser('~/.artshowkeeper.ini') 
    with open(ini_file, 'w') as config_file:
        config.write(config_file)
    file_created(ini_file)

    shutil.copy(os.path.join(deployment_dir, 'currency.xml'), os.path.join(data_dir, 'currency.xml'))

    desktop_dir = get_special_folder_path("CSIDL_DESKTOPDIRECTORY")
    link_file_name = 'Artshow Keeper.lnk'
    create_shortcut(
            os.path.join(sys.prefix, 'python.exe'),
            'Artshow Keeper',
            link_file_name,
            '-c "import artshowkeeper.run_desktop"',
            '',
            os.path.join(deployment_dir, 'icon.ico'),
    )
    shutil.move(os.path.join(os.getcwd(), link_file_name), os.path.join(desktop_dir, link_file_name))
    file_created(os.path.join(desktop_dir, link_file_name))

    link_file_name = 'Artshow Keeper Custom Directory.lnk'
    create_shortcut(
            custom_data_dir,
            'Artshow Keeper Custom Directory',
            link_file_name,
            '',
            '',
            os.path.join(deployment_dir, 'icon.ico'),
    )
    shutil.move(os.path.join(os.getcwd(), link_file_name), os.path.join(desktop_dir, link_file_name))
    file_created(os.path.join(desktop_dir, link_file_name))
