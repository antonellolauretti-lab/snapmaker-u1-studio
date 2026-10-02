# Chernabog (Fantasia) - Snapmaker U1 (Versione 15 cm - Corpo Blu & Occhi Gialli)

## 📌 Panoramica del Progetto
Modello di **Chernabog** dal capolavoro Disney *Fantasia*, scalato con precisione a **15,0 cm di altezza** mantenendo le identiche proporzioni originali su tutti gli assi (fattore di scala **82,38%**).
Configurato specificamente per **Snapmaker U1** con profilo **SnapSpeed PLA**, ugello da 0.4 mm e piatto PEI testurizzato.
- **Corpo, ali e base rocciosa:** **Blu SnapSpeed (Slot 4)**
- **Occhi / pupille a mandorla:** **Giallo brillante (Slot 3)**

---

## 📐 Dimensioni Proporzionate (Altezza 15 cm)

- **Altezza (Z):** **15,0 cm** (149.96 mm)
- **Larghezza (X - apertura massima ali):** **8,27 cm** (82.73 mm)
- **Profondità (Y - petto/braccia protese):** **6,49 cm** (64.88 mm)
- **Quota Occhi:** Gli occhi si trovano ad un'altezza compresa tra $Z = 93.96$ mm e $Z = 95.24$ mm da terra.

---

## 🖨️ Mappatura Bobine e Slot (Snapmaker U1)

| Slot / Posizione | Colore | Filamento Esatto | Ruolo nel Modello | Consumo Effettivo |
| :---: | :---: | :---: | :---: | :---: |
| **Slot 1** | *(Non usato)* | - | Libero / Qualsiasi | **0.00 g** |
| **Slot 2** | *(Non usato)* | - | Libero / Qualsiasi | **0.00 g** |
| **Slot 3** | **Giallo** (`#FFD700`) | **PLA SnapSpeed** | **Pupille / occhi a mandorla** | **0.03 g** |
| **Slot 4** | **Blu** (`#0055FF`) | **SnapSpeed PLA (RFID) Blue (003776) - SKU: 34064** | **Corpo intero, ali, base e supporti** | **74.11 g** |

---

## ⚙️ Parametri di Stampa e Ottimizzazione

- **Stampante:** Snapmaker U1 (4 ugelli indipendenti da 0,4 mm)
- **Profilo di stampa:** Snapmaker PLA SnapSpeed @U1 (Layer height 0.16 mm standard / 0.20 mm primo layer)
- **Temperatura Ugello:** 220 °C
- **Temperatura Piatto PEI:** 65 °C
- **Tempo di stampa stimato:** **6 ore e 15 minuti** *(risparmiate quasi 3 ore rispetto alla versione da 18 cm)*
- **Filamento totale consumato:** **74.14 g** *(risparmiati oltre 41 grammi di materiale)*
- **Torre di Spurgo (Prime Tower):** **DISABILITATA (`enable_prime_tower = "0"`)**
  - Zero spreco di plastica sul piatto.
  - La U1 gestisce la pulizia sui tergi-ugello in dock tramite macro hardware `SM_PRINT_PREEXTRUDE_FILAMENT`.
- **Supporti:** **Tree supports (ad albero slim)** con `support_on_build_plate_only = 1`.
  - Partono unicamente dal piano di stampa verso mento, ali e mani senza sfiorare né rovinare il corpo della statua.
  - Estrusi direttamente dalla testina Blu (Slot 4) a zero cambi per i supporti.
- **Cambi utensile:** Soltanto **8 cambi utensile** in tutto il ciclo di stampa (concentrati tra $Z = 94.0$ e $95.2$ mm). I restanti 930 layer sono stampati a zero cambi.

---

## 🧲 Controllo Magneti
- **Sedi magneti:** Nessuna sede magnete presente nel modello (base solida e monolitica ad altissima aderenza).

---

## 📂 File Inclusi nella Cartella

1. `Chernabog_U1_15CM_BLU_GIALLO_SLOT3_4.3mf`: File di stampa definitivo pronto all'uso a 15 cm di altezza.
2. `Chernabog_U1_BLU_GIALLO_SLOT3_4.3mf`: Versione originale a 18,2 cm (conservata come riferimento).
3. `anteprima_corpo_blu_occhi_gialli.png`: Rendering di dettaglio del volto con gli occhi gialli.
4. `VERIFICA.json`: Scheda tecnica certificata con hash crittografico SHA-256 e metriche di slicing a 15 cm.
