# Toothless — Snapmaker U1

Aprire `Toothless_U1_QUALITA_008.3mf` **come progetto** in Snapmaker Orca.

## Statuetta senza incollaggio

La versione AMS fornita contiene già i componenti nella posizione assemblata. L'analisi ha individuato 26 gusci chiusi: corpo con ali e coda, artigli, inserti della coda e dettagli degli occhi. Sono state verificate intersezioni di volume positivo fra i gusci, non solo la loro appartenenza allo stesso oggetto dello slicer.

Le due pupille avevano un piccolo gioco rispetto agli occhi. Pupille e riflessi sono stati spostati insieme di 0,30 mm verso l'interno del viso. Dopo la correzione, tutti i 26 gusci risultano collegati al corpo attraverso intersezioni solide. I volumi sovrapposti vengono uniti durante lo slicing dello stesso oggetto.

Per evitare l'esaurimento della memoria dello slicer, la mesh è stata ridotta da 6.592.960 a 2.071.644 triangoli con una tolleranza di 0,005 mm. La pittura delle due superfici degli occhi è mantenuta esattamente; le superfici monocromatiche sono alleggerite. Tutte le 25 connessioni necessarie a collegare i 26 gusci sono state ricontrollate dopo la riduzione, con intersezioni di volume positivo. La versione corretta senza riduzione è conservata in `Verifica_Toothless/Toothless_U1_MESH_COMPLETA.3mf`.

Non usare “Separa in oggetti” o disporre automaticamente i singoli gusci: si perderebbe la posa assemblata. Restano da rimuovere i supporti e il brim dopo la stampa; non è previsto l'incollaggio dei dettagli.

## Materiali e colori

Configurazione ripresa dal precedente progetto U1: quattro ugelli da 0,4 mm, quattro PLA Snapmaker SnapSpeed e piatto PEI ruvido.

| Testina | Colore | Uso |
|---|---|---|
| 1 | Giallo | Occhi, al posto del verde |
| 2 | Rosso | Inserto della coda |
| 3 | Bianco | Artigli, riflessi, simbolo sulla coda |
| 4 | Nero | Corpo, pupille, resto della coda e supporti |

## Profilo di finitura

- Strati da 0,08 mm; primo strato da 0,16 mm.
- Parete esterna 30 mm/s, accelerazione 500 mm/s²; pareti interne 60 mm/s.
- Tre pareti, riempimento gyroid 15%, superfici superiori 25 mm/s.
- Percorsi con risoluzione 0,005 mm, generatore pareti Arachne, cucitura posteriore.
- Supporti ad albero organici, distanza Z 0,16 mm, tre strati di interfaccia superiore e distanza XY 0,30 mm.
- Brim esterno 5 mm, torre di adescamento attiva, cambi testina nativi U1.
- PLA SnapSpeed: ugelli 220 °C, piatto 65 °C. Nessun materiale di supporto diverso dal PLA installato.

Il profilo privilegia la finitura rispetto al tempo. La qualità effettiva, l'adesione dei dettagli e la rimozione dei supporti vanno controllate su una prima stampa completa prima di produrre una serie.

## Verifiche

Il dettaglio delle intersezioni è in `Verifica_Toothless/VERIFICA_GEOMETRIA.json`; la trasformazione delle colorazioni è documentata in `Verifica_Toothless/paint_remap.json`. Il file originale è conservato.
