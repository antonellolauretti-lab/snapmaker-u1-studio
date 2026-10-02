from pathlib import Path
import zipfile, json, hashlib, xml.etree.ElementTree as E

folder=Path(__file__).resolve().parent.parent/'PROGETTI DEFINITIVI/BUMPER TCG DESIGN 6mm'
src=folder/'4 BUMPER TCG DESIGN 6mm.3mf'
dst=folder/'4 BUMPER TCG DESIGN 6mm - QUALITA 0.12.3mf'
assert not dst.exists(), 'Destination already exists'
original_hash=hashlib.sha256(src.read_bytes()).hexdigest()
changes={
 'layer_height':'0.12',
 'initial_layer_print_height':'0.25',
 'outer_wall_speed':'60',
 'top_surface_speed':'40',
 'top_shell_thickness':'1',
 'bottom_shell_thickness':'0.6',
 'ironing_type':'no ironing',
 'sparse_infill_density':'15%',
 'xy_contour_compensation':'0',
 'xy_hole_compensation':'0',
 'print_settings_id':'BUMPER DESIGN - Qualita 0.12 @Snapmaker U1 (0.4 nozzle)',
}
with zipfile.ZipFile(src) as z:
 original=json.loads(z.read('Metadata/project_settings.config'))
 cfg=dict(original); cfg.update(changes)
 assert int(cfg['top_shell_layers'])>0 and int(cfg['bottom_shell_layers'])>0
 model_settings=E.fromstring(z.read('Metadata/model_settings.config'))
 assert not any(p.get('key') in changes for p in model_settings.findall('.//metadata')),'Unexpected object-level override'
 with zipfile.ZipFile(dst,'w',zipfile.ZIP_DEFLATED) as out:
  for entry in z.infolist():
   data=z.read(entry.filename)
   if entry.filename=='Metadata/project_settings.config':
    data=json.dumps(cfg,ensure_ascii=False,indent=2).encode('utf-8')
   out.writestr(entry,data)
with zipfile.ZipFile(src) as a,zipfile.ZipFile(dst) as b:
 assert b.testzip() is None
 assert a.namelist()==b.namelist()
 for name in a.namelist():
  if name!='Metadata/project_settings.config': assert a.read(name)==b.read(name),name
 saved=json.loads(b.read('Metadata/project_settings.config'))
 assert all(saved[k]==v for k,v in changes.items())
 assert all(saved[k]==v for k,v in original.items() if k not in changes)
assert hashlib.sha256(src.read_bytes()).hexdigest()==original_hash
report={'file':dst.name,'changes':{k:{'before':original.get(k),'after':v} for k,v in changes.items() if original.get(k)!=v},'geometry_colors_placement_unchanged':True,'other_settings_unchanged':True,'source_sha256':original_hash,'zip_verified':True,'slicing_performed':False}
(folder/'VERIFICA_QUALITA_012.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
(folder/'LEGGIMI_QUALITA_012.txt').write_text('BUMPER DESIGN - QUALITA 0.12\n\nAprire 4 BUMPER TCG DESIGN 6mm - QUALITA 0.12.3mf come progetto in Snapmaker Orca.\nAltezza strato: 0,12 mm; primo strato: 0,25 mm.\nParete esterna: 60 mm/s; superficie superiore: 40 mm/s.\nSpessore guscio superiore: 1 mm; inferiore: 0,6 mm.\nConteggi minimi gusci conservati: superiore 5, inferiore 3; lo spessore minimo richiede ulteriori strati quando necessario.\nStiratura disattivata, riempimento 15%, compensazioni XY contorno e fori a zero.\nGeometrie, incastro, bordo 6 mm, colori e disposizione identici al progetto di partenza.\nTutte le altre impostazioni conservate.\nVerificato il contenuto del 3MF dopo il salvataggio; slicing non eseguito.\nAffettare e controllare l\'anteprima prima della stampa.\n',encoding='utf-8')
print(json.dumps(report,indent=2))
