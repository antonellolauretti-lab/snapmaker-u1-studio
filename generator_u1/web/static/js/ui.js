/**
 * UI Controller & Event Handlers (v4.5 - Enhanced Fonts & Robust 3MF Download)
 * Gestisce:
 * 1. Switch dinamico tra generatore "Portachiavi" e "Targhetta da Tavolo" (Desk Sign).
 * 2. Dropdown Font Personalizzato con Anteprima Tipografica Reale (Google Fonts + System + Upload).
 * 3. Palette rapida a 4 slot per Snapmaker U1 con aggiornamento Three.js a 0 ms.
 * 4. Chiamate API protette con cold-start feedback (Render free tier) e toast notifications.
 * 5. Generazione e download 3MF nativo multi-volume per Snapmaker Orca con gestione errori.
 */

// ==============================================================================
// 0. CATALOGO FONT PRECARICATO (Disponibilità immediata a latenza zero)
// ==============================================================================
const DEFAULT_CURATED_FONTS = [
  { id: "Anton", name: "Anton", desc: "Massiccio Display Bold", category: "display", family: "'Anton', sans-serif" },
  { id: "Bebas Neue", name: "Bebas Neue", desc: "Alto e Condensato", category: "display", family: "'Bebas Neue', sans-serif" },
  { id: "Pacifico", name: "Pacifico", desc: "Corsivo Connesso Elegante", category: "script", family: "'Pacifico', cursive" },
  { id: "Lobster", name: "Lobster", desc: "Vintage Bold Script", category: "script", family: "'Lobster', cursive" },
  { id: "Bungee", name: "Bungee", desc: "Spesso e Dimensional", category: "display", family: "'Bungee', cursive" },
  { id: "Righteous", name: "Righteous", desc: "Retro Futuristico Techno", category: "display", family: "'Righteous', cursive" },
  { id: "Bangers", name: "Bangers", desc: "Fumetto Comic Bold", category: "display", family: "'Bangers', cursive" },
  { id: "Permanent Marker", name: "Permanent Marker", desc: "Tratto Pennarello Autentico", category: "script", family: "'Permanent Marker', cursive" },
  { id: "Orbitron", name: "Orbitron", desc: "Futuristico Sci-Fi Mecha", category: "display", family: "'Orbitron', sans-serif" },
  { id: "Montserrat", name: "Montserrat", desc: "Geometrico Moderno Bold", category: "sans-serif", family: "'Montserrat', sans-serif" },
  { id: "Poppins", name: "Poppins", desc: "Geometrico Pulito e Morbido", category: "sans-serif", family: "'Poppins', sans-serif" },
  { id: "Roboto", name: "Roboto", desc: "Standard Tecnico Bilanciato", category: "sans-serif", family: "'Roboto', sans-serif" },
  { id: "Oswald", name: "Oswald", desc: "Display Dinamico", category: "display", family: "'Oswald', sans-serif" },
  { id: "Playfair Display", name: "Playfair Display", desc: "Serif Elegante Tradizionale", category: "serif", family: "'Playfair Display', serif" },
  { id: "Cinzel", name: "Cinzel", desc: "Classico Romano Scolpito", category: "serif", family: "'Cinzel', serif" },
  { id: "Ubuntu", name: "Ubuntu", desc: "Humanist Moderno", category: "sans-serif", family: "'Ubuntu', sans-serif" },
  { id: "Arial", name: "Arial", desc: "Sans-Serif Standard", category: "sans-serif", family: "Arial, sans-serif" },
  { id: "Arial Black", name: "Arial Black", desc: "Ultra-Spesso Massiccio", category: "sans-serif", family: "'Arial Black', sans-serif" },
  { id: "Impact", name: "Impact", desc: "Massiccio Classico", category: "display", family: "Impact, sans-serif" },
  { id: "Segoe UI", name: "Segoe UI", desc: "Geometrico Interfaccia", category: "sans-serif", family: "'Segoe UI', sans-serif" },
  { id: "Segoe Script", name: "Segoe Script", desc: "Corsivo Continuo Saldato", category: "script", family: "'Segoe Script', cursive" },
  { id: "Georgia", name: "Georgia", desc: "Serif Classico", category: "serif", family: "Georgia, serif" },
  { id: "Consolas", name: "Consolas", desc: "Monospazio Tecnico", category: "monospace", family: "Consolas, monospace" },
];

let globalFontsList = [...DEFAULT_CURATED_FONTS];

