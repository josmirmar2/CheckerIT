export const MUSIC_LIST = [
  'track-1.mp3',
  'track-2.mp3',
  'track-3.mp3',
  'track-4.mp3',
  'track-5.mp3',
  'track-6.mp3',
];

export const getRandomMusicIndex = (previousIndex = -1) => {
  let randomIndex;
  do {
    randomIndex = Math.floor(Math.random() * MUSIC_LIST.length);
  } while (randomIndex === previousIndex && MUSIC_LIST.length > 1);
  return randomIndex;
};
