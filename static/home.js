// The homepage uses a pre-composed 10 x 10 visual wall so the full 100-tile composition
// is stable, fast, and visually consistent on the first paint. The Discover page still
// loads live/fallback video metadata for interactive browsing.
(() => {
  const wall = document.querySelector('.thumbnail-wall');
  if (wall) wall.setAttribute('role', 'img');
})();
