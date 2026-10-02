import os
import json
import zipfile
import uuid
from dataclasses import dataclass
from typing import List, Optional
import trimesh

@dataclass
class PartItem:
    name: str
    mesh: trimesh.Trimesh
    extruder: int  # 0=T0, 1=T1, 2=T2, 3=T3

class Snapmaker3MFPackager:
    """
    Compilatore modulare per pacchetti .3MF compatibili con Snapmaker Orca / Snapmaker U1.
    Accetta un insieme arbitrario di mesh e genera un progetto multi-volume pronto per la stampa.
    """
    def __init__(
        self,
        project_name: str = "Snapmaker_Model",
        machine_name: str = "Snapmaker U1 (0.4 nozzle)",
        process_name: str = "0.20 Standard @Snapmaker U1 (0.4 nozzle)",
        bed_type: str = "Textured PEI Plate",
        filament_colors: Optional[List[str]] = None,
        filament_types: Optional[List[str]] = None,
        filament_vendors: Optional[List[str]] = None,
        enable_prime_tower: bool = False,
        enable_support: bool = False,
        bed_center_x: float = 135.0,
        bed_center_y: float = 135.0,
    ):
        self.project_name = project_name
        self.machine_name = machine_name
        self.process_name = process_name
        self.bed_type = bed_type
        self.filament_colors = filament_colors or ["#000000", "#FFFFFF", "#E31B23", "#FFD700"]
        self.filament_types = filament_types or ["PLA", "PLA", "PLA", "PLA"]
        self.filament_vendors = filament_vendors or ["Snapmaker", "Snapmaker", "Snapmaker", "Snapmaker"]
        self.enable_prime_tower = enable_prime_tower
        self.enable_support = enable_support
        self.bed_center_x = bed_center_x
        self.bed_center_y = bed_center_y

    def _mesh_to_3mf_object_xml(self, mesh: trimesh.Trimesh, obj_id: int, obj_uuid: str) -> str:
        v_lines = [f'     <vertex x="{v[0]:.6f}" y="{v[1]:.6f}" z="{v[2]:.6f}"/>' for v in mesh.vertices]
        f_lines = [f'     <triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}"/>' for f in mesh.faces]
        vertices_xml = "\n".join(v_lines)
        triangles_xml = "\n".join(f_lines)
        return f"""  <object id="{obj_id}" p:UUID="{obj_uuid}" type="model">
   <mesh>
    <vertices>
{vertices_xml}
    </vertices>
    <triangles>
{triangles_xml}
    </triangles>
   </mesh>
  </object>"""

    def export(self, parts: List[PartItem], output_path: str, reference_config_path: Optional[str] = None):
        """
        Compila l'archivio .3MF unificando tutte le parti in un singolo oggetto multi-volume.
        """
        container_obj_id = len(parts) + 1
        model_uuid = str(uuid.uuid4())
        container_uuid = str(uuid.uuid4())
        build_item_uuid = str(uuid.uuid4())

        # 1. Oggetti mesh in 3D/Objects/model_parts.model
        part_uuids = [str(uuid.uuid4()) for _ in parts]
        objects_xml_list = []
        for idx, (part, p_uuid) in enumerate(zip(parts, part_uuids), start=1):
            objects_xml_list.append(self._mesh_to_3mf_object_xml(part.mesh, obj_id=idx, obj_uuid=p_uuid))
        
        objects_model_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <resources>
{"\n".join(objects_xml_list)}
 </resources>
</model>"""

        # 2. Struttura assemblaggio in 3D/3dmodel.model
        components_xml = []
        for idx, p_uuid in enumerate(part_uuids, start=1):
            components_xml.append(
                f'    <component p:path="/3D/Objects/model_parts.model" objectid="{idx}" p:UUID="{p_uuid}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
            )

        d3model_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">
 <metadata name="Application">Snapmaker_Orca-2.4.0</metadata>
 <metadata name="BambuStudio:3mfVersion">1</metadata>
 <metadata name="Title">{self.project_name}</metadata>
 <resources>
  <object id="{container_obj_id}" p:UUID="{container_uuid}" type="model">
   <components>
{"\n".join(components_xml)}
   </components>
  </object>
 </resources>
 <build p:UUID="{model_uuid}">
  <item objectid="{container_obj_id}" p:UUID="{build_item_uuid}" transform="1 0 0 0 1 0 0 0 1 {self.bed_center_x:.6f} {self.bed_center_y:.6f} 0" printable="1"/>
 </build>
</model>"""

        # 3. Mappatura parti/estrusori in Metadata/model_settings.config
        parts_settings_xml = []
        for idx, part in enumerate(parts, start=1):
            # Nota: OrcaSlicer usa 1-based index per la UI (1 = T0, 2 = T1, etc.)
            extruder_val = part.extruder + 1
            parts_settings_xml.append(f"""    <part id="{idx}" subtype="normal_part">
      <metadata key="name" value="{part.name}"/>
      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>
      <metadata key="source_object_id" value="0"/>
      <metadata key="source_volume_id" value="0"/>
      <metadata key="extruder" value="{extruder_val}"/>
      <mesh_stat edges_fixed="0" degenerate_facets="0" facets_removed="0" facets_reversed="0" backwards_edges="0"/>
    </part>""")

        model_settings_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<config>
  <object id="{container_obj_id}">
    <metadata key="name" value="{self.project_name}"/>
    <metadata key="extruder" value="{parts[0].extruder + 1}"/>
{"\n".join(parts_settings_xml)}
  </object>
  <plate>
    <metadata key="plater_id" value="1"/>
    <metadata key="plater_name" value=""/>
    <metadata key="locked" value="false"/>
    <metadata key="filament_map_mode" value="Auto For Flush"/>
    <metadata key="filament_maps" value="1 1 1 1"/>
    <model_instance>
      <metadata key="object_id" value="{container_obj_id}"/>
      <metadata key="instance_id" value="0"/>
      <metadata key="identify_id" value="101"/>
    </model_instance>
  </plate>
  <assemble>
   <assemble_item object_id="{container_obj_id}" instance_id="0" transform="1 0 0 0 1 0 0 0 1 0 0 0" offset="0 0 0"/>
  </assemble>
