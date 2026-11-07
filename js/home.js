// Main page behaviour: hero parallax, talking monk, clip gallery.
// The page works without this file; each feature only adds to it.
(function () {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const MOUSE = 'mouse';

    initTilt();
    initMonk();
    initClips();

    // Parallax: pointer position becomes --px/--py (-1..1); CSS scales it per layer.
    // Mouse only, one style write per frame.
    function initTilt() {
        const hero = document.getElementById('hero');
        if (!hero) {
            return;
        }

        let frame = 0;
        let tilt = { x: 0, y: 0 };

        hero.addEventListener('pointermove', (event) => {
            if (reduced.matches || event.pointerType !== MOUSE) {
                return;
            }

            const rect = hero.getBoundingClientRect();
            tilt = {
                x: ((event.clientX - rect.left) / rect.width) * 2 - 1,
                y: ((event.clientY - rect.top) / rect.height) * 2 - 1,
            };

            if (frame) {
                return;
            }

            frame = requestAnimationFrame(() => {
                frame = 0;
                setTilt(hero, tilt.x, tilt.y);
            });
        });

        hero.addEventListener('pointerleave', () => setTilt(hero, 0, 0));
    }

    function setTilt(hero, x, y) {
        hero.style.setProperty('--px', x.toFixed(3));
        hero.style.setProperty('--py', y.toFixed(3));
    }

    // Talking monk: each click moves to the next line from _data/home.yml.
    function initMonk() {
        const monk = document.getElementById('monk');
        const says = document.getElementById('monk-says');
        const data = document.getElementById('monk-quips');
        if (!monk || !says || !data) {
            return;
        }

        const quips = JSON.parse(data.textContent);
        let index = 0;

        monk.addEventListener('click', () => {
            index = (index + 1) % quips.length;
            says.textContent = quips[index];
        });
    }

    // Clip gallery: thumbnails swap the feature video. Reduced motion: no autoplay, show controls.
    function initClips() {
        document.querySelectorAll('[data-player]').forEach(initStrip);

        if (!reduced.matches) {
            return;
        }

        document.querySelectorAll('.feature-video').forEach((video) => {
            video.removeAttribute('autoplay');
            video.pause();
            video.controls = true;
        });
    }

    function initStrip(strip) {
        const video = document.getElementById(strip.dataset.player);
        const caption = document.getElementById(strip.dataset.caption);
        const thumbs = strip.querySelectorAll('.clip-thumb');
        if (!video) {
            return;
        }

        thumbs.forEach((thumb, index) => {
            thumb.addEventListener('click', () => {
                showClip(video, thumb);

                thumbs.forEach((other) => {
                    other.setAttribute('aria-pressed', String(other === thumb));
                });

                if (!caption) {
                    return;
                }

                caption.textContent = 'Clip ' + (index + 1) + ' of ' + thumbs.length + ' · ' + thumb.dataset.name;
            });
        });
    }

    function showClip(video, thumb) {
        video.poster = thumb.dataset.poster;
        video.src = thumb.dataset.video;
        video.setAttribute('aria-label', thumb.dataset.alt);

        if (reduced.matches) {
            return;
        }

        // Autoplay can be refused (e.g. data saver); the poster stays up.
        video.play().catch(() => {});
    }
})();
