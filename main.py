from ast import literal_eval
from typing import List, Dict, Any

import arcpy
import json

from arcgis.apps.storymap import Map

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
            'visible': 'layer.visible'
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

    def set_group_name(self, group_name, layer, type_of_layer, dict_type_of_layer, layers_from_map, layer_iter):
        if layer.isGroupLayer:
            group_name = layer.longName
            type_of_layer = self._get_type_of_layer(layer)
            dict_type_of_layer = self.dict_properties_for_layers.get(type_of_layer)
            if dict_type_of_layer:
                layers_from_map.append({type_of_layer: {
                    'name': eval(dict_type_of_layer.get('name')),
                    'transparency': eval(dict_type_of_layer.get('transparency')),
                    'visible': eval(dict_type_of_layer.get('visible')),
                    'layers': {}
                }})
            # layer_iter += 1
            return group_name, type_of_layer, dict_type_of_layer, layers_from_map, layer_iter
        elif group_name and group_name in layer.longName.split('\\')[0]:
            group_name = layer.longName.split('\\')[0]
        else:
            group_name = ''
        return group_name, type_of_layer, dict_type_of_layer, layers_from_map, layer_iter

    def _update_aprx_properties(self, type_of_layer, group_name, layer, layers_from_map, layer_iter, list_layers):
        dict_type_of_layer = self.dict_properties_for_layers.get(type_of_layer)
        group_name, type_of_layer, dict_type_of_layer, layers_from_map, layer_iter = \
            self.set_group_name(group_name, layer, type_of_layer, dict_type_of_layer, layers_from_map,
                                layer_iter)
        if layer.isGroupLayer or not layers_from_map:
            layer_iter += 1
            # print(layer_iter, '126')
            return type_of_layer, group_name, layer, layers_from_map, layer_iter
        proper_dict_to_set = f'''layers_from_map.append'''
        if 'GroupLayer' in layers_from_map[-1].keys() and \
                group_name == layers_from_map[-1].get('GroupLayer').get('name'):
            proper_dict_to_set = f'''list(layers_from_map[-1].values())[-1].get('layers').update'''
        dict1 = {}
        if dict_type_of_layer:
            for key, value in dict_type_of_layer.items():
                dict1[key] = eval(value)
            if type_of_layer == 'WMS':
                layer_iter += 1
                # print(layer_iter, '139')
                layer = list_layers[layer_iter]
                dict1.update({'name': layer.name})
                print(layer_iter)
                print(layer.name)
            eval(proper_dict_to_set)({type_of_layer: dict1})
        layer_iter += 1
        # print(layer_iter, '146')
        return type_of_layer, group_name, layer, layers_from_map, layer_iter

    def _get_type_of_layer(self, layer):
        cim_type_of_layer = layer.getDefinition('V3').__str__().split('.CIM')[-1].split()[0]
        type_of_layer = self.dict_types_of_layers.get(cim_type_of_layer)
        if isinstance(type_of_layer, tuple):
            type_of_layer = layer.connectionProperties.get('workspace_factory')
        return type_of_layer

    def _get_layers_from_map_and_update_aprx_properties(self) -> None:
        for arcgis_map, aprx_property in zip(self.arcgis_maps, self.aprx_properties):
            layers_from_map = []
            list_layers = arcgis_map.listLayers()
            layer_iter = 0
            group_name = ''
            while layer_iter < len(list_layers):
                layer = list_layers[layer_iter]
                type_of_layer = self._get_type_of_layer(layer)
                # print(layer, type_of_layer)
                # if hasattr(list_layers[layer_iter + 2], 'dataSource'):
                #     print(layer_iter)
                #     print(list_layers[layer_iter + 2].dataSource)
                if (len(list_layers) > layer_iter + 2 and not any((layer.isBasemapLayer, layer.isFeatureLayer,
                                                                   layer.isNetworkAnalystLayer,
                                                                   layer.isNetworkDatasetLayer,
                                                                   layer.isRasterLayer,
                                                                   layer.isSceneLayer))
                        and not hasattr(list_layers[layer_iter + 2], 'dataSource')):
                    # print('tutaj')
                    layer_iter += 2
                    continue
                type_of_layer, group_name, layer, layers_from_map, layer_iter = \
                    self._update_aprx_properties(type_of_layer, group_name, layer, layers_from_map, layer_iter,
                                                 list_layers)
                # print(layer_iter, '181')
                continue

            self.aprx_properties[aprx_property]['map_layers'] = layers_from_map

    def _dump_aprx_properties_to_json(self, json_path):
        with open(json_path, 'w') as write_file:
            json.dump(self.aprx_properties, write_file)


def main():
    AprxProject()


if __name__ == '__main__':
    main()
