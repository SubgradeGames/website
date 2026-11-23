// Main page behaviour: hero parallax, clip gallery, devlog list.
// The page works without this file; each feature only adds to it.
(function () {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
    const MOUSE = 'mouse';

    // Devlog filter: "all" matches every row. URL keys keep a view shareable, e.g. "?tag=art&page=2".
    const ALL = 'all';
    const TAG_KEY = 'tag';
    const PAGE_KEY = 'page';

    initTilt();
    initClips();
    initDevlog();

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

                // Template from _data/home.yml. Example: "Clip {index} of {count} · {name}" -> "Clip 2 of 4 · Getting started".
                caption.textContent = strip.dataset.template
                    .replace('{index}', index + 1)
                    .replace('{count}', thumbs.length)
                    .replace('{name}', thumb.dataset.name);
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

    // Devlog list: one game or tag filter, then pages of data-per-page rows.
    // Without JS every row shows; chips and pager stay hidden.
    function initDevlog() {
        const list = document.getElementById('devlog-list');
        const pager = document.getElementById('devlog-pager');
        const filter = document.querySelector('.tag-filter');
        if (!list || !pager || !filter) {
            return;
        }

        const params = new URLSearchParams(location.search);
        const view = {
            list,
            pager,
            chips: filter.querySelectorAll('.tag-chip'),
            rows: Array.from(list.querySelectorAll('.log-row')),
            empty: document.getElementById('devlog-empty'),
            perPage: Number(list.dataset.perPage),
            tag: params.get(TAG_KEY) || ALL,
            page: Number(params.get(PAGE_KEY)) || 1,
        };

        // Unknown tag in the URL (e.g. renamed since shared): fall back to all.
        const known = Array.from(view.chips).some((chip) => chip.dataset.tag === view.tag);
        if (!known) {
            view.tag = ALL;
        }

        view.chips.forEach((chip) => {
            chip.addEventListener('click', () => {
                view.tag = chip.dataset.tag;
                view.page = 1;
                renderLog(view);
            });
        });

        pager.querySelectorAll('.pager-step').forEach((step) => {
            step.addEventListener('click', () => turnPage(view, view.page + Number(step.dataset.step)));
        });

        filter.hidden = false;
        renderLog(view);
    }

    function turnPage(view, page) {
        view.page = page;
        renderLog(view);

        // Long pages push the list top off screen; bring it back.
        const top = view.list.getBoundingClientRect().top;
        if (top < 0) {
            view.list.scrollIntoView({ behavior: reduced.matches ? 'auto' : 'smooth' });
        }
    }

    function renderLog(view) {
        const matches = view.rows.filter((row) => view.tag === ALL || row.dataset.tags.split(' ').includes(view.tag));
        const pages = Math.max(1, Math.ceil(matches.length / view.perPage));
        view.page = Math.min(Math.max(view.page, 1), pages);

        // Rows on this page: [from, to). Example: page 2 of 5 per page -> rows 5..9.
        const from = (view.page - 1) * view.perPage;
        const to = Math.min(from + view.perPage, matches.length);
        const shown = new Set(matches.slice(from, to));
        view.rows.forEach((row) => {
            row.hidden = !shown.has(row);
        });

        view.chips.forEach((chip) => {
            chip.setAttribute('aria-pressed', String(chip.dataset.tag === view.tag));
        });

        view.list.hidden = matches.length === 0;
        view.empty.hidden = matches.length > 0;
        renderPager(view, pages, from, to, matches.length);
        saveView(view);
    }

    function renderPager(view, pages, from, to, count) {
        const pager = view.pager;
        pager.hidden = count <= view.perPage;
        if (pager.hidden) {
            return;
        }

        const [prev, next] = pager.querySelectorAll('.pager-step');
        prev.disabled = view.page === 1;
        next.disabled = view.page === pages;

        const numbers = pager.querySelector('.pager-pages');
        numbers.replaceChildren();
        for (let page = 1; page <= pages; page++) {
            const button = document.createElement('button');
            button.type = 'button';
            button.textContent = page;
            if (page === view.page) {
                button.setAttribute('aria-current', 'page');
            }
            button.addEventListener('click', () => turnPage(view, page));

            const item = document.createElement('li');
            item.append(button);
            numbers.append(item);
        }

        // Template from _data/home.yml. Example: "{from}–{to} of {count}" -> "6–10 of 12".
        pager.querySelector('.pager-status').textContent = pager.dataset.template
            .replace('{from}', from + 1)
            .replace('{to}', to)
            .replace('{count}', count);
    }

    // Defaults stay out of the URL so the plain home link stays clean.
    function saveView(view) {
        const url = new URL(location.href);
        url.searchParams.delete(TAG_KEY);
        url.searchParams.delete(PAGE_KEY);

        if (view.tag !== ALL) {
            url.searchParams.set(TAG_KEY, view.tag);
        }
        if (view.page > 1) {
            url.searchParams.set(PAGE_KEY, view.page);
        }

        history.replaceState(null, '', url);
    }
})();