const DEFAULT_CURATED_ICONS = [
  {
    "id": "none",
    "name": "Nessuna Icona",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Solo testo senza simboli aggiuntivi",
    "d": ""
  },
  {
    "id": "heart",
    "name": "Cuore",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Cuore classico romantico",
    "d": "M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"
  },
  {
    "id": "star",
    "name": "Stella",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Stella a 5 punte solida",
    "d": "M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"
  },
  {
    "id": "crown",
    "name": "Corona",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Corona regale maestosa",
    "d": "M2 19h20v2H2v-2zm1.5-4.5L5 9l5 4 2-8 2 8 5-4 1.5 5.5H3.5z"
  },
  {
    "id": "diamond",
    "name": "Diamante",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Gemma diamante sfaccettata",
    "d": "M19 3H5L2 9l10 12L22 9l-3-6z"
  },
  {
    "id": "shield",
    "name": "Scudo",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Scudo cavalleresco di protezione",
    "d": "M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3z"
  },
  {
    "id": "trophy",
    "name": "Trofeo",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Coppa trofeo vincitore",
    "d": "M19 5h-2V3H7v2H5c-1.1 0-2 .9-2 2v1c0 2.55 1.92 4.63 4.39 4.94.63 1.5 1.98 2.63 3.61 2.96V19H7v2h10v-2h-4v-3.1c1.63-.33 2.98-1.46 3.61-2.96C19.08 12.63 21 10.55 21 8V7c0-1.1-.9-2-2-2zM5 8V7h2v3.82C5.84 10.4 5 9.3 5 8zm14 0c0 1.3-.84 2.4-2 2.82V7h2v1z"
  },
  {
    "id": "medal",
    "name": "Medaglia",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Medaglia al valore con nastro",
    "d": "M12 15c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"
  },
  {
    "id": "ribbon",
    "name": "Fiocco / Coccarda",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Fiocco elegante o nastro regalo",
    "d": "M12 2C8.69 2 6 4.69 6 8c0 2.97 2.16 5.44 5 5.91V22l4-2 4 2v-8.09c2.84-.47 5-2.94 5-5.91 0-3.31-2.69-6-6-6zm0 10c-2.21 0-4-1.79-4-4s1.79-4 4-4 4 1.79 4 4-1.79 4-4 4z"
  },
  {
    "id": "clover",
    "name": "Quadrifoglio",
    "category": "forme",
    "category_name": "Forme Classiche",
    "desc": "Trifoglio / Quadrifoglio portafortuna",
    "d": "M12 9.5C10.6 9.5 9.5 8.4 9.5 7s1.1-2.5 2.5-2.5 2.5 1.1 2.5 2.5-1.1 2.5-2.5 2.5zm-2.5 5c0-1.4-1.1-2.5-2.5-2.5S4.5 13.1 4.5 14.5s1.1 2.5 2.5 2.5 2.5-1.1 2.5-2.5zm9.5 0c0-1.4-1.1-2.5-2.5-2.5s-2.5 1.1-2.5 2.5 1.1 2.5 2.5 2.5 2.5-1.1 2.5-2.5zm-7 5c-1.4 0-2.5-1.1-2.5-2.5s1.1-2.5 2.5-2.5 2.5 1.1 2.5 2.5-1.1 2.5-2.5 2.5z"
  },
  {
    "id": "paw",
    "name": "Zampa",
    "category": "animali",
    "category_name": "Animali",
    "desc": "Impronta zampa di cane o gatto",
    "d": "M12 13c-2.2 0-4 1.8-4 4s1.8 4 4 4 4-1.8 4-4-1.8-4-4-4zm-4.5-3c1.38 0 2.5-1.12 2.5-2.5S8.88 5 7.5 5 5 6.12 5 7.5 6.12 10 7.5 10zm9 0c1.38 0 2.5-1.12 2.5-2.5S17.88 5 16.5 5 14 6.12 14 7.5s1.12 2.5 2.5 2.5zm-6-2C11.38 8 12.5 6.88 12.5 5.5S11.38 3 10 3 7.5 4.12 7.5 5.5 8.62 8 10 8zm4 0c1.38 0 2.5-1.12 2.5-2.5S15.38 3 14 3s-2.5 1.12-2.5 2.5S12.62 8 14 8z"
  },
  {
    "id": "cat",
    "name": "Gatto",
    "category": "animali",
    "category_name": "Animali",
    "desc": "Testa di gattino con orecchie a punta",
    "d": "M12 14c-3.31 0-6 2.69-6 6h12c0-3.31-2.69-6-6-6zm-7-2l2-7 4 3 3-1 3 1 4-3 2 7c-2 2-5 3-8 3s-6-1-8-3z"
  },
  {
    "id": "dog",
    "name": "Cane",
    "category": "animali",
    "category_name": "Animali",
    "desc": "Profilo muso di cane fedele",
    "d": "M19 12c-1.5 0-2.8.6-3.7 1.6L12 10.3V5c0-1.1-.9-2-2-2H8C6.9 3 6 3.9 6 5v5.3L2.7 13.6C1.8 12.6.5 12-1 12v3c1.1 0 2 .9 2 2v2c0 1.7 1.3 3 3 3h12c1.7 0 3-1.3 3-3v-2c0-1.1.9-2 2-2v-3z"
  },
  {
    "id": "fish",
    "name": "Pesce",
    "category": "animali",
    "category_name": "Animali",
    "desc": "Pesciolino marino nuotatore",
    "d": "M2 12s4-5 11-5c3 0 6 2 9 5-3 3-6 5-9 5-7 0-11-5-11-5zm20 0l-3-4v8l3-4z"
  },
  {
    "id": "butterfly",
    "name": "Farfalla",
    "category": "animali",
    "category_name": "Animali",
    "desc": "Farfalla con ali spiegate",
    "d": "M12 5c-1 0-2 .8-2 1.8V17c0 1 .9 2 2 2s2-1 2-2V6.8c0-1-1-1.8-2-1.8zm-3 2C6 7 2 9 2 13s3 5 7 4V7zm6 0v10c4 1 7 0 7-4s-4-6-7-6z"
  },
  {
    "id": "bird",
    "name": "Uccello",
    "category": "animali",
    "category_name": "Animali",
    "desc": "Uccello o colomba in volo",
    "d": "M22 6c-1.5 1-3.5 1-5 .5C15 5 13 6 12 8c-2-1-5-1-7 1 3 0 5 1 6 3-3 0-5 2-6 4 3 0 5 0 7-1-2 2-3 4-3 6 4-1 7-4 9-8 2 0 4-1 4-7z"
  },
  {
    "id": "gamepad",
    "name": "Controller Gamer",
    "category": "gaming",
    "category_name": "Gaming & Geek",
    "desc": "Joypad da console / gamepad",
    "d": "M15 7.5V2H9v5.5l3 3 3-3zM7.5 9H2v6h5.5l3-3-3-3zM9 16.5V22h6v-5.5l-3-3-3 3zM16.5 9l-3 3 3 3H22V9h-5.5z"
  },
  {
    "id": "sword",
    "name": "Spada",
    "category": "gaming",
    "category_name": "Gaming & Geek",
    "desc": "Spada da cavaliere RPG",
    "d": "M19.7 4.3c-.4-.4-1-.4-1.4 0L12 10.6 8.4 7 7 8.4l3.6 3.6-7.3 7.3V21h1.7l7.3-7.3 3.6 3.6 1.4-1.4-3.6-3.6 6.3-6.3c.4-.4.4-1 0-1.7z"
  },
  {
    "id": "skull",
    "name": "Teschio",
    "category": "gaming",
    "category_name": "Gaming & Geek",
    "desc": "Teschio piratesco o gothic",
    "d": "M12 2C7.03 2 3 6.03 3 11c0 3.12 1.6 5.87 4 7.45V21c0 .55.45 1 1 1h8c.55 0 1-.45 1-1v-2.55c2.4-1.58 4-4.33 4-7.45 0-4.97-4.03-9-9-9zm-3 12c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm6 0c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"
  },
  {
    "id": "ghost",
    "name": "Fantasma",
    "category": "gaming",
    "category_name": "Gaming & Geek",
    "desc": "Fantasmino stile arcade rétro",
    "d": "M12 2C7.58 2 4 5.58 4 10v10l3-3 3 3 2-2 2 2 3-3 3 3V10c0-4.42-3.58-8-8-8zm-3 9c-.83 0-1.5-.67-1.5-1.5S8.17 8 9 8s1.5.67 1.5 1.5S9.83 11 9 11zm6 0c-.83 0-1.5-.67-1.5-1.5S14.17 8 15 8s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"
  },
  {
    "id": "dice",
    "name": "Dado",
    "category": "gaming",
    "category_name": "Gaming & Geek",
    "desc": "Dado a 6 facce da gioco da tavolo",
    "d": "M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM7.5 18c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm0-9C6.67 9 6 8.33 6 7.5S6.67 6 7.5 6 9 6.67 9 7.5 8.33 9 7.5 9zm4.5 4.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm4.5 4.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm0-9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"
  },
  {
    "id": "rocket",
    "name": "Razzo Spaziale",
    "category": "gaming",
    "category_name": "Gaming & Geek",
    "desc": "Navicella / razzo in decollo",
    "d": "M12 2.5s-5 4.5-5 10.5c0 3 1.5 5 2 6l3-1 3 1c.5-1 2-3 2-6 0-6-5-10.5-5-10.5zm0 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm-7 8l2-3c-.5-1-1-2.5-1-4L2 15l3 4.5zm14 0l-2-3c.5-1 1-2.5 1-4l4 2.5-3 4.5z"
  },
  {
    "id": "music",
    "name": "Nota Musicale",
    "category": "musica",
    "category_name": "Musica",
    "desc": "Nota musicale singola",
    "d": "M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"
  },
  {
    "id": "music_double",
    "name": "Doppia Nota",
    "category": "musica",
    "category_name": "Musica",
    "desc": "Due note musicali unite",
    "d": "M21 3L9 6.5v10.3c-.6-.3-1.3-.5-2-.5-2.2 0-4 1.8-4 4s1.8 4 4 4 4-1.8 4-4V10.8l8-2.3v6.3c-.6-.3-1.3-.5-2-.5-2.2 0-4 1.8-4 4s1.8 4 4 4 4-1.8 4-4V3z"
  },
  {
    "id": "headphones",
    "name": "Cuffie DJ",
    "category": "musica",
    "category_name": "Musica",
    "desc": "Cuffie stereo ad archetto",
    "d": "M12 3C6.5 3 2 7.5 2 13v6c0 1.7 1.3 3 3 3h2v-8H4v-1c0-4.4 3.6-8 8-8s8 3.6 8 8v1h-3v8h2c1.7 0 3-1.3 3-3v-6c0-5.5-4.5-10-10-10z"
  },
  {
    "id": "guitar",
    "name": "Chitarra",
    "category": "musica",
    "category_name": "Musica",
    "desc": "Chitarra rock o classica",
    "d": "M20 3l-1.5 1.5 2 2L19 8l-2-2-4 4c.5 1.2.3 2.6-.6 3.5l-1 1c-.3.3-.7.5-1.1.6L8 13.5l3.5-3.5c.1-.4.3-.8.6-1.1l1-1c.9-.9 2.3-1.1 3.5-.6l4-4-2-2L20 3zM4 17.5C4 15.6 5.6 14 7.5 14S11 15.6 11 17.5 9.4 21 7.5 21 4 19.4 4 17.5z"
  },
  {
    "id": "soccer",
    "name": "Calcio",
    "category": "sport",
    "category_name": "Sport & Fitness",
    "desc": "Pallone da calcio a esagoni",
    "d": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 3.1l2.5 1.8-.9 2.9h-3.2l-.9-2.9L13 5.1zM6.3 8.8l2.6 1.1-.9 2.9-2.7-.9c.2-1.1.5-2.1 1-3.1zm-.3 6.3l2.8-.9 1.8 2.4-1.7 2.4c-1.3-1.1-2.3-2.4-2.9-3.9zm9 4c-.7.5-1.5.8-2.3.9l-1.4-2.7 1.8-2.4 2.8.9c-.3 1.2-.5 2.2-.9 3.3zm2.7-5.1l-2.7.9-.9-2.9 2.6-1.1c.5 1 1 2 1 3.1z"
  },
  {
    "id": "dumbbell",
    "name": "Manubrio Pesi",
    "category": "sport",
    "category_name": "Sport & Fitness",
    "desc": "Manubrio fitness da palestra",
    "d": "M6.5 5h-2c-.8 0-1.5.7-1.5 1.5v11c0 .8.7 1.5 1.5 1.5h2c.8 0 1.5-.7 1.5-1.5V6.5c0-.8-.7-1.5-1.5-1.5zm13 0h-2c-.8 0-1.5.7-1.5 1.5v11c0 .8.7 1.5 1.5 1.5h2c.8 0 1.5-.7 1.5-1.5V6.5c0-.8-.7-1.5-1.5-1.5zM15 11H9v2h6v-2z"
  },
  {
    "id": "target",
    "name": "Bersaglio",
    "category": "sport",
    "category_name": "Sport & Fitness",
    "desc": "Bersaglio centro perfetto",
    "d": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm0-14c-3.31 0-6 2.69-6 6s2.69 6 6 6 6-2.69 6-6-2.69-6-6-6zm0 8c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"
  },
  {
    "id": "car",
    "name": "Auto Sportiva",
    "category": "motori",
    "category_name": "Auto & Motori",
    "desc": "Automobile / silhouette vettura",
    "d": "M18.92 6.01C18.72 5.42 18.16 5 17.5 5h-11c-.66 0-1.21.42-1.42 1.01L3 12v8c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-1h12v1c0 .55.45 1 1 1h1c.55 0 1-.45 1-1v-8l-2.08-5.99zM6.5 16c-.83 0-1.5-.67-1.5-1.5S5.67 13 6.5 13s1.5.67 1.5 1.5S7.33 16 6.5 16zm11 0c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zM5 11l1.5-4.5h11L19 11H5z"
  },
  {
    "id": "motorcycle",
    "name": "Moto",
    "category": "motori",
    "category_name": "Auto & Motori",
    "desc": "Motocicletta racing o scooter",
    "d": "M19.4 9.3l-2.8-5.6c-.3-.5-.8-.7-1.3-.7H12v2h3.3l1.8 3.6L14 11H9.8l-1-2H11V7H7.8l-1.5-3H4v2h1.2l3.4 6.8c-.8.8-1.4 1.9-1.5 3.2-1.9.4-3.3 2-3.3 4 0 2.2 1.8 4 4 4s4-1.8 4-4c0-.7-.2-1.3-.5-1.9l2.7-2.1h3l3.2 4.2c-.3.6-.5 1.2-.5 1.8 0 2.2 1.8 4 4 4s4-1.8 4-4c0-2-1.4-3.6-3.3-4-.1-1.8-1.1-3.3-2.6-4.1zM7.8 19c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm11.4 0c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2z"
  },
  {
    "id": "wrench",
    "name": "Chiave Inglese",
    "category": "motori",
    "category_name": "Auto & Motori",
    "desc": "Attrezzo meccanico chiave di lavoro",
    "d": "M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.6C.5 7 1 10 3 12c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.4-.4.4-1 0-1.3z"
  },
  {
    "id": "leaf",
    "name": "Foglia",
    "category": "natura",
    "category_name": "Natura & Meteo",
    "desc": "Foglia verde biologica",
    "d": "M17 8C8 10 5.9 16.17 3.82 21.34L5.71 22l1-2.3A4.49 4.49 0 0 0 8 20C19 20 22 3 22 3c-1 2-8 2.25-13 3.25S2 11.5 2 13.5s1.75 3.75 1.75 3.75C7 8 17 8 17 8z"
  },
  {
    "id": "tree",
    "name": "Albero / Pino",
    "category": "natura",
    "category_name": "Natura & Meteo",
    "desc": "Pino boschivo o abete natalizio",
    "d": "M14 18v4h-4v-4H4l4.5-5H6l4.5-5H8l4-6 4 6h-2.5l4.5 5h-2.5l4.5 5h-6z"
  },
  {
    "id": "fire",
    "name": "Fuoco / Fiamma",
    "category": "natura",
    "category_name": "Natura & Meteo",
    "desc": "Fiamma viva potente",
    "d": "M12 23c-4.97 0-9-4.03-9-9 0-3.61 2.21-6.7 5.37-8.08.31-.13.66.02.77.33.1.28.02.59-.21.78C7.54 8.23 7 9.8 7 11.5c0 .35.03.7.09 1.04.06.34.37.58.71.55.33-.03.58-.31.57-.64C8.28 11.23 9.49 10 11 10c.85 0 1.62.36 2.16.94.24.26.65.28.91.04.14-.13.2-.31.18-.49-.24-2.18-1.55-4.01-3.37-4.9-.3-.15-.42-.51-.27-.81.14-.28.47-.41.77-.3 3.82 1.34 6.62 5.01 6.62 9.52 0 4.97-4.03 9-9 9z"
  },
  {
    "id": "lightning",
    "name": "Fulmine",
    "category": "natura",
    "category_name": "Natura & Meteo",
    "desc": "Saetta di energia elettrica",
    "d": "M7 2v11h3v9l7-12h-4l4-8z"
  },
  {
    "id": "sun",
    "name": "Sole",
    "category": "natura",
    "category_name": "Natura & Meteo",
    "desc": "Sole raggiante splendente",
    "d": "M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58c-.39-.39-1.03-.39-1.41 0s-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37c-.39-.39-1.03-.39-1.41 0s-.39 1.03 0 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41l-1.06-1.06zm1.06-10.96c.39-.39.39-1.03 0-1.41s-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36c.39-.39.39-1.03 0-1.41s-1.03-.39-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z"
  },
  {
    "id": "moon",
    "name": "Mezzaluna",
    "category": "natura",
    "category_name": "Natura & Meteo",
    "desc": "Luna crescente notturna",
    "d": "M12.3 2a10 10 0 0 0-1.9 19.8 10 10 0 0 0 11.6-11.6A10 10 0 0 1 12.3 2z"
  },
  {
    "id": "snowflake",
    "name": "Fiocco di Neve",
    "category": "natura",
    "category_name": "Natura & Meteo",
    "desc": "Cristallo di ghiaccio invernale",
    "d": "M13 2h-2v4.18L8.46 3.65 7.05 5.06 9.99 8H5.82L3.65 5.83 2.24 7.24 4.18 9.18v3.64H2v2h2.18l-1.94 1.94 1.41 1.41 2.17-2.17h4.17l-2.94 2.94 1.41 1.41L11 17.82V22h2v-4.18l2.54 2.53 1.41-1.41-2.94-2.94h4.17l2.17 2.17 1.41-1.41-1.94-1.94H22v-2h-2.18l1.94-1.94-1.41-1.41-2.17 2.17h-4.17l2.94-2.94-1.41-1.41L13 6.18V2z"
  },
  {
    "id": "smile",
    "name": "Smile Felice",
    "category": "simboli",
    "category_name": "Simboli & Faccine",
    "desc": "Faccina sorridente allegra",
    "d": "M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z"
  },
  {
    "id": "sunglasses",
    "name": "Occhiali da Sole",
    "category": "simboli",
    "category_name": "Simboli & Faccine",
    "desc": "Stile cool con lenti scure",
    "d": "M22 8c-.6-1.8-2.3-3-4.2-3H6.2C4.3 5 2.6 6.2 2 8L1 12v3c0 1.7 1.3 3 3 3h5c1.7 0 3-1.3 3-3v-1h.1v1c0 1.7 1.3 3 3 3h5c1.7 0 3-1.3 3-3v-3l-1-4zM8 15H5c-.6 0-1-.4-1-1v-2l1-3c.2-.6.7-1 1.3-1H8c1.1 0 2 .9 2 2v3c0 1.1-.9 2-2 2zm11 0h-3c-1.1 0-2-.9-2-2v-3c0-1.1.9-2 2-2h1.7c.6 0 1.1.4 1.3 1l1 3v2c0 .6-.4 1-1 1z"
  },
  {
    "id": "infinity",
    "name": "Infinito",
    "category": "simboli",
    "category_name": "Simboli & Faccine",
    "desc": "Simbolo di infinito eterno",
    "d": "M18.6 6.62c-1.44 0-2.8.56-3.77 1.53L12 11l-2.83-2.85c-.97-.97-2.33-1.53-3.77-1.53-2.93 0-5.4 2.47-5.4 5.4s2.47 5.4 5.4 5.4c1.44 0 2.8-.56 3.77-1.53L12 13l2.83 2.85c.97.97 2.33 1.53 3.77 1.53 2.93 0 5.4-2.47 5.4-5.4s-2.47-5.4-5.4-5.4zm-13.2 8.4c-1.65 0-3-1.35-3-3s1.35-3 3-3c.8 0 1.55.31 2.08.85L9.66 12l-2.18 2.15c-.53.54-1.28.85-2.08.85zm13.2 0c-.8 0-1.55-.31-2.08-.85L14.34 12l2.18-2.15c.53-.54 1.28-.85 2.08-.85 1.65 0 3 1.35 3 3s-1.35 3-3 3z"
  },
  {
    "id": "check_circle",
    "name": "Spunta OK",
    "category": "simboli",
    "category_name": "Simboli & Faccine",
    "desc": "Cerchio con spunta di conferma",
    "d": "M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
  },
  {
    "id": "gift",
    "name": "Pacco Regalo",
    "category": "simboli",
    "category_name": "Simboli & Faccine",
    "desc": "Scatola regalo con nastro e fiocco",
    "d": "M20 6h-2.18c.11-.31.18-.65.18-1 0-1.66-1.34-3-3-3-1.05 0-1.96.54-2.5 1.35l-.5.65-.5-.65C10.96 2.54 10.05 2 9 2 7.34 2 6 3.34 6 5c0 .35.07.69.18 1H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-5-2c.55 0 1 .45 1 1s-.45 1-1 1h-2.22l.62-.83c.37-.48.95-.77 1.6-.77zm-6 0c.65 0 1.23.29 1.6.77l.62.83H9c-.55 0-1-.45-1-1s.45-1 1-1zm11 15H4v-2h16v2zm0-5H4V8h5.08L7 10.83 8.62 12 11 8.76V14h2V8.76L15.38 12 17 10.83 14.92 8H20v6z"
  },
  {
    "id": "coffee",
    "name": "Tazzina Caffè",
    "category": "simboli",
    "category_name": "Simboli & Faccine",
    "desc": "Tazza di espresso fumante",
    "d": "M20 3H4v10c0 2.21 1.79 4 4 4h6c2.21 0 4-1.79 4-4v-3h2c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 5h-2V5h2v3zM4 19h16v2H4z"
  }
];

