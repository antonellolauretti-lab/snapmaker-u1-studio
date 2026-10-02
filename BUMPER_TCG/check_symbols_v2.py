from pathlib import Path
root=Path(__file__).resolve().parent
replacements={
 'BUMPER TCG ENERGIE 6mm':'BUMPER TCG ENERGIE SIMBOLI GRANDI',
 '4 BUMPER TCG ENERGIE 6mm - QUALITA 0.12.3mf':'4 BUMPER ENERGIE SIMBOLI GRANDI - QUALITA 0.12.3mf',
 'energy_slice':'symbols_v2_slice',
}
def adapt(text):
 # Longest key first: the complete filename contains the old folder label.
 for a,b in sorted(replacements.items(),key=lambda p:-len(p[0])):text=text.replace(a,b)
 return text
code=adapt((root/'verify_energy_slice.py').read_text())
exec(compile(code,str(root/'verify_energy_slice.py'),'exec'))
assert p.returncode==0
code=adapt((root/'finish_energy.py').read_text())
code=code.replace('corpo 91,9 x 147,2 x 7,5 mm. Altezza massima con rilievi 8,34 mm.','corpo 91,9 x 147,2 x 7,5 mm. Altezza massima con simbolo 9,3 mm. Simbolo alto 12,5 mm in vista frontale, sporgenza esterna 7,4 mm; nessuna basetta rettangolare aggiunta.')
code=code.replace("BUMPER TCG | ENERGIE | BORDO 6 mm","BUMPER TCG | SIMBOLI CENTRALI GRANDI")
exec(compile(code,str(root/'finish_energy.py'),'exec'))
