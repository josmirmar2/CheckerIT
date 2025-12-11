// Lista de canciones locales
// Añade aquí los nombres de los archivos de audio que tengas en la carpeta music/
// Formatos soportados: .mp3, .ogg, .wav

export const MUSIC_LIST = [
  // Ejemplo: 'cancion1.mp3', 'cancion2.mp3', 'musica-fondo.ogg'
  // Añade tus archivos aquí
];

export const getRandomMusicIndex = (previousIndex = -1) => {
  let randomIndex;
  do {
    randomIndex = Math.floor(Math.random() * MUSIC_LIST.length);
  } while (randomIndex === previousIndex && MUSIC_LIST.length > 1);
  return randomIndex;
};
