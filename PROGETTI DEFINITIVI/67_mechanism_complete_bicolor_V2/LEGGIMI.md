# 67 Tiny Hands Fidget (Push to Wave) — Snapmaker U1

Progetto ottimizzato e verificato per **Snapmaker U1** con profilo **PLA SnapSpeed**, quattro ugelli da **0,4 mm** e **piatto PEI testurizzato**.

## Configurazione Bobine Utente

- **Slot 1**: — (Non utilizzato)
- **Slot 2**: **Bianco** (`#FFFFFF`) — Usato per il Piatto 1 (Scocca e Coperchio)
- **Slot 3**: **Rosso** (`#FF0000`) — Usato per il Piatto 2 (Meccanismo interno e Manine)
- **Slot 4**: — (Non utilizzato)

## Tabella piatti e tempi di stampa

| Piatto / File | Componenti inclusi | Layer mm | Slot 1 | Slot 2 (Bianco) | Slot 3 (Rosso) | Slot 4 | Tempo stimato | PLA g | Torre spurgo | Brim |
|---|---|---:|---|---|---|---|---:|---:|---:|---|
| [P1 BIANCO](67_mechanism_U1_P1_BIANCO.3mf) | Housing + Cover | 0,16 mm | — | **Bianco** (#FFFFFF) | — | — | 51m 59s | 13.86 g | NO (0 g) | No (base ampia) |
| [P2 ROSSO](67_mechanism_U1_P2_ROSSO.3mf) | Molla, Leva, Bielletta, 2 Mani | 0,16 mm | — | — | **Rosso** (#FF0000) | — | 34m 42s | 5.93 g | NO (0 g) | **Selettivo** (8 mm mani, 5 mm connettore, 0 mm molla) |
| **TOTALE** | *Modello completo (7 pezzi)* | *0,16 mm* | — | — | — | — | **~1h 26m** | **19.79 g** | **0,00 g** | Massima sicurezza di adesione |

## Diagnosi del problema di stampa e Soluzione Adottata

### Causa del fallimento precedente (Piatto Rosso)
1. **Perno di base minuscolo**: Le due manine hanno alla base un perno cilindrico di soli **Ø 3,5 mm** (area di contatto sul piatto di appena ~9,6 mm²), ma si sviluppano in altezza per **20,62 mm** allargandosi verso l'alto (fino a 12,2 mm di larghezza delle dita).
2. **Effetto leva e distacco**: Senza brim sul piatto PEI testurizzato, raggiunti gli 8–12 mm di altezza, la forza laterale esercitata dall'ugello e il baricentro sbilanciato hanno fatto staccare le manine dal piatto.
3. **Effetto a catena (spaghetti)**: Le manine staccate sono state trascinate dall'ugello, generando filamenti aggrovigliati che hanno urtato il connettore (spezzandone il perno) e impigliato la molla.
4. **Perché l'auto-brim generale non funzionava**: Poiché tutti i pezzi rossi erano raggruppati in un unico assieme ("Zusammenbau"), lo slicer vedeva la grande superficie d'appoggio della molla e della leva e disabilitava automaticamente il brim. Inoltre, abilitare un brim globale avrebbe fuso e saldato insieme le spire della molla a serpentina (lo spazio tra le spire è di soli 2-3 mm), rovinando l'elasticità della molla.

### Soluzione Implementata
- **Separazione dei componenti in oggetti indipendenti**:
  - **Manine (Hand e Left Hand)**: Configurato un **Brim esterno da 8 mm** (gap 0,1 mm), che espande l'area di contatto a terra da Ø3,5 mm a quasi Ø20 mm (oltre 20 volte la superficie d'adesione), rendendole perfettamente stabili e impossibili da scalzare.
  - **Connettore (Connector)**: Configurato un **Brim esterno da 5 mm** (gap 0,1 mm) per ancorare saldamente il piccolo snodo.
  - **Molla a serpentina (Spring)**: Configurato **`no_brim`** (0 mm). Le spire rimangono libere e pulite al 100%, garantendo la perfetta funzionalità del meccanismo a molla.
  - **Leva (Lever)**: Configurato **`no_brim`** (0 mm), avendo già una base piatta di 40×18 mm con adesione naturale perfetta.
- Il brim da 8 mm si rimuove con estrema facilità a mano o con una tronchesina grazie al gap di distacco di 0,1 mm.

## Strategia di stampa a ZERO SPRECO

- **Piatto 1 (Bianco - Slot 2)**: 100% monocolore, **0 cambi filamento**, **0 torre di spurgo**.
- **Piatto 2 (Rosso - Slot 3)**: 100% monocolore, **0 cambi filamento**, **0 torre di spurgo**.
- **Progetto Unificato**: Il file `67_mechanism_U1_2PIATTI_COMPLETO.3mf` contiene entrambi i piatti già abbinati ai tuoi slot (Piatto 1 -> Slot 2, Piatto 2 -> Slot 3).
- **File Singolo Piatto 2**: Puoi anche stampare direttamente solo il file `67_mechanism_U1_P2_ROSSO.3mf` che contiene esclusivamente il piatto rosso già corretto con il brim selettivo.

## Verifica magneti

- **Controllo eseguito**: Analisi geometrica di tutte le cavità e riscontro con le istruzioni di montaggio originali.
- **Esito**: Il modello **non utilizza magneti**. Tutti i vincoli, le guide di scorrimento a T, il perno di fulcro e i 4 perni d'angolo di chiusura sono interamente integrati e stampati in 3D.

## Parametri di stampa configurati

- **Altezza strato**: 0,16 mm (primo strato 0,20 mm) per garantire scorrimenti fluidi della molla e incastri precisi dei perni senza attriti.
- **Pareti**: 3 perimetri (Wall loops: 3).
- **Riempimento**: 15% Gyroid.
- **Velocità**: Pareti esterne 40 mm/s, interne 80 mm/s, superfici superiori 30 mm/s.
- **Temperature**: Ugello 220 °C, piatto PEI testurizzato 65 °C.
- **Supporti**: Disattivati (tutte le geometrie sono auto-portanti).

## Guida al montaggio (dall'Assembly Guide originale)

Consultare anche il manuale illustrato [67_mechanism_Assembly_Instruction.pdf](67_mechanism_Assembly_Instruction.pdf) incluso nella cartella:
1. **Passo 1 (Molla)**: Inserire la molla a serpentina rossa (`Spring`) nella scocca bianca (`Housing`) facendola scorrere nelle guide a T inferiori.
2. **Passo 2 (Bielletta)**: Installare il piccolo connettore (`Connector`) sul perno quadrato della molla.
3. **Passo 3 (Leva)**: Posizionare la leva rossa (`Lever`) collegando il foro centrale sul perno di fulcro della scocca e l'asola sul perno di azionamento del connettore.
4. **Passo 4 (Coperchio)**: Chiudere la scocca posizionando il coperchio bianco (`Cover`) sui 4 perni d'angolo a pressione.
5. **Passo 5 (Mani)**: Inserire le due manine rosse attraverso le due asole arcuate del coperchio, innestandole sui rispettivi perni della leva interna.
6. **Passo 6**: Premere il pulsante superiore per far salutare le manine!