let globalIconsList = [...DEFAULT_CURATED_ICONS];


// ==============================================================================
// 0.1 TOAST NOTIFICATIONS MANAGER
// ==============================================================================
const ToastManager = {
  container: null,
  init() {
    this.container = document.getElementById("studioToastContainer");
    if (!this.container) {
      this.container = document.createElement("div");
      this.container.id = "studioToastContainer";
      this.container.className = "studio-toast-container";
      document.body.appendChild(this.container);
    }
  },
  show({ type = "info", title, message, duration = 5000 }) {
    if (!this.container) this.init();

    const toast = document.createElement("div");
    toast.className = `studio-toast ${type}`;

    let icon = "ℹ️";
    if (type === "warning") icon = "⏳";
    if (type === "success") icon = "✅";
    if (type === "error") icon = "❌";

    toast.innerHTML = `
      <span class="studio-toast-icon">${icon}</span>
      <div class="studio-toast-body">
        ${title ? `<div class="studio-toast-title">${title}</div>` : ""}
        <div class="studio-toast-message">${message}</div>
      </div>
      <button type="button" class="studio-toast-close" title="Chiudi">✕</button>
    `;

    const closeBtn = toast.querySelector(".studio-toast-close");
    closeBtn.addEventListener("click", () => this.dismiss(toast));

    this.container.appendChild(toast);

    if (duration > 0) {
      setTimeout(() => this.dismiss(toast), duration);
    }

    return toast;
  },
  dismiss(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.add("fade-out");
    setTimeout(() => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, 200);
  },
};

