> Aggiornamento magneti 6×2 mm: le quattro sedi degli anelli sono ora Ø6,20 × 2,10 mm. Consultare [istruzioni e verifica aggiornate](PROGETTI%20DEFINITIVI/LEGGIMI_POKEBALL_MAGNETI_6x2.md). Le stime e il confronto geometrico riportati sotto descrivono la versione precedente.

# Pokeball — Snapmaker U1, qualità 0,08 mm

Aprire **Pokeball_U1_PRECISIONE.3mf** come progetto in Snapmaker Orca.

Il progetto è configurato per **Snapmaker PLA SnapSpeed**, quattro ugelli da **0,4 mm** e **piatto PEI ruvido**. L'utente ha confermato che tutti e quattro i filamenti sono PLA SnapSpeed e gli ugelli sono da 0,4 mm: non occorre modificare il profilo per materiale o diametro degli ugelli. Temperature del profilo PLA SnapSpeed: ugelli 220 °C, piatto 65 °C. Il flusso nominale del produttore non sostituisce una calibrazione dei singoli filamenti.

## Componenti e colori

Un solo piatto, geometrie e dimensioni originali. Due calotte, cerniera con due anelli, due parti del pulsante e otto perni.

| Testina | Colore | Componenti |
|---|---|---|
| 1 | Giallo | Non utilizzato da questo modello |
| 2 | Rosso | Calotta superiore e otto perni |
| 3 | Bianco | Calotta inferiore e centro pulsante |
| 4 | Nero | Anelli/cerniera e parte esterna pulsante |

## Impostazioni principali

- Strati 0,08 mm; primo strato 0,16 mm.
- Pareti esterne 40 mm/s, accelerazione 800 mm/s²; interne 80 mm/s.
- Tre pareti, riempimento gyroid 15%, superfici superiori a 30 mm/s.
- Risoluzione dei percorsi 0,005 mm; nessuna modifica o aumento artificiale della risoluzione della mesh originale.
- Cucitura posteriore; niente stiratura sulle calotte curve.
- Compensazione piede d'elefante 0,15 mm; compensazioni XY nulle per mantenere gli incastri.
- Calotte con apertura appoggiata al piatto; supporti disattivati. L'originale usava supporti manuali senza triangoli dipinti.
- Brim esterno da 3 mm sul gruppo dei perni, senza raft; anelli senza brim per non unire la cerniera.
- Stampa per strato, torre di adescamento attiva, cambio testina e macro macchina del profilo nativo U1.

## Verifica e limiti

Importazione, slicing ed esportazione G-code completati in **Snapmaker Orca 2.3.6**. Parametri riletti dal 3MF salvato dal programma e dal G-code. Geometrie entro il piatto, componenti separati; 388 strati. Controllo delle testine sulle estrusioni effettive nelle aree dei componenti documentato in `Verifica_tecnica/VERIFICA.json`.

Stima slicer: **9 h 21 min**, **66,99 g** totali, di cui **50,04 g** per i componenti e **16,95 g** per la torre. Riscaldamento, calibrazioni e pulizia possono aggiungere tempo e consumo. Non è stata avviata una stampa fisica.

Lo strato 0,08 mm rientra nell'intervallo dichiarato da Snapmaker per la U1: https://support.snapmaker.com/hc/en-us/articles/33344279396759-Snapmaker-U1-FAQ

Per una serie destinata alla vendita, valutare prima un esemplare completo: qualità reale delle calotte, scorrimento della cerniera e inserimento dei perni. La cerniera originale è la variante con gioco 0,2 mm; strati fini non garantiscono da soli la precisione degli incastri. La finitura FDM resta stratificata: 0,08 mm riduce i gradini, senza eliminarli completamente.

## Informazione contenuta nel file originale

Il modello originale attribuisce il design a **yoyothechicken** e riporta licenza **BY-NC-SA**. La descrizione incorporata dichiara che la licenza commerciale è ottenibile separatamente dall'autore. Questa conversione conserva tali metadati e non conferisce un'autorizzazione commerciale.

Il file originale `Sliced+Bambu.3mf` è conservato. I file intermedi e il G-code usato per il controllo si trovano in `Verifica_tecnica`; usare il progetto principale per applicare eventuali correzioni al materiale e rifare lo slicing.
