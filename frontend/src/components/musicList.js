export const MUSIC_LIST = [
  'SQMgRfVbdVM',
  'seBb-E6kyYk',
  'm2uXML4wGkU',
  '5v9pfI2NLO4',
  'jmSr0SHOty8',
  'zuLfqdUFSqw',
  '-aiTrarsiro',
  '1hjAvRK8XHk',
];

export const getRandomMusicIndex = (previousIndex = -1) => {
  let randomIndex;
  do {
    randomIndex = Math.floor(Math.random() * MUSIC_LIST.length);
  } while (randomIndex === previousIndex && MUSIC_LIST.length > 1);
  return randomIndex;
};