// ==============================================================================
// 0.2 CUSTOM FONT DROPDOWN COMPONENT (Anteprima reale e ricerca)
// ==============================================================================
class CustomFontDropdown {
  constructor(selectElem, onFontChange) {
    this.selectElem = selectElem;
    this.onFontChange = onFontChange;
    this.currentCategory = "all";
    this.searchTerm = "";

    this.init();
  }

  init() {
    this.selectElem.style.display = "none";

    this.wrapper = document.createElement("div");
    this.wrapper.className = "custom-font-dropdown";

    this.wrapper.innerHTML = `
      <div class="custom-font-trigger" tabindex="0">
        <div class="custom-font-trigger-info">
          <span class="custom-font-current-name">Arial</span>
          <span class="custom-font-current-badge">Sans</span>
        </div>
        <span class="custom-font-arrow">▼</span>
      </div>
      <div class="custom-font-menu">
        <div class="custom-font-search-box">
          <input type="text" class="custom-font-search-input" placeholder="🔍 Cerca font per nome o stile...">
        </div>
        <div class="custom-font-filter-chips">
          <button type="button" class="custom-font-chip active" data-cat="all">Tutti</button>
          <button type="button" class="custom-font-chip" data-cat="display">Display</button>
          <button type="button" class="custom-font-chip" data-cat="script">Corsivo</button>
          <button type="button" class="custom-font-chip" data-cat="sans-serif">Sans</button>
          <button type="button" class="custom-font-chip" data-cat="serif">Serif</button>
          <button type="button" class="custom-font-chip" data-cat="custom">Caricati</button>
        </div>
        <div class="custom-font-options-list"></div>
      </div>
    `;

    this.selectElem.parentNode.insertBefore(this.wrapper, this.selectElem.nextSibling);

    this.trigger = this.wrapper.querySelector(".custom-font-trigger");
    this.menu = this.wrapper.querySelector(".custom-font-menu");
    this.currentName = this.wrapper.querySelector(".custom-font-current-name");
    this.currentBadge = this.wrapper.querySelector(".custom-font-current-badge");
    this.searchInput = this.wrapper.querySelector(".custom-font-search-input");
    this.optionsList = this.wrapper.querySelector(".custom-font-options-list");
    this.chips = this.wrapper.querySelectorAll(".custom-font-chip");

    // Eventi
    this.trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      this.toggleMenu();
    });

    this.trigger.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        this.toggleMenu();
      }
    });

    this.searchInput.addEventListener("input", (e) => {
      this.searchTerm = e.target.value.toLowerCase().trim();
      this.renderOptions();
    });

    this.searchInput.addEventListener("click", (e) => e.stopPropagation());

    this.chips.forEach((chip) => {
      chip.addEventListener("click", (e) => {
        e.stopPropagation();
        this.chips.forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        this.currentCategory = chip.dataset.cat;
        this.renderOptions();
      });
    });

    document.addEventListener("click", (e) => {
      if (!this.wrapper.contains(e.target)) {
        this.closeMenu();
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") this.closeMenu();
    });

    this.updateFromSelect();
  }

  toggleMenu() {
    const isOpen = this.wrapper.classList.contains("open");
    // Chiudi tutti gli altri dropdown aperti
    document.querySelectorAll(".custom-font-dropdown.open").forEach((d) => {
      if (d !== this.wrapper) d.classList.remove("open");
    });

    if (isOpen) {
      this.closeMenu();
    } else {
      this.wrapper.classList.add("open");
      this.renderOptions();
      setTimeout(() => this.searchInput.focus(), 50);
    }
  }

  closeMenu() {
    this.wrapper.classList.remove("open");
  }

  updateFromSelect() {
    const selectedVal = this.selectElem.value || "Arial";
    const font = globalFontsList.find((f) => f.id === selectedVal) || {
      id: selectedVal,
      name: selectedVal,
      category: "sans-serif",
      family: selectedVal,
    };

    this.currentName.textContent = font.name || font.id;
    this.currentName.style.fontFamily = font.family || font.id;
    this.currentBadge.textContent = font.category || "Font";
  }

  renderOptions() {
    this.optionsList.innerHTML = "";
    const selectedVal = this.selectElem.value;

    const filtered = globalFontsList.filter((f) => {
      const matchCat = this.currentCategory === "all" || f.category === this.currentCategory;
      const matchSearch = !this.searchTerm ||
        f.id.toLowerCase().includes(this.searchTerm) ||
        (f.name && f.name.toLowerCase().includes(this.searchTerm)) ||
        (f.desc && f.desc.toLowerCase().includes(this.searchTerm));
      return matchCat && matchSearch;
    });

    if (filtered.length === 0) {
      this.optionsList.innerHTML = `<div style="padding: 12px; color: var(--text-dim); text-align: center; font-size: 12px;">Nessun carattere trovato.</div>`;
      return;
    }

    filtered.forEach((font) => {
      const isSelected = font.id === selectedVal;
      const item = document.createElement("div");
      item.className = `custom-font-option-item ${isSelected ? "selected" : ""}`;
      item.dataset.value = font.id;

      item.innerHTML = `
        <div class="custom-font-item-main">
          <div class="custom-font-item-name" style="font-family: ${font.family || font.id};">
            ${font.name || font.id}
          </div>
          <div class="custom-font-item-sample" style="font-family: ${font.family || font.id};">
            ${font.desc || "Anteprima Testo 3D • Snapmaker U1"}
          </div>
        </div>
        <div class="custom-font-item-meta">
          <span class="custom-font-item-badge">${font.category || "Font"}</span>
          ${isSelected ? `<span class="custom-font-check">✓</span>` : ""}
        </div>
      `;

      item.addEventListener("click", (e) => {
        e.stopPropagation();
        this.selectFont(font.id);
      });

      this.optionsList.appendChild(item);
    });
  }

  selectFont(fontId) {
    this.selectElem.value = fontId;
    this.updateFromSelect();
    this.closeMenu();

    // Trigger evento change sul select originario per retrocompatibilità
    const event = new Event("change", { bubbles: true });
    this.selectElem.dispatchEvent(event);

    if (this.onFontChange) this.onFontChange(fontId);
  }
}

// ==============================================================================
// 0.3 CUSTOM ICON DROPDOWN COMPONENT (Libreria 40+ Simboli Vettoriali e Ricerca)
// ==============================================================================
class CustomIconDropdown {
  constructor(selectElem, onIconChange) {
    this.selectElem = selectElem;
    this.onIconChange = onIconChange;
    this.currentCategory = "all";
    this.searchTerm = "";

    this.init();
  }

