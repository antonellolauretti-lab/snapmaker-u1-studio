from pathlib import Path
import zipfile,json,subprocess,time
root=Path(__file__).resolve().parent
dest=root.parent/'PROGETTI DEFINITIVI/BUMPER TCG ENERGIE 6mm'
project=dest/'4 BUMPER TCG ENERGIE 6mm - QUALITA 0.12.3mf'
work=root/'energy_slice'; work.mkdir(exist_ok=True)
profiles=Path('C:/Program Files/Snapmaker_Orca/resources/profiles/Snapmaker/filament')
def filament(name):
 d=json.loads((profiles/(name+'.json')).read_text(encoding='utf-8-sig'))
 b=filament(d['inherits']) if d.get('inherits') else {}; b.update(d); return b
material=filament('Snapmaker PLA SnapSpeed @U1')
with zipfile.ZipFile(project) as z:
 contents={n:z.read(n) for n in z.namelist()}
cfg=json.loads(contents['Metadata/project_settings.config'])
old=dict(cfg)
exclude={'type','from','instantiation','name','setting_id','inherits','compatible_printers','compatible_prints','compatible_printers_condition','compatible_prints_condition','filament_id','description','version','default_filament_colour'}
for k,v in material.items():
 if k not in exclude: cfg[k]=v*4 if isinstance(v,list) and len(v)==1 else v
# Retain the conservative flow cap of the quality profile.
cfg['filament_max_volumetric_speed']=old['filament_max_volumetric_speed']
cfg['filament_settings_id']=['Snapmaker PLA SnapSpeed @U1']*4
cfg['filament_preset']=['Snapmaker PLA SnapSpeed @U1']*4
cfg['prime_tower_width']='36'
cfg['prime_tower_brim_width']='3'
cfg['wipe_tower_x']=['117']
cfg['wipe_tower_y']=['116']
for k in ['filament_colour','extruder_colour']: cfg[k]=old[k]
for k in ['layer_height','initial_layer_print_height','outer_wall_speed','top_surface_speed','top_shell_thickness','bottom_shell_thickness','xy_contour_compensation','xy_hole_compensation']: assert cfg[k]==old[k]
contents['Metadata/project_settings.config']=json.dumps(cfg,ensure_ascii=False,indent=2).encode()
tmp=work/'material_updated.3mf'
with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED) as z:
 for n,data in contents.items(): z.writestr(n,data)
with zipfile.ZipFile(tmp) as z: assert z.testzip() is None
project.write_bytes(tmp.read_bytes())
portable=root.parent/'Verifica_batch_U1/OrcaSlicer_portable'
def machine(name):
 d=json.loads((portable/'resources/profiles/Snapmaker/machine'/(name+'.json')).read_text(encoding='utf-8-sig'))
 b=machine(d['inherits']) if d.get('inherits') else {}; b.update(d); return b
mc=machine('Snapmaker U1 (0.4 nozzle)'); control=dict(cfg)
# The portable Orca validator requires its own machine macros. Never deliver this control copy.
for k in control:
 if 'gcode' in k and k!='gcode_flavor': control[k]=mc.get(k,['']*4 if isinstance(control[k],list) else '')
control['tree_support_wall_count']=str(max(0,int(control.get('tree_support_wall_count','1'))))
contents['Metadata/project_settings.config']=json.dumps(control).encode()
checkfile=work/'controllo.3mf'
with zipfile.ZipFile(checkfile,'w',zipfile.ZIP_DEFLATED) as z:
 for n,data in contents.items(): z.writestr(n,data)
args=[str(portable/'orca-slicer.exe'),'--debug','2','--allow-newer-file','--outputdir',str(work),'--slice','0','--export-3mf','controllo_sliced.3mf',str(checkfile)]
print('SLICING',flush=True); start=time.time()
with (work/'console.log').open('wb') as log:
 p=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=240,creationflags=subprocess.CREATE_NO_WINDOW)
print('SLICE EXIT',p.returncode,'SECONDS',round(time.time()-start,1),flush=True)
print((work/'console.log').read_text(errors='replace')[-5000:],flush=True)
(work/'execution.json').write_text(json.dumps({'exit_code':p.returncode,'seconds':time.time()-start,'files':[q.name for q in work.iterdir()]},indent=2))
