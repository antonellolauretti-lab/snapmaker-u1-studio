# Preferenze permanenti per i progetti di stampa 3D

## Autonomia e utilizzo

- L'utente autorizza piena autonomia operativa per le attività pertinenti al progetto `STAMPE 3D IA`: lettura e modifica dei file, modellazione, uso di strumenti e librerie, verifiche, slicing e organizzazione dei risultati. Procedere senza chiedere nuovamente conferma per queste attività quando necessarie al lavoro richiesto.
- Contenere l'utilizzo: riusare script, librerie e risultati già disponibili; raggruppare i controlli indipendenti; evitare render, ricerche e verifiche ripetute senza una ragione concreta. Non ridurre le verifiche necessarie per qualità, funzionalità e stampabilità.
- Questa autorizzazione non modifica il sandbox o i permessi obbligatori della piattaforma: rispettarli e riusare le autorizzazioni tecniche già approvate quando applicabili. Non promettere di eliminare richieste imposte dal sistema.

## Preferenze di stampa

- Stampante: Snapmaker U1, quattro ugelli da 0,4 mm; profilo PLA SnapSpeed e piatto PEI testurizzato, salvo diversa indicazione dell'utente.
- Privilegiare una buona qualità di stampa e mantenere i colori originali, prevedendo cambi di bobina fra i piatti.
- **Torre di spurgo/priming sempre disabilitata di default (`enable_prime_tower = "0"`)**: sulla Snapmaker U1 le 4 testine sono fisicamente indipendenti (nessuna contaminazione di colore all'interno dell'ugello) e la macchina gestisce la pulizia e il pre-carico tramite le stazioni dock esterne e la macro hardware `SM_PRINT_PREEXTRUDE_FILAMENT`. Disabilitare sempre la torre di spurgo nei piatti monocolore e anche nei piatti multicolore dove i cambi colore avvengono a quote elevate o localizzate (evitando la generazione di torri su centinaia di layer a vuoto). Attivarla solo ed esclusivamente se espressamente richiesto dall'utente.
- Usare il minor numero possibile di piatti per ciascun progetto, **MA evitando cambi filamento inutili per layer**:
  - **Raggruppare sempre insieme i componenti monocolore dello stesso colore** sullo stesso piatto (es. tutti i pezzi rossi insieme, tutti i pezzi neri insieme): questo produce piatti a **0 cambi filamento** e **0 torre di spurgo**, massimizzando velocità e qualità.
  - **Non mischiare pezzi completamente monocolore di colori diversi sullo stesso piatto** se non è possibile la stampa "per oggetto" (per via dell'ingombro della testina U1 di 72,5 mm): la modalità "per strato" genererebbe 1 o 2 cambi utensile ad ogni singolo layer (decine o centinaia di cambi inutili, usura e tempi morti).
  - **Riservare i piatti multicolore esclusivamente ai singoli componenti che richiedono intrinsecamente più colori** (es. basi con loghi incorporati, badge con scritte a contrasto), senza appesantirli con altri pezzi monocolore esterni che possono essere stampati a zero cambi.
- L'utente dispone di magneti cilindrici da **6 mm di diametro × 2 mm di spessore**. In ogni verifica futura controllare sempre se il progetto utilizza magneti, misurare tutte le sedi e adattarle a questi magneti quando necessario. Verificare il gioco di montaggio, lo spessore residuo, la polarità/accoppiamento e le eventuali pause di inserimento; documentare le misure effettive delle sedi. Non presumere la misura delle sedi dal solo nome del file.
- Salvare i progetti verificati in `PROGETTI DEFINITIVI`. Eliminare l'originale da `PROGETTI DA VERIFICARE` soltanto dopo aver verificato la copia definitiva.