  init() {
    this.selectElem.style.display = "none";

    this.wrapper = document.createElement("div");
    this.wrapper.className = "custom-icon-dropdown";

    this.wrapper.innerHTML = `
      <div class="custom-icon-trigger" tabindex="0">
        <div class="custom-icon-trigger-info">
          <div class="custom-icon-trigger-preview">
            <span class="custom-icon-none-badge">✕</span>
          </div>
          <span class="custom-icon-current-name">Nessuna Icona</span>
          <span class="custom-icon-current-badge">Solo Testo</span>
        </div>
        <span class="custom-icon-arrow">▼</span>
      </div>
      <div class="custom-icon-menu">
        <div class="custom-icon-search-box">
          <input type="text" class="custom-icon-search-input" placeholder="🔍 Cerca simbolo (es. cuore, zampa, auto, gamer, sport)...">
        </div>
        <div class="custom-icon-filter-chips">
          <button type="button" class="custom-icon-chip active" data-cat="all">Tutti</button>
          <button type="button" class="custom-icon-chip" data-cat="forme">Forme</button>
          <button type="button" class="custom-icon-chip" data-cat="animali">Animali</button>
          <button type="button" class="custom-icon-chip" data-cat="gaming">Gaming</button>
          <button type="button" class="custom-icon-chip" data-cat="musica">Musica</button>
          <button type="button" class="custom-icon-chip" data-cat="sport">Sport</button>
          <button type="button" class="custom-icon-chip" data-cat="motori">Motori</button>
          <button type="button" class="custom-icon-chip" data-cat="natura">Natura</button>
          <button type="button" class="custom-icon-chip" data-cat="simboli">Simboli</button>
        </div>
        <div class="custom-icon-options-list"></div>
      </div>
    `;

    this.selectElem.parentNode.insertBefore(this.wrapper, this.selectElem.nextSibling);

    this.trigger = this.wrapper.querySelector(".custom-icon-trigger");
    this.menu = this.wrapper.querySelector(".custom-icon-menu");
    this.previewWrap = this.wrapper.querySelector(".custom-icon-trigger-preview");
    this.currentName = this.wrapper.querySelector(".custom-icon-current-name");
    this.currentBadge = this.wrapper.querySelector(".custom-icon-current-badge");
    this.searchInput = this.wrapper.querySelector(".custom-icon-search-input");
    this.optionsList = this.wrapper.querySelector(".custom-icon-options-list");
    this.chips = this.wrapper.querySelectorAll(".custom-icon-chip");

    // Eventi
    this.trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      this.toggleMenu();
    });

    this.trigger.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        this.toggleMenu();
      }
    });

    this.searchInput.addEventListener("input", (e) => {
      this.searchTerm = e.target.value.toLowerCase().trim();
      this.renderOptions();
    });

    this.searchInput.addEventListener("click", (e) => e.stopPropagation());

    this.chips.forEach((chip) => {
      chip.addEventListener("click", (e) => {
        e.stopPropagation();
        this.chips.forEach((c) => c.classList.remove("active"));
        chip.classList.add("active");
        this.currentCategory = chip.dataset.cat;
        this.renderOptions();
      });
    });

    document.addEventListener("click", (e) => {
      if (!this.wrapper.contains(e.target)) {
        this.closeMenu();
      }
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") this.closeMenu();
    });

    this.updateFromSelect();
  }

  toggleMenu() {
    const isOpen = this.wrapper.classList.contains("open");
    document.querySelectorAll(".custom-icon-dropdown.open, .custom-font-dropdown.open").forEach((d) => {
      if (d !== this.wrapper) d.classList.remove("open");
    });

    if (isOpen) {
      this.closeMenu();
    } else {
      this.wrapper.classList.add("open");
      this.renderOptions();
      setTimeout(() => this.searchInput.focus(), 50);
    }
  }

  closeMenu() {
    this.wrapper.classList.remove("open");
  }

  updateFromSelect() {
    const selectedVal = this.selectElem.value || "none";
    const icon = globalIconsList.find((i) => i.id === selectedVal) || {
      id: "none",
      name: "Nessuna Icona",
      category: "forme",
      category_name: "Solo Testo",
      d: ""
    };

    if (icon.d) {
      this.previewWrap.innerHTML = `<svg viewBox="0 0 24 24"><path d="${icon.d}" /></svg>`;
    } else {
      this.previewWrap.innerHTML = `<span class="custom-icon-none-badge">✕</span>`;
    }

    this.currentName.textContent = icon.name;
    this.currentBadge.textContent = icon.category_name || icon.category;
  }

  renderOptions() {
    this.optionsList.innerHTML = "";
    const selectedVal = this.selectElem.value || "none";

    const filtered = globalIconsList.filter((icon) => {
      const matchCat = this.currentCategory === "all" || icon.category === this.currentCategory;
      const matchSearch = !this.searchTerm ||
        icon.id.toLowerCase().includes(this.searchTerm) ||
        (icon.name && icon.name.toLowerCase().includes(this.searchTerm)) ||
        (icon.desc && icon.desc.toLowerCase().includes(this.searchTerm));
      return matchCat && matchSearch;
    });

    if (filtered.length === 0) {
      this.optionsList.innerHTML = `<div style="padding: 12px; color: var(--text-dim); text-align: center; font-size: 12px;">Nessun simbolo trovato.</div>`;
      return;
    }

    filtered.forEach((icon) => {
      const isSelected = icon.id === selectedVal;
      const item = document.createElement("div");
      item.className = `custom-icon-option-item ${isSelected ? "selected" : ""}`;
      item.dataset.value = icon.id;

      const svgHtml = icon.d
        ? `<svg viewBox="0 0 24 24"><path d="${icon.d}" /></svg>`
        : `<span style="font-size: 14px; opacity: 0.7;">❌</span>`;

      item.innerHTML = `
        <div class="custom-icon-item-left">
          <div class="custom-icon-svg-wrap">
            ${svgHtml}
          </div>
          <div class="custom-icon-item-texts">
            <div class="custom-icon-item-name">${icon.name}</div>
            <div class="custom-icon-item-desc">${icon.desc}</div>
          </div>
        </div>
        <div class="custom-icon-item-meta">
          <span class="custom-icon-item-badge">${icon.category_name || icon.category}</span>
          ${isSelected ? `<span class="custom-icon-check">✓</span>` : ""}
        </div>
      `;

      item.addEventListener("click", (e) => {
        e.stopPropagation();
        this.selectIcon(icon.id);
      });

      this.optionsList.appendChild(item);
    });
  }

  selectIcon(iconId) {
    this.selectElem.value = iconId;
    this.updateFromSelect();
    this.closeMenu();

    const event = new Event("change", { bubbles: true });
    this.selectElem.dispatchEvent(event);

    if (this.onIconChange) this.onIconChange(iconId);
  }
}


