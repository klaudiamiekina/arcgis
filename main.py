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
            'visible': 'layer.visible'
        },
        'Shape File': {
            'source': 'layer.dataSource',
            'name': 'layer.name',
            'crs': 'arcpy.Describe(layer).spatialReference.PCSCode',
            'transparency': 'layer.transparency',
            'visible': 'layer.visible'
        },
        'Raster': {
            'source': 'layer.dataSource',
            'name': 'layer.name',
            'crs': 'arcpy.Describe(layer).spatialReference.PCSCode',
            'transparency': 'layer.transparency',
            'visible': 'layer.visible'
        },
        'WMS': {
            'source': 'layer.dataSource',
            'name': 'layer.name',
            'crs': 'self.aprx_properties.get(self._arcgis_map_name).get("map_crs")',
            'transparency': 'layer.transparency',
            'visible': 'layer.visible'
        },
        'WMTS': {
            'source': 'layer.dataSource',
            'name': 'layer.name',
            'crs': 'self.aprx_properties.get(self._arcgis_map_name).get("map_crs")',
            'transparency': 'layer.transparency',
            'visible': 'layer.visible'
        },
        'GroupLayer': {
            'name': 'layer.longName',
            'transparency': 'layer.transparency',
            'visible': 'layer.visible',
            'layers': '{}',
            'subgroups': '{}'
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
        type_of_layer = self.dict_types_of_layers.get(cim_type_of_layer)
        if isinstance(type_of_layer, tuple):
            type_of_layer = layer.connectionProperties.get('workspace_factory')
        return type_of_layer

    def _get_layers_from_map_and_update_aprx_properties(self) -> None:
        for arcgis_map, aprx_property in zip(self.arcgis_maps, self.aprx_properties):
            layers_from_map = []
            list_layers = arcgis_map.listLayers()
            counter = -1
            self._current_dict = {}
            for layer in list_layers:
                counter += 1
                type_of_layer = self._get_type_of_layer(layer)
                self._current_dict = {}
                dict_type_of_layer = self.dict_properties_for_layers.get(type_of_layer)
                if all((type_of_layer == 'WMS', '\\' in layer.longName, not hasattr(layer, 'dataSource'))):
                    layers_from_map[-1].get(type_of_layer)['name'] = layer.name
                    continue
                if layer.isGroupLayer and '\\' in layer.longName:
                    temp_dict = {}
                    if dict_type_of_layer:
                        for key, value in dict_type_of_layer.items():
                            temp_dict[key] = eval(value)
                        self._current_dict[type_of_layer] = temp_dict
                        eval_str = f'layers_from_map[-1]'
                        for counter in range(layer.longName.count('\\')):
                            eval_str = f'''list({eval_str}.values())[0].get('subgroups')'''
                        proper_dict = eval(eval_str)
                        proper_dict.update(self._current_dict)
                        continue
                if '\\' in layer.longName and not layer.isGroupLayer:
                    temp_dict = {}
                    if dict_type_of_layer:
                        for key, value in dict_type_of_layer.items():
                            temp_dict[key] = eval(value)
                        self._current_dict[type_of_layer] = temp_dict
                        eval_str = f'layers_from_map[-1]'
                        for counter in range(layer.longName.count('\\') - 1):
                            eval_str = f'''list({eval_str}.values())[0].get('subgroups')'''
                        eval_str = f'''list({eval_str}.values())[0].get('layers')'''
                        proper_dict = eval(eval_str)
                        proper_dict.update(self._current_dict)
                        continue
                temp_dict = {}
                if dict_type_of_layer:
                    for key, value in dict_type_of_layer.items():
                        temp_dict[key] = eval(value)
                    self._current_dict[type_of_layer] = temp_dict
                    layers_from_map.append(self._current_dict)
            self.aprx_properties[aprx_property]['map_layers'] = layers_from_map

    def _dump_aprx_properties_to_json(self, json_path):
        with open(json_path, 'w') as write_file:
            json.dump(self.aprx_properties, write_file)


def main():
    AprxProject()


if __name__ == '__main__':
    main()
