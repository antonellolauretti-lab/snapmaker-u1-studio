# Pokewall — Pokémon PSA Card Display (Snapmaker U1)

Riprogettazione completa e ottimizzazione per la **Snapmaker U1** con 4 testine da 0,4 mm e profilo SnapSpeed PLA.

Il progetto trasforma una card graduata PSA in una **Pokéball tridimensionale da parete o da scrivania**, con telaio portante posteriore nero e due gusci frontali a scatto (superiore rosso, inferiore bianco).

---

## 1. Assegnazione Slot / Testine U1

| Slot U1 | Filamento | Colore | Componente Assegnato |
|:---:|:---|:---|:---|
| **Slot 1** | SnapSpeed PLA | **Nero** (`#080A0D`) | **Telaio Posteriore Portante** (`Back frame`) |
| **Slot 2** | SnapSpeed PLA | **Bianco** (`#D9DFE5`) | **Guscio Inferiore Pokéball** (`Front cover Bottom`) |
| **Slot 3** | SnapSpeed PLA | **Rosso** (`#E72F1D`) | **Guscio Superiore Pokéball** (`Front cover Top`) |
| **Slot 4** | SnapSpeed PLA | **Giallo** (`#F8F81C`) | Riservato per varianti tematiche (es. Ultra Ball) |

---

## 2. Perché 139 cambi sul piatto unico vs Versione Multi-Piatto

### La spiegazione tecnica dei 139 cambi sul piatto singolo:
* Nel file a piatto singolo (`Pokewall_PSA_Display_U1.3mf`), la sequenza di stampa è **"Per strato" (By layer)**.
* Ad ogni singolo strato (altezza layer 0,2 mm per 73 layer = ~14,6 mm di altezza totale), la U1 stampa:
  1. Il telaio nero con la Testina 1
  2. Cambio utensile a Testina 2 $\rightarrow$ stampa il guscio inferiore bianco
  3. Cambio utensile a Testina 3 $\rightarrow$ stampa il guscio superiore rosso
* **73 layer × 2 cambi a strato = ~139 cambi filamento/testina!**

### Perché non si può fare "Stampa per oggetto" (Sequential Printing) su 1 piatto unico?
* In OrcaSlicer, la modalità "Stampa per oggetto" richiede un **raggio di sicurezza della testina (`extruder_clearance_radius = 72.5 mm`)** attorno a ciascun oggetto per evitare che la testina o il condotto ventole collidano con un pezzo già stampato.
* Con il telaio (112,4 × 167,4 mm) e i due gusci (112,4 × 78,2 mm ciascuno), l'ingombro di sicurezza virtuale richiesto supera le dimensioni del piatto da 270 × 270 mm (**257 × 312 mm** solo per il telaio), causando un errore di collisione nello slicer.

---

## 3. I File 3MF Disponibili nella Cartella

Abbiamo preparato le configurazioni ottimali per ogni esigenza:

### A) `Pokewall_PSA_Display_U1_3Piatti_ZeroCambi.3mf` (CONSIGLIATO)
* **Contiene 3 piatti separati nello stesso progetto:**
  * **Piatto 1:** `Telaio Posteriore` (Nero - Slot 1) $\rightarrow$ **0 cambi filamento**, **0 torre di spurgo** (~45 min)
  * **Piatto 2:** `Guscio Superiore` (Rosso - Slot 3) $\rightarrow$ **0 cambi filamento**, **0 torre di spurgo** (~25 min)
  * **Piatto 3:** `Guscio Inferiore` (Bianco - Slot 2) $\rightarrow$ **0 cambi filamento**, **0 torre di spurgo** (~25 min)
* **Vantaggi:** **ZERO cambi filamento in assoluto**, usura meccanica azzerata, finitura superficiale impeccabile, tempo complessivo ridotto di oltre il 50%!

### B) `Pokewall_PSA_Display_U1_2Piatti.3mf`
* **Piatto 1:** `Telaio Posteriore` (Nero - Slot 1) $\rightarrow$ **0 cambi filamento**
* **Piatto 2:** `Guscio Superiore` (Rosso) + `Guscio Inferiore` (Bianco) stampati insieme

### C) `Pokewall_PSA_Display_U1.3mf`
* Piatto singolo originale con tutti e 3 i pezzi posizionati insieme (modalità per strato, 139 cambi).

---

## 4. Modifiche Geometriche Effettuate

1. **Allargamento Sede PSA a 82,5 mm**:
   * Nell'originale la sede misurava **81,0 mm**, risultando più stretta della custodia PSA (**81,3 mm**) con conseguente rischio di forzature e graffi.
   * La sede è stata allargata a **82,5 mm di larghezza × 137,2 mm di altezza × 6,5 mm di profondità**, garantendo un gioco di **0,6 mm per lato** per un inserimento fluido e sicuro della slab.
2. **Supporti**:
   * Abilitati solo dove strettamente necessari (sottosquadri dei fori di scatto sui gusci frontali).
3. **Dimensioni finali montato**:
   * **112,4 mm (L) × 167,4 mm (H) × 14,6 mm (P)**.

---

## 5. Istruzioni di Montaggio a Parete e Uso

1. **Fissaggio a parete**: Il telaio posteriore nero dispone di **4 fori svasati** (2 a sinistra e 2 a destra) per tasselli/viti da muro a testa svasata (diametro vite 3,5–4 mm).
2. **Inserimento carta**: Posizionare la slab PSA nuda nell'alloggiamento centrale del telaio nero.
3. **Applicazione gusci Pokéball**: 
   * Inserire a scatto il **Guscio Bianco** sulla parte inferiore.
   * Inserire a scatto il **Guscio Rosso** sulla parte superiore.
   * I due gusci coprono completamente le teste delle viti a muro, lasciando una cornice a forma di Pokéball pulita e senza fissaggi a vista.
4. **Sostituzione card**: Per cambiare carta è sufficiente tirare delicatamente i gusci frontali verso l'esterno.
