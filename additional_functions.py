import json
import os


def find_qgis_instance_dir(file_name='python-qgis-ltr.bat') -> str:
    for root, dirs, files in os.walk('/'):
        if all((file_name in files, 'QGIS' in os.path.abspath(os.path.join(root, file_name)))):
            return os.path.abspath(root)


def find_qgis_project_dir() -> str:
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    list_dir = os.listdir(parent_dir)
    if 'qgis' in list_dir:
        return '\\'.join((parent_dir, 'qgis'))


def dump_aprx_properties_to_json(json_path, aprx_properties_dict) -> None:
    with open(json_path, 'w') as write_file:
        json.dump(aprx_properties_dict, write_file)
