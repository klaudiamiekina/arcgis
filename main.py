from ast import literal_eval
from typing import List, Dict, Any

import arcpy
import json

from arcgis.apps.storymap import Map
from arcpy._mp import Layer

# APRX_PATH = r'C:\Users\klaud\OneDrive\Dokumenty\geoinformatyka\III_rok\praca_inz\arcpy_env\MyProject2\MyProject2.aprx'
JSON_PATH = r'C:\Users\klaud\OneDrive\Dokumenty\geoinformatyka\III_rok\praca_inz\arcpy_env\aprx_data2.json'
APRX_PATH = r"C:\Users\klaud\OneDrive\Dokumenty\geoinformatyka\III_rok\praca_inz\arcpy_env\MyProject2\MyProject2.aprx"


class AprxProject:
    arcgis_project = arcpy.mp.ArcGISProject(APRX_PATH)
    dict_types_of_layers = {
        'GroupLayer': 'GroupLayer',
        'WMSLayer': 'WMS',
        'FeatureLayer': ('WFS', 'Shape File'),
        'RasterLayer': 'Raster',
        'TiledServiceLayer': 'WMTS'
    }
    dict_properties_for_layers = {
        'WFS': {
            'source': 'layer.connectionProperties.get("connection_info").get("url")',
            'name': 'layer.name',
            'crs': 'arcpy.Describe(layer).spatialReference.PCSCode',
            'transparency': 'layer.transparency',
            'visible': 'layer.visible',
            'supergroup_id': ''
        },
        'Shape File': {
            'source': 'layer.dataSource',
            'name': 'layer.name',
            'crs': 'arcpy.Describe(layer).spatialReference.PCSCode',
            'transparency': 'layer.transparency',
            'visible': 'layer.visible',
            'supergroup_id': ''
        },
        'Raster': {
            'source': 'layer.dataSource',
            'name': 'layer.name',
            'crs': 'arcpy.Describe(layer).spatialReference.PCSCode',
            'transparency': 'layer.transparency',
            'visible': 'layer.visible',
            'supergroup_id': ''
        },
        'WMS': {
            'source': 'layer.dataSource',
            'name': 'layer.name',
            'crs': "int('2180')",
            'transparency': 'layer.transparency',
            'visible': 'layer.visible',
            'supergroup_id': ''
        },
        'WMTS': {
            'source': 'layer.dataSource',
            'name': 'layer.name',
            'crs': "int('2180')",
            'transparency': 'layer.transparency',
            'visible': 'layer.visible',
            'supergroup_id': ''
        },
        'GroupLayer': {
            'name': 'layer.name',
            'transparency': 'layer.transparency',
            'visible': 'layer.visible',
            'supergroup': f'''layer.longName.rstrip(layer.name).rstrip('\\\\')''',
            'id': f'''layer.URI.split('/')[1].split('.')[0]''',
            'longName': 'layer.longName'
        }
    }

    def __init__(self):
        self.arcgis_maps = self._get_arcgis_maps()
        self.aprx_properties = self._get_properties_from_map_and_update_aprx_properties()
        self._get_layers_from_map_and_update_aprx_properties()
        self._dump_aprx_properties_to_json(JSON_PATH)

    @property
    def arcgis_map_name(self):
        return self._arcgis_map_name

    @arcgis_map_name.setter
    def arcgis_map_name(self, var):
        self._arcgis_map_name = var

    def _get_arcgis_maps(self) -> List[Map]:
        arcgis_maps = []
        for aprx_map in self.arcgis_project.listMaps():
            arcgis_maps.append(aprx_map)
        return arcgis_maps

    def _get_properties_from_map_and_update_aprx_properties(self) -> Dict[str, Any]:
        aprx_properties = {}
        for arcgis_map in self.arcgis_maps:
            aprx_properties_for_map = {
                'extent_xmin': arcgis_map.defaultCamera.getExtent().XMin,
                'extent_ymin': arcgis_map.defaultCamera.getExtent().YMin,
                'extent_xmax': arcgis_map.defaultCamera.getExtent().XMax,
                'extent_ymax': arcgis_map.defaultCamera.getExtent().YMax,
                'map_crs': arcgis_map.spatialReference.PCSCode
            }
            self._arcgis_map_name = arcgis_map.name
            aprx_properties[arcgis_map.name] = aprx_properties_for_map
        return aprx_properties

    def _get_type_of_layer(self, layer: Layer) -> str:
        cim_type_of_layer = layer.getDefinition('V3').__str__().split('.CIM')[-1].split()[0]
        type_of_layer = None
        if not layer.isBasemapLayer:
            type_of_layer = self.dict_types_of_layers.get(cim_type_of_layer)
            if isinstance(type_of_layer, tuple):
                type_of_layer = layer.connectionProperties.get('workspace_factory')
        return type_of_layer

    def _update_dict(self, layer, type_of_layer, dict_type_of_layer, layers_from_map):
        temp_dict = {}
        if dict_type_of_layer:
            for key, value in dict_type_of_layer.items():
                if all((key in 'supergroup', '\\' not in layer.longName)):
                    continue
                if value == '':
                    temp_dict[key] = ''
                    continue
                temp_dict[key] = eval(value)
            # if type_of_layer not in 'GroupLayer' and '\\' in layer.longName:
            #     list_of_groups = [group_dict for group_dict in layers_from_map
            #                       if list(group_dict.keys())[0] in 'GroupLayer']
            #     for group_dict in reversed(list_of_groups):
            #         long_name = group_dict.get('GroupLayer').get('longName')
            #         if long_name == layer.longName.strip(f'{layer.name}').strip('\\'):
            #             temp_dict['supergroup_id'] = group_dict.get('GroupLayer').get('id')
            #             break
            if '\\' in layer.longName:
                list_of_groups = [group_dict for group_dict in layers_from_map
                                  if list(group_dict.keys())[0] in 'GroupLayer']
                for group_dict in reversed(list_of_groups):
                    long_name = group_dict.get('GroupLayer').get('longName')
                    if long_name == layer.longName.strip(f'{layer.name}').strip('\\'):
                        temp_dict['supergroup_id'] = group_dict.get('GroupLayer').get('id')
                        break
            self._current_dict[type_of_layer] = temp_dict

    def _get_layers_from_map_and_update_aprx_properties(self) -> None:
        for arcgis_map, aprx_property in zip(self.arcgis_maps, self.aprx_properties):
            layers_from_map = []
            list_layers = arcgis_map.listLayers()
            counter = -1
            self._current_dict = {}
            for layer in list_layers:
                # print(layer.name)
                counter += 1
                type_of_layer = self._get_type_of_layer(layer)
                self._current_dict = {}
                dict_type_of_layer = self.dict_properties_for_layers.get(type_of_layer)
                if all((type_of_layer == 'WMS', '\\' in layer.longName, not hasattr(layer, 'dataSource'))):
                    layers_from_map[-1].get(type_of_layer)['name'] = layer.name
                    continue
                if all((type_of_layer == 'WMS', '\\' in layer.longName, hasattr(layer, 'dataSource'),
                        layers_from_map)):
                    if layers_from_map[-1].get(type_of_layer):
                        layers_from_map[-1].get(type_of_layer)['name'] = layer.name
                        continue
                # if layer.isGroupLayer and '\\' in layer.longName:
                #     self._update_dict(layer, type_of_layer, dict_type_of_layer, layers_from_map)
                #     layers_from_map.append(self._current_dict)
                #     # eval_str = f'layers_from_map[-1]'
                #     # for counter in range(layer.longName.count('\\')):
                #     #     eval_str = f'''list({eval_str}.values())[0].get('subgroups')'''
                #     # proper_dict = eval(eval_str)
                #     # proper_dict.update(self._current_dict)
                #     continue
                # if layer.isGroupLayer:
                #     self._update_dict(layer, type_of_layer, dict_type_of_layer, layers_from_map)
                #     layers_from_map.append(self._current_dict)
                #     continue
                # if '\\' in layer.longName and not layer.isGroupLayer:
                #     self._update_dict(layer, type_of_layer, dict_type_of_layer, layers_from_map)
                #     layers_from_map.append(self._current_dict)
                #     # eval_str = f'layers_from_map[-1]'
                #     # for counter in range(layer.longName.count('\\') - 1):
                #     #     eval_str = f'''list({eval_str}.values())[0].get('subgroups')'''
                #     # eval_str = f'''list({eval_str}.values())[0].get('layers')'''
                #     # proper_dict = eval(eval_str)
                #     # proper_dict.update(self._current_dict)
                #     continue
                self._update_dict(layer, type_of_layer, dict_type_of_layer, layers_from_map)
                layers_from_map.append(self._current_dict)
            self.aprx_properties[aprx_property]['map_layers'] = layers_from_map

    def _dump_aprx_properties_to_json(self, json_path):
        with open(json_path, 'w') as write_file:
            json.dump(self.aprx_properties, write_file)


def main():
    AprxProject()


if __name__ == '__main__':
    main()