</config>"""

        # 4. Impostazioni di stampa in Metadata/project_settings.config
        project_cfg = {}
        if reference_config_path and os.path.exists(reference_config_path):
            try:
                if reference_config_path.lower().endswith(".3mf"):
                    with zipfile.ZipFile(reference_config_path, "r") as rz:
                        if "Metadata/project_settings.config" in rz.namelist():
                            project_cfg = json.loads(rz.read("Metadata/project_settings.config").decode("utf-8"))
                else:
                    with open(reference_config_path, "r", encoding="utf-8") as f:
                        project_cfg = json.load(f)
            except Exception as e:
                print(f"Warning: Caricamento reference config fallito ({e}), uso default.")

        # Sanitizza machine_start_gcode per compatibilità tra versioni Orca/Snapmaker
        if "machine_start_gcode" in project_cfg:
            gcode = project_cfg["machine_start_gcode"]
            if "chamber_cooling_mode" in gcode:
                # Ripristina start gcode standard U1 senza macro non riconosciute dai parser CLI
                u1_profile_path = r"C:\Users\AirGT\Desktop\STAMPE 3D IA\Verifica_batch_U1\OrcaSlicer_portable\resources\profiles\Snapmaker\machine\Snapmaker U1 (0.4 nozzle).json"
                if os.path.exists(u1_profile_path):
                    try:
                        with open(u1_profile_path, "r", encoding="utf-8") as pf:
                            p_data = json.load(pf)
                            if "machine_start_gcode" in p_data:
                                project_cfg["machine_start_gcode"] = p_data["machine_start_gcode"]
                    except Exception:
                        pass

        project_cfg["printer_settings_id"] = self.machine_name
        project_cfg["print_settings_id"] = self.process_name
        project_cfg["curr_bed_type"] = self.bed_type
        project_cfg["filament_colour"] = self.filament_colors
        project_cfg["default_filament_colour"] = self.filament_colors
        project_cfg["filament_type"] = self.filament_types
        project_cfg["filament_vendor"] = self.filament_vendors
        project_cfg["filament_settings_id"] = [f"Snapmaker PLA" for _ in range(4)]
        project_cfg["enable_prime_tower"] = "1" if self.enable_prime_tower else "0"
        project_cfg["enable_support"] = "1" if self.enable_support else "0"

        # 5. File di relazione e types
        content_types = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
 <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
 <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>
 <Default Extension="config" ContentType="application/xml"/>
 <Default Extension="json" ContentType="application/json"/>
</Types>"""

        root_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/3dmodel.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""

        d3model_rels = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
 <Relationship Target="/3D/Objects/model_parts.model" Id="rel-1" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>
</Relationships>"""

        slice_info = """<?xml version="1.0" encoding="UTF-8"?>
<config>
  <header>
    <header_item key="X-BBL-Client-Type" value="snorca"/>
    <header_item key="X-BBL-Client-Version" value="02.04.00.00"/>
  </header>
</config>"""

        # 6. Scrittura archivio compresso ZIP
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", content_types)
            z.writestr("_rels/.rels", root_rels)
            z.writestr("3D/3dmodel.model", d3model_content)
            z.writestr("3D/_rels/3dmodel.model.rels", d3model_rels)
            z.writestr("3D/Objects/model_parts.model", objects_model_content)
            z.writestr("Metadata/model_settings.config", model_settings_content)
            z.writestr("Metadata/project_settings.config", json.dumps(project_cfg, indent=4))
            z.writestr("Metadata/slice_info.config", slice_info)

        return output_path
