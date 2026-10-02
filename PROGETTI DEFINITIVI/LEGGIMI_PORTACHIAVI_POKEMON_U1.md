# Portachiavi e Supporto Telefono Pokémon — Snapmaker U1

Progetto ottimizzato e riconfigurato per **Snapmaker U1** a **4 colori** (da 5 originali).

## File di Progetto
- File: `portachiaviPOKEMON_U1.3mf`
- Posizione: `PROGETTI DEFINITIVI/`
- Profilo Macchina: **Snapmaker U1 (0.4 nozzle)**
- Profilo Materiale: **Snapmaker PLA SnapSpeed @U1** (4 filamenti)
- Piatto: **PEI testurizzato** (Textured PEI Plate)

---

## Modifica Colori (da 5 a 4 colori)
Nel file originale erano richiesti 5 colori con la base della targhetta "Pokémon" in blu.
Come richiesto, la **parte blu è stata sostituita con il nero**.

### Palette Assegnata alle Testine U1:
| Testina | Colore | Codice HEX | Descrizione Componenti |
| :---: | :---: | :---: | :--- |
| **T1** | Rosso | `#FF0000` | Calotta superiore Pokeball (Piatto 1) |
| **T2** | Bianco | `#FFFFFF` | Calotta inferiore e centro Pokeball (Piatto 1) |
| **T3** | Nero | `#000000` | Fascia centrale/bordo Pokeball (Piatto 1) + **Base/contorno targhetta Pokémon** (Piatto 2) |
| **T4** | Giallo | `#FCD04B` | **Scritta/lettere a rilievo Pokémon** (Piatto 2) |

---

## Organizzazione dei Piatti di Stampa

### Piatto 1: Corpo Portachiavi / Supporto Telefono (`1.stl`)
- **Dimensioni:** ~29.8 × 89.8 × 13.0 mm
- **Caratteristica:** Meccanismo print-in-place con ruota girevole di supporto e foro portachiavi Ø 3.5 mm.
- **Colori utilizzati:** T1 (Rosso), T2 (Bianco), T3 (Nero)
- **Cambi colore a strati (`custom_gcode_per_layer`):**
  - $Z = 0.0 \to 3.8\text{ mm}$: T2 (Bianco)
  - $Z = 3.8 \to 7.6\text{ mm}$: T3 (Nero)
  - $Z = 7.6 \to 11.4\text{ mm}$: T1 (Rosso)
  - $Z = 11.4 \to 12.0\text{ mm}$: T3 (Nero)
  - $Z = 12.0 \to 12.6\text{ mm}$: T2 (Bianco)
  - $Z = 12.6 \to 13.0\text{ mm}$: T1 (Rosso)

### Piatto 2: Targhetta Logo Pokémon (`2.stl`)
- **Dimensioni:** ~44.0 × 16.1 × 1.2 mm
- **Caratteristica:** Targhetta a rilievo da inserire/incollare sul retro o nell'alloggiamento.
- **Colori utilizzati:** T3 (Nero), T4 (Giallo)
- **Cambi colore a strati (`custom_gcode_per_layer`):**
  - $Z = 0.0 \to 0.8\text{ mm}$: **T3 (Nero)** *(in origine Blu)*
  - $Z = 0.8 \to 1.2\text{ mm}$: **T4 (Giallo)**

---

## Verifica Magneti
- **Esito:** Il modello **non utilizza magneti**.
- Il supporto telefono sfrutta un perno a scatto/frizione print-in-place ("ruedita") e il foro presente è esclusivamente per l'anello portachiavi (Ø 3,5 mm).

---

## Istruzioni per la Stampa su Snapmaker Orca
1. Aprire **`portachiaviPOKEMON_U1.3mf`** direttamente in **Snapmaker Orca**.
2. Verificare che le 4 bobine siano caricate sulle testine T1 (Rosso), T2 (Bianco), T3 (Nero) e T4 (Giallo).
3. Eseguire lo slicing del Piatto 1 e del Piatto 2.
4. Dopo la stampa di Piatto 1, sbloccare delicatamente la rotella centrale premendola leggermente con il pollice per liberare il meccanismo print-in-place.