// ==============================================================================
// 1. INIZIALIZZAZIONE APPLICAZIONE
// ==============================================================================
document.addEventListener("DOMContentLoaded", () => {
  ToastManager.init();

  const viewer = new ModelViewer("canvas-container");
  let debounceTimer = null;
  let isRequestPending = false;
  let currentProduct = "keychain"; // "keychain" | "desk_sign"

  function safeAddListener(el, evt, handler) {
    if (el) el.addEventListener(evt, handler);
  }

  // Preset Palettes U1
  const PALETTE_PRESETS = {
    snapmaker: ["#161616", "#ffffff", "#e31b23", "#ffd400"],
    sunset: ["#1c120c", "#ff7b00", "#ffd700", "#e63946"],
    cyberpunk: ["#0e111a", "#00f5d4", "#f72585", "#7b2cbf"],
    forest: ["#18231c", "#84a98c", "#52796f", "#cad2c5"],
  };

  // --- Elementi Switcher Prodotto ---
  const tabKeychain = document.getElementById("tabKeychain");
  const tabDeskSign = document.getElementById("tabDeskSign");
  const headerTabKeychain = document.getElementById("headerTabKeychain");
  const headerTabDeskSign = document.getElementById("headerTabDeskSign");

  // --- Elementi Portachiavi (Keychain) ---
  const textInput = document.getElementById("textInput");
  const fontSelect = document.getElementById("fontSelect");
  const iconSelect = document.getElementById("iconSelect");
  const btnUploadFont = document.getElementById("btnUploadFont");
  const fontFileInput = document.getElementById("fontFileInput");
  const fontUploadStatus = document.getElementById("fontUploadStatus");

  const fontSizeInput = document.getElementById("fontSizeInput");
  const fontSizeVal = document.getElementById("fontSizeVal");
  const letterSpacingInput = document.getElementById("letterSpacingInput");
  const letterSpacingVal = document.getElementById("letterSpacingVal");

  const iconOptionsWrap = document.getElementById("iconOptionsWrap");
  const extruderIconSelect = document.getElementById("extruderIconSelect");

  const baseThicknessInput = document.getElementById("baseThicknessInput");
  const baseThicknessVal = document.getElementById("baseThicknessVal");
  const cornerRadiusInput = document.getElementById("cornerRadiusInput");
  const cornerRadiusVal = document.getElementById("cornerRadiusVal");
  const paddingXInput = document.getElementById("paddingXInput");
  const paddingXVal = document.getElementById("paddingXVal");
  const paddingYInput = document.getElementById("paddingYInput");
  const paddingYVal = document.getElementById("paddingYVal");

  const textThicknessInput = document.getElementById("textThicknessInput");
  const textThicknessVal = document.getElementById("textThicknessVal");

  const holeToggle = document.getElementById("holeToggle");
  const holeDiameterInput = document.getElementById("holeDiameterInput");
  const holeDiameterVal = document.getElementById("holeDiameterVal");
  const holeOptionsWrap = document.getElementById("holeOptionsWrap");
  const extruderTextSelect = document.getElementById("extruderTextSelect");

  // --- Elementi Targhetta da Tavolo (Desk Sign) ---
  const dsWedgeAngleGroup = document.getElementById("dsWedgeAngleGroup");
  const dsWedgeAngleInput = document.getElementById("dsWedgeAngleInput");
  const dsWedgeAngleVal = document.getElementById("dsWedgeAngleVal");
  const dsBaseThicknessInput = document.getElementById("dsBaseThicknessInput");
  const dsBaseThicknessVal = document.getElementById("dsBaseThicknessVal");
  const dsPaddingXInput = document.getElementById("dsPaddingXInput");
  const dsPaddingXVal = document.getElementById("dsPaddingXVal");
  const dsPaddingYInput = document.getElementById("dsPaddingYInput");
  const dsPaddingYVal = document.getElementById("dsPaddingYVal");

  const dsText1Input = document.getElementById("dsText1Input");
  const dsFont1Select = document.getElementById("dsFont1Select");
  const dsFontSize1Input = document.getElementById("dsFontSize1Input");
  const dsFontSize1Val = document.getElementById("dsFontSize1Val");
  const dsThickness1Input = document.getElementById("dsThickness1Input");
  const dsThickness1Val = document.getElementById("dsThickness1Val");
  const dsExtruderLine1Select = document.getElementById("dsExtruderLine1Select");

  const dsLine2Toggle = document.getElementById("dsLine2Toggle");
  const dsLine2Wrap = document.getElementById("dsLine2Wrap");
  const dsText2Input = document.getElementById("dsText2Input");
  const dsFont2Select = document.getElementById("dsFont2Select");
  const dsFontSize2Input = document.getElementById("dsFontSize2Input");
  const dsFontSize2Val = document.getElementById("dsFontSize2Val");
  const dsLineSpacingInput = document.getElementById("dsLineSpacingInput");
  const dsLineSpacingVal = document.getElementById("dsLineSpacingVal");
  const dsThickness2Input = document.getElementById("dsThickness2Input");
  const dsThickness2Val = document.getElementById("dsThickness2Val");
  const dsExtruderLine2Select = document.getElementById("dsExtruderLine2Select");

  const dsBorderToggle = document.getElementById("dsBorderToggle");
  const dsBorderWrap = document.getElementById("dsBorderWrap");
  const dsBorderWidthInput = document.getElementById("dsBorderWidthInput");
  const dsBorderWidthVal = document.getElementById("dsBorderWidthVal");
  const dsBorderThicknessInput = document.getElementById("dsBorderThicknessInput");
  const dsBorderThicknessVal = document.getElementById("dsBorderThicknessVal");
  const dsCornerRadiusInput = document.getElementById("dsCornerRadiusInput");
  const dsCornerRadiusVal = document.getElementById("dsCornerRadiusVal");
  const dsExtruderBorderSelect = document.getElementById("dsExtruderBorderSelect");

  // --- Elementi Comuni: Palette & Toolbar ---
  const extruderBaseSelect = document.getElementById("extruderBaseSelect");
  const colorT0 = document.getElementById("colorT0");
  const colorT1 = document.getElementById("colorT1");
  const colorT2 = document.getElementById("colorT2");
  const colorT3 = document.getElementById("colorT3");

  const btnGenerate = document.getElementById("btnGenerate");
  const dimWidth = document.getElementById("dimWidth");
  const dimHeight = document.getElementById("dimHeight");
  const dimDepth = document.getElementById("dimDepth");
  const statusPill = document.getElementById("statusPill");
  const statusDot = statusPill ? statusPill.querySelector(".status-dot") : null;
  const statusText = document.getElementById("statusText");

  // ==========================================
  // 1.1 GESTIONE SELETTORE PRODOTTO (TABS)
  // ==========================================
  function setProduct(product) {
    currentProduct = product;
    if (product === "desk_sign") {
      if (tabDeskSign) tabDeskSign.classList.add("active");
      if (tabKeychain) tabKeychain.classList.remove("active");
      if (headerTabDeskSign) headerTabDeskSign.classList.add("active");
      if (headerTabKeychain) headerTabKeychain.classList.remove("active");
      document.body.classList.add("mode-desksign");
    } else {
      if (tabKeychain) tabKeychain.classList.add("active");
      if (tabDeskSign) tabDeskSign.classList.remove("active");
      if (headerTabKeychain) headerTabKeychain.classList.add("active");
      if (headerTabDeskSign) headerTabDeskSign.classList.remove("active");
      document.body.classList.remove("mode-desksign");
    }
    triggerPreview(true);
  }

  safeAddListener(tabKeychain, "click", () => setProduct("keychain"));
  safeAddListener(tabDeskSign, "click", () => setProduct("desk_sign"));
  safeAddListener(headerTabKeychain, "click", () => setProduct("keychain"));
  safeAddListener(headerTabDeskSign, "click", () => setProduct("desk_sign"));

  // ==============================================================================
  // 1.2 CONFIGURAZIONE DINAMICA API_BASE_URL (Supporto Localhost, Vercel & Render)
  // ==============================================================================
  const btnApiSettings = document.getElementById("btnApiSettings");
  const apiStatusDot = document.getElementById("apiStatusDot");
  const apiStatusLabel = document.getElementById("apiStatusLabel");
  const DEFAULT_PRODUCTION_API = "https://snapmaker-u1-backend.onrender.com";

  function determineApiBaseUrl() {
    const metaTag = document.querySelector('meta[name="api-base-url"]');
    if (metaTag && metaTag.content && metaTag.content.trim() !== "") {
      return metaTag.content.trim().replace(/\/$/, "");
    }
    if (window.API_BASE_URL) {
      return window.API_BASE_URL.replace(/\/$/, "");
    }
    const saved = localStorage.getItem("snapmaker_u1_api_url");
    if (saved && saved.trim() !== "") {
      return saved.trim().replace(/\/$/, "");
    }
    const isLocal = window.location.hostname === "localhost" ||
                    window.location.hostname === "127.0.0.1";
    if (isLocal) {
      if (window.location.port !== "8000" && window.location.port !== "") {
        return "http://localhost:8000";
      }
      return "";
    }
    return DEFAULT_PRODUCTION_API;
  }

  let API_BASE_URL = determineApiBaseUrl();

  async function checkApiHealth() {
    if (apiStatusLabel) apiStatusLabel.textContent = "API: Verifica...";
    if (apiStatusDot) apiStatusDot.className = "api-status-dot";

    try {
      const url = `${API_BASE_URL}/api/health`;
      const res = await fetch(url, { method: "GET" });
      if (res.ok) {
        if (apiStatusDot) apiStatusDot.className = "api-status-dot online";
        let displayHost = "Localhost:8000";
        if (API_BASE_URL) {
          try {
            displayHost = new URL(API_BASE_URL).hostname;
          } catch {
            displayHost = API_BASE_URL;
          }
        }
        if (apiStatusLabel) apiStatusLabel.textContent = `API: Online (${displayHost})`;
      } else {
        throw new Error("HTTP " + res.status);
      }
    } catch (err) {
      if (apiStatusDot) apiStatusDot.className = "api-status-dot offline";
      if (apiStatusLabel) apiStatusLabel.textContent = "API: Offline / Standby";
    }
  }

  safeAddListener(btnApiSettings, "click", () => {
    const current = API_BASE_URL || "(Relativo / Localhost:8000)";
    const input = prompt(
      "Configura l'endpoint Backend API per Snapmaker U1:\n" +
      "- In locale: http://localhost:8000\n" +
      "- Su Render/Railway: https://tuo-servizio.onrender.com\n\n" +
      "URL attuale: " + current,
      API_BASE_URL
    );
    if (input !== null) {
      const cleaned = input.trim().replace(/\/$/, "");
      if (cleaned) {
        localStorage.setItem("snapmaker_u1_api_url", cleaned);
        API_BASE_URL = cleaned;
      } else {
        localStorage.removeItem("snapmaker_u1_api_url");
        API_BASE_URL = determineApiBaseUrl();
      }
      checkApiHealth();
      loadFonts();
    }
  });

  checkApiHealth();

  // ==========================================
  // 2. INIZIALIZZAZIONE CUSTOM FONT DROPDOWNS
  // ==========================================
  function populateSelectOptions(selectElem, fonts, selectedId) {
    if (!selectElem) return;
    const prevVal = selectElem.value || selectedId || "Arial";
    selectElem.innerHTML = "";
    fonts.forEach((f) => {
      const opt = document.createElement("option");
      opt.value = f.id;
      opt.textContent = f.name;
      if (f.path) opt.dataset.path = f.path;
      if (f.id === prevVal) opt.selected = true;
      selectElem.appendChild(opt);
    });
  }

  // Popola immediatamente con i font di default
  populateSelectOptions(fontSelect, globalFontsList, "Anton");
  populateSelectOptions(dsFont1Select, globalFontsList, "Anton");
  populateSelectOptions(dsFont2Select, globalFontsList, "Montserrat");

  // Inizializza i 3 custom dropdown font
  const dropdownKeychain = fontSelect ? new CustomFontDropdown(fontSelect, () => triggerPreview(true)) : null;
  const dropdownDs1 = dsFont1Select ? new CustomFontDropdown(dsFont1Select, () => triggerPreview(true)) : null;
  const dropdownDs2 = dsFont2Select ? new CustomFontDropdown(dsFont2Select, () => triggerPreview(true)) : null;

  // Inizializza custom dropdown icona vettoriale
  function populateIconOptions(selectElem, icons, selectedId) {
    if (!selectElem) return;
    const prevVal = selectElem.value || selectedId || "none";
    selectElem.innerHTML = "";
    icons.forEach((icon) => {
      const opt = document.createElement("option");
      opt.value = icon.id;
      opt.textContent = `${icon.id === "none" ? "❌ " : ""}${icon.name}`;
      if (icon.id === prevVal) opt.selected = true;
      selectElem.appendChild(opt);
    });
  }

  populateIconOptions(iconSelect, globalIconsList, "none");
  const dropdownIcon = iconSelect ? new CustomIconDropdown(iconSelect, (iconId) => {
    if (iconOptionsWrap) {
      iconOptionsWrap.style.display = (iconId && iconId !== "none") ? "flex" : "none";
    }
    triggerPreview(true);
  }) : null;

  function refreshAllDropdowns() {
    if (dropdownKeychain) {
      dropdownKeychain.updateFromSelect();
      dropdownKeychain.renderOptions();
    }
    if (dropdownDs1) {
      dropdownDs1.updateFromSelect();
      dropdownDs1.renderOptions();
    }
    if (dropdownDs2) {
      dropdownDs2.updateFromSelect();
      dropdownDs2.renderOptions();
    }
  }

  function loadFonts(selectedId = null) {
    fetch(`${API_BASE_URL}/api/fonts`)
      .then((res) => {
        if (!res.ok) throw new Error("Status " + res.status);
        return res.json();
      })
      .then((fonts) => {
        if (Array.isArray(fonts) && fonts.length > 0) {
          globalFontsList = fonts;
          populateSelectOptions(fontSelect, globalFontsList, selectedId || fontSelect?.value || "Anton");
          populateSelectOptions(dsFont1Select, globalFontsList, dsFont1Select?.value || "Anton");
          populateSelectOptions(dsFont2Select, globalFontsList, dsFont2Select?.value || "Montserrat");
          refreshAllDropdowns();
          triggerPreview(true);
        }
      })
      .catch(() => {
        // Fallback tranquillo sui font integrati
        refreshAllDropdowns();
        triggerPreview(true);
      });
  }

  // Caricamento asincrono icone dal backend (opzionale)
  function loadIcons() {
    fetch(`${API_BASE_URL}/api/icons`)
      .then((res) => {
        if (!res.ok) throw new Error("Status " + res.status);
        return res.json();
      })
      .then((icons) => {
        if (Array.isArray(icons) && icons.length > 0) {
          globalIconsList = icons;
          populateIconOptions(iconSelect, globalIconsList, iconSelect?.value || "none");
          if (dropdownIcon) {
            dropdownIcon.updateFromSelect();
            dropdownIcon.renderOptions();
          }
        }
      })
      .catch(() => {});
  }
  loadIcons();

  // Caricamento asincrono font dal backend
  loadFonts();

  // Upload Font .ttf / .otf
  safeAddListener(btnUploadFont, "click", () => {
    if (fontFileInput) fontFileInput.click();
  });

  safeAddListener(fontFileInput, "change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    if (fontUploadStatus) {
      fontUploadStatus.style.display = "block";
      fontUploadStatus.style.color = "#ffa502";
      fontUploadStatus.textContent = "Caricamento font in corso...";
    }

    try {
      const res = await fetch(`${API_BASE_URL}/api/fonts/upload`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Errore upload font");
      }

      const data = await res.json();
      if (fontUploadStatus) {
        fontUploadStatus.style.color = "#2ed573";
        fontUploadStatus.textContent = `✓ Font ${file.name} caricato e pronto!`;
      }

      ToastManager.show({
        type: "success",
        title: "Font Caricato",
        message: `Il font "${file.name}" è stato aggiunto con successo.`,
      });

      loadFonts(data.font.id);
    } catch (err) {
      if (fontUploadStatus) {
        fontUploadStatus.style.color = "#ff4757";
        fontUploadStatus.textContent = `Errore: ${err.message}`;
      }
      ToastManager.show({
        type: "error",
        title: "Errore Caricamento Font",
        message: err.message,
      });
    }
  });

  // ==========================================
  // 3. PRESET PALETTE & COLORI
  // ==========================================
  document.querySelectorAll(".preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const presetKey = btn.dataset.preset;
      const colors = PALETTE_PRESETS[presetKey];
      if (colors) {
        if (colorT0) colorT0.value = colors[0];
        if (colorT1) colorT1.value = colors[1];
        if (colorT2) colorT2.value = colors[2];
        if (colorT3) colorT3.value = colors[3];
        onPaletteChange();
      }
    });
  });

  function onPaletteChange() {
    const c0 = colorT0 ? colorT0.value : "#161616";
    const c1 = colorT1 ? colorT1.value : "#ffffff";
    const c2 = colorT2 ? colorT2.value : "#e31b23";
    const c3 = colorT3 ? colorT3.value : "#ffd400";
    viewer.updateColors([c0, c1, c2, c3]);
  }

  safeAddListener(colorT0, "input", onPaletteChange);
  safeAddListener(colorT1, "input", onPaletteChange);
  safeAddListener(colorT2, "input", onPaletteChange);
  safeAddListener(colorT3, "input", onPaletteChange);

  // ==========================================
  // 4. EVENT LISTENERS DINAMICI
  // ==========================================
  // Portachiavi Icone
  safeAddListener(iconSelect, "change", (e) => {
    const val = e.target.value;
    if (iconOptionsWrap) {
      iconOptionsWrap.style.display = (val && val !== "none") ? "flex" : "none";
    }
    triggerPreview(true);
  });

  document.querySelectorAll('input[name="iconPos"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });

  safeAddListener(extruderIconSelect, "change", () => triggerPreview(true));

  // Portachiavi Slider
  safeAddListener(textInput, "input", () => triggerPreview(false));
  safeAddListener(fontSelect, "change", () => triggerPreview(true));

  safeAddListener(fontSizeInput, "input", (e) => {
    if (fontSizeVal) fontSizeVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(letterSpacingInput, "input", (e) => {
    if (letterSpacingVal) letterSpacingVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(baseThicknessInput, "input", (e) => {
    if (baseThicknessVal) baseThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(cornerRadiusInput, "input", (e) => {
    if (cornerRadiusVal) cornerRadiusVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(paddingXInput, "input", (e) => {
    if (paddingXVal) paddingXVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(paddingYInput, "input", (e) => {
    if (paddingYVal) paddingYVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(textThicknessInput, "input", (e) => {
    if (textThicknessVal) textThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(holeDiameterInput, "input", (e) => {
    if (holeDiameterVal) holeDiameterVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(holeToggle, "change", (e) => {
    if (holeOptionsWrap) holeOptionsWrap.style.display = e.target.checked ? "flex" : "none";
    triggerPreview(true);
  });

  document.querySelectorAll('input[name="baseStyle"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });
  document.querySelectorAll('input[name="textMode"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });
  document.querySelectorAll('input[name="holePos"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });
  safeAddListener(extruderBaseSelect, "change", () => triggerPreview(true));
  safeAddListener(extruderTextSelect, "change", () => triggerPreview(true));

  // --- Targhetta da Tavolo (Desk Sign) Event Listeners ---
  document.querySelectorAll('input[name="dsBaseMode"]').forEach((r) => {
    r.addEventListener("change", (e) => {
      if (dsWedgeAngleGroup) dsWedgeAngleGroup.style.display = e.target.value === "wedge" ? "flex" : "none";
      triggerPreview(true);
    });
  });

  safeAddListener(dsWedgeAngleInput, "input", (e) => {
    if (dsWedgeAngleVal) dsWedgeAngleVal.textContent = `${e.target.value}°`;
    triggerPreview(false);
  });
  safeAddListener(dsBaseThicknessInput, "input", (e) => {
    if (dsBaseThicknessVal) dsBaseThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsPaddingXInput, "input", (e) => {
    if (dsPaddingXVal) dsPaddingXVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsPaddingYInput, "input", (e) => {
    if (dsPaddingYVal) dsPaddingYVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });

  safeAddListener(dsText1Input, "input", () => triggerPreview(false));
  safeAddListener(dsFont1Select, "change", () => triggerPreview(true));
  safeAddListener(dsFontSize1Input, "input", (e) => {
    if (dsFontSize1Val) dsFontSize1Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsThickness1Input, "input", (e) => {
    if (dsThickness1Val) dsThickness1Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsExtruderLine1Select, "change", () => triggerPreview(true));

  safeAddListener(dsLine2Toggle, "change", (e) => {
    if (dsLine2Wrap) dsLine2Wrap.style.display = e.target.checked ? "flex" : "none";
    triggerPreview(true);
  });
  safeAddListener(dsText2Input, "input", () => triggerPreview(false));
  safeAddListener(dsFont2Select, "change", () => triggerPreview(true));
  safeAddListener(dsFontSize2Input, "input", (e) => {
    if (dsFontSize2Val) dsFontSize2Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsLineSpacingInput, "input", (e) => {
    if (dsLineSpacingVal) dsLineSpacingVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsThickness2Input, "input", (e) => {
    if (dsThickness2Val) dsThickness2Val.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsExtruderLine2Select, "change", () => triggerPreview(true));

  safeAddListener(dsBorderToggle, "change", (e) => {
    if (dsBorderWrap) dsBorderWrap.style.display = e.target.checked ? "flex" : "none";
    triggerPreview(true);
  });
  document.querySelectorAll('input[name="dsTextAlign"]').forEach((r) => {
    r.addEventListener("change", () => triggerPreview(true));
  });
  safeAddListener(dsBorderWidthInput, "input", (e) => {
    if (dsBorderWidthVal) dsBorderWidthVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsBorderThicknessInput, "input", (e) => {
    if (dsBorderThicknessVal) dsBorderThicknessVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsCornerRadiusInput, "input", (e) => {
    if (dsCornerRadiusVal) dsCornerRadiusVal.textContent = `${e.target.value} mm`;
    triggerPreview(false);
  });
  safeAddListener(dsExtruderBorderSelect, "change", () => triggerPreview(true));

  // ==========================================
  // 5. RACCOLTA PARAMETRI PER L'API
  // ==========================================
  function getParams() {
    const palette = [
      colorT0 ? colorT0.value : "#161616",
      colorT1 ? colorT1.value : "#ffffff",
      colorT2 ? colorT2.value : "#e31b23",
      colorT3 ? colorT3.value : "#ffd400",
    ];
    const baseExtruder = extruderBaseSelect ? parseInt(extruderBaseSelect.value) : 0;

    if (currentProduct === "desk_sign") {
      const baseMode = document.querySelector('input[name="dsBaseMode"]:checked')?.value || "wedge";
      const textAlign = document.querySelector('input[name="dsTextAlign"]:checked')?.value || "center";
      const font1Opt = dsFont1Select ? dsFont1Select.options[dsFont1Select.selectedIndex] : null;
      const font2Opt = dsFont2Select ? dsFont2Select.options[dsFont2Select.selectedIndex] : null;

      return {
        generator: "desk_sign",
        base_mode: baseMode,
        wedge_angle: dsWedgeAngleInput ? parseFloat(dsWedgeAngleInput.value) : 45.0,
        base_thickness: dsBaseThicknessInput ? parseFloat(dsBaseThicknessInput.value) : 3.0,
        corner_radius: dsCornerRadiusInput ? parseFloat(dsCornerRadiusInput.value) : 3.0,
        padding_x: dsPaddingXInput ? parseFloat(dsPaddingXInput.value) : 8.0,
        padding_y: dsPaddingYInput ? parseFloat(dsPaddingYInput.value) : 6.0,
        line_spacing: dsLineSpacingInput ? parseFloat(dsLineSpacingInput.value) : 3.5,
        text_align: textAlign,
        text_line1: dsText1Input ? dsText1Input.value.trim() || "STUDIO U1" : "STUDIO U1",
        font_family_line1: dsFont1Select ? dsFont1Select.value || "Anton" : "Anton",
        font_path_line1: font1Opt?.dataset?.path || null,
        font_size_line1: dsFontSize1Input ? parseFloat(dsFontSize1Input.value) : 14.0,
        thickness_line1: dsThickness1Input ? parseFloat(dsThickness1Input.value) : 1.2,
        extruder_line1: dsExtruderLine1Select ? parseInt(dsExtruderLine1Select.value) : 1,
        line2_enabled: dsLine2Toggle ? dsLine2Toggle.checked : false,
        text_line2: dsText2Input ? dsText2Input.value.trim() : "",
        font_family_line2: dsFont2Select ? dsFont2Select.value || "Montserrat" : "Montserrat",
        font_path_line2: font2Opt?.dataset?.path || null,
        font_size_line2: dsFontSize2Input ? parseFloat(dsFontSize2Input.value) : 7.5,
        thickness_line2: dsThickness2Input ? parseFloat(dsThickness2Input.value) : 1.0,
        extruder_line2: dsExtruderLine2Select ? parseInt(dsExtruderLine2Select.value) : 2,
        border_enabled: dsBorderToggle ? dsBorderToggle.checked : true,
        border_width: dsBorderWidthInput ? parseFloat(dsBorderWidthInput.value) : 2.0,
        border_thickness: dsBorderThicknessInput ? parseFloat(dsBorderThicknessInput.value) : 1.0,
        extruder_border: dsExtruderBorderSelect ? parseInt(dsExtruderBorderSelect.value) : 3,
        extruder_base: baseExtruder,
        filament_colors: palette,
      };
    } else {
      // Template Keychain
      const baseStyle = document.querySelector('input[name="baseStyle"]:checked')?.value || "rectangle";
      const textMode = document.querySelector('input[name="textMode"]:checked')?.value || "embossed";
      const holePos = document.querySelector('input[name="holePos"]:checked')?.value || "left";
      const iconName = iconSelect ? iconSelect.value : "none";
      const iconPos = document.querySelector('input[name="iconPos"]:checked')?.value || "left";
      const selectedFontOpt = fontSelect ? fontSelect.options[fontSelect.selectedIndex] : null;
      const textExtruder = extruderTextSelect ? parseInt(extruderTextSelect.value) : 1;
      let iconExtruder = extruderIconSelect ? parseInt(extruderIconSelect.value) : -1;
      if (iconExtruder === -1) iconExtruder = textExtruder;

      return {
        generator: "keychain",
        text: textInput ? textInput.value.trim() || "NOME" : "NOME",
        font_family: fontSelect ? fontSelect.value || "Anton" : "Anton",
        font_path: selectedFontOpt?.dataset?.path || null,
        font_size: fontSizeInput ? parseFloat(fontSizeInput.value) : 14.0,
        letter_spacing: letterSpacingInput ? parseFloat(letterSpacingInput.value) : 0.0,
        base_style: baseStyle,
        base_thickness: baseThicknessInput ? parseFloat(baseThicknessInput.value) : 2.4,
        text_thickness: textThicknessInput ? parseFloat(textThicknessInput.value) : 1.2,
        text_mode: textMode,
        corner_radius: cornerRadiusInput ? parseFloat(cornerRadiusInput.value) : 4.0,
        padding_x: paddingXInput ? parseFloat(paddingXInput.value) : 5.0,
        padding_y: paddingYInput ? parseFloat(paddingYInput.value) : 4.5,
        hole_enabled: holeToggle ? holeToggle.checked : true,
        hole_position: holePos,
        hole_diameter: holeDiameterInput ? parseFloat(holeDiameterInput.value) : 5.0,
        icon_name: iconName,
        icon_position: iconPos,
        extruder_base: baseExtruder,
        extruder_text: textExtruder,
        extruder_icon: iconExtruder,
        filament_colors: palette,
      };
    }
  }

  // ==========================================
  // 6. CHIAMATA ANTEPRIMA CON DEBOUNCE
  // ==========================================
  function triggerPreview(immediate = false) {
    if (debounceTimer) clearTimeout(debounceTimer);

    if (immediate) {
      executePreview();
    } else {
      if (statusDot) statusDot.classList.add("busy");
      if (statusText) statusText.textContent = "Modifica in corso...";
      debounceTimer = setTimeout(executePreview, 260);
    }
  }

  async function executePreview() {
    const params = getParams();
    if (statusDot) statusDot.classList.add("busy");
    if (statusText) statusText.textContent = "Calcolo geometria 3D...";
    isRequestPending = true;

    try {
      const response = await fetch(`${API_BASE_URL}/api/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || "Errore di anteprima geometria.");
      }

      const data = await response.json();
      viewer.updateGeometry(
        data,
        params.filament_colors,
        params.extruder_base,
        params.extruder_text !== undefined ? params.extruder_text : params.extruder_line1
      );

      if (data.dimensions) {
        if (dimWidth) dimWidth.textContent = `${data.dimensions.width} mm`;
        if (dimHeight) dimHeight.textContent = `${data.dimensions.height} mm`;
        if (dimDepth) dimDepth.textContent = `${data.dimensions.depth} mm`;
      }

      if (statusDot) statusDot.classList.remove("busy");
      if (statusText) statusText.textContent = "Pronto per la stampa";
    } catch (error) {
      console.error("Preview error:", error);
      if (statusDot) statusDot.classList.remove("busy");
      if (statusText) statusText.textContent = "Errore di calcolo";
    } finally {
      isRequestPending = false;
    }
  }

  // ==========================================
  // 7. TOOLBAR CAMERA & WIREFRAME
  // ==========================================
  const btnResetView = document.getElementById("btnResetView");
  const btnTopView = document.getElementById("btnTopView");
  const btnFrontView = document.getElementById("btnFrontView");
  const btnWireframe = document.getElementById("btnWireframe");

  safeAddListener(btnResetView, "click", () => viewer.resetView());
  safeAddListener(btnTopView, "click", () => viewer.topView());
  safeAddListener(btnFrontView, "click", () => viewer.frontView());
  safeAddListener(btnWireframe, "click", function () {
    const isWire = viewer.toggleWireframe();
    this.classList.toggle("active", isWire);
  });

  // ==========================================
  // 8. DOWNLOAD 3MF NATIVO PER SNAPMAKER U1
  // ==========================================
  if (btnGenerate) {
    btnGenerate.addEventListener("click", async () => {
      const params = getParams();

      // Disabilita pulsante e attiva spinner
      btnGenerate.disabled = true;
      btnGenerate.classList.add("loading");
      btnGenerate.innerHTML = `<span class="spinner"></span> Preparazione 3MF...`;

      if (statusText) statusText.textContent = "Compilazione pacchetto 3MF in corso...";

      // Timer di Cold Start (se Render free tier è in standby e richiede ~30s per risvegliarsi)
      let coldStartNotice = null;
      const coldStartTimer = setTimeout(() => {
        coldStartNotice = ToastManager.show({
          type: "warning",
          title: "Risveglio Server Cloud (Render Free Tier)",
          message: "Il backend cloud si sta avviando dallo standby. Può richiedere ~30-40 secondi per il primo caricamento. Attendere...",
          duration: 0, // Rimane finché non risponde
        });
      }, 3500);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minuti timeout massimo

      try {
        const response = await fetch(`${API_BASE_URL}/api/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params),
          signal: controller.signal,
        });

        clearTimeout(coldStartTimer);
        clearTimeout(timeoutId);
        if (coldStartNotice) ToastManager.dismiss(coldStartNotice);

        if (!response.ok) {
          let errDetail = `Errore HTTP ${response.status}`;
          try {
            const errJson = await response.json();
            if (errJson && errJson.detail) errDetail = errJson.detail;
          } catch {
            const errText = await response.text();
            if (errText) errDetail = errText;
          }
          throw new Error(errDetail);
        }

        // Nome file coerente
        const disposition = response.headers.get("Content-Disposition");
        let rawName = currentProduct === "desk_sign" ? params.text_line1 : params.text;
        let cleanName = (rawName || "Model").replace(/[^a-zA-Z0-9_\-]/g, "_").trim() || "Model";

        let filename = currentProduct === "desk_sign"
          ? `targhetta_snapmaker_u1_${cleanName}.3mf`
          : `portachiavi_snapmaker_u1_${cleanName}.3mf`;

        if (disposition && disposition.indexOf("filename=") !== -1) {
          const matches = /filename="?([^"]+)"?/.exec(disposition);
          if (matches != null && matches[1]) {
            filename = matches[1];
          }
        }

        // Download automatico Blob
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.style.display = "none";
        a.href = downloadUrl;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(downloadUrl);

        if (statusText) statusText.textContent = "✓ 3MF scaricato!";

        ToastManager.show({
          type: "success",
          title: "Download Completato",
          message: `Il file "${filename}" è pronto per lo slicing su Snapmaker Orca.`,
          duration: 6000,
        });
      } catch (err) {
        clearTimeout(coldStartTimer);
        clearTimeout(timeoutId);
        if (coldStartNotice) ToastManager.dismiss(coldStartNotice);

        console.error("Errore generazione 3MF:", err);

        let userMsg = err.message;
        if (err.name === "AbortError") {
          userMsg = "La richiesta al server è scaduta (timeout). Riprova tra pochi istanti.";
        } else if (err.message && err.message.includes("Failed to fetch")) {
          userMsg = "Impossibile contattare il server cloud. Verifica la connessione o prova a riconnettere l'API dal pulsante in alto.";
        }

        ToastManager.show({
          type: "error",
          title: "Errore Generazione 3MF",
          message: userMsg,
          duration: 8000,
        });

        if (statusText) statusText.textContent = "Errore durante il download";
      } finally {
        btnGenerate.disabled = false;
        btnGenerate.classList.remove("loading");
        btnGenerate.innerHTML = `
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
          </svg>
          SCARICA 3MF PER SNAPMAKER U1
        `;
      }
    });
  }
});
