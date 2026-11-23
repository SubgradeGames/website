// Main page sky: picks day, dusk or night from the visitor's clock.
// Loaded in <head> so the right sky paints first. Preview any sky with ?sky=night.
(function () {
    const Sky = Object.freeze({ day: 'day', dusk: 'dusk', night: 'night' });

    // Day 06:00-16:59, dusk 17:00-19:59, night otherwise. Example: 18:30 -> dusk.
    const DAWN_HOUR = 6;
    const DUSK_HOUR = 17;
    const NIGHT_HOUR = 20;
    const TICK_MS = 60 * 1000;
    const PREVIEW_PARAM = 'sky';

    function skyAt(hour) {
        if (hour >= DAWN_HOUR && hour < DUSK_HOUR) {
            return Sky.day;
        }

        if (hour >= DUSK_HOUR && hour < NIGHT_HOUR) {
            return Sky.dusk;
        }

        return Sky.night;
    }

    function preview() {
        const value = new URLSearchParams(window.location.search).get(PREVIEW_PARAM);
        return Object.values(Sky).includes(value) ? value : null;
    }

    // Set the sky on <html>.
    function paint() {
        const now = new Date();
        const forced = preview();
        const sky = forced || skyAt(now.getHours());

        document.documentElement.dataset.sky = sky;
    }

    paint();
    setInterval(paint, TICK_MS);
})();
