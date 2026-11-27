/**
 * Assets - where the files GameScene loads come from.
 *
 * Working on the game there is no build: every load is the file itself, and
 * `Assets.json` / `Assets.url` hand the path back (with a `?t=` cache-buster
 * where an edit must show on the next reload).
 *
 * The deployed game is built by tools/build_dist.js, which packs what the
 * scene loads into three content-hashed files named in `window.GAME_BUILD`:
 * one JSON file with every JSON file parsed (and an index of the other two),
 * and two binary files with the images and the NPC photos end to end.
 * GameScene downloads the packs and installs them here, and the same two
 * calls then return the parsed object and a `blob:` URL of the image's
 * bytes. Phaser's loader takes either, so texture keys, frames and
 * everything that reads them are the same in both.
 *
 * A file the packs do not have falls back to its path: the built site also
 * holds every loose file.
 *
 * Every image and JSON load in the scene goes through these two calls: the
 * build runs the scene's own preload() and queuePhotos() against a recording
 * copy of this class to decide what to pack, and refuses a load that did not
 * come through it (see "Loading and the deploy build" in docs/architecture.md).
 */
class Assets {
    /** path -> parsed JSON from the data pack; null in the unbuilt game and after release() */
    static files = null;
    /** the images pack: { index: path -> [offset, length], blob }, or null */
    static images = null;
    /** the photos pack, the same shape; its blob is null until installPhotos() */
    static photos = null;
    /** blob: URLs handed out and not yet revoked */
    static urls = [];

    /** What to give `load.json` for a JSON file: the parsed object from the pack, or its URL. */
    static json(path) {
        const data = Assets.files && Assets.files[path];
        return data || `${path}?t=${Date.now()}`;
    }

    /**
     * What to give `load.image` / `load.spritesheet` for an image: a blob: URL
     * of its bytes in a pack, or its path (`bust`: with a cache-buster, for
     * art that is replaced under the same name).
     */
    static url(path, bust = false) {
        for (const pack of [Assets.images, Assets.photos]) {
            const at = pack && pack.blob && pack.index[path];
            if (!at) continue;
            const url = URL.createObjectURL(pack.blob.slice(at[0], at[0] + at[1], 'image/png'));
            Assets.urls.push(url);
            return url;
        }
        return bust ? `${path}?t=${Date.now()}` : path;
    }

    /** Is this what tools/build_dist.js writes as the data pack? */
    static isDataPack(data) {
        const map = (v) => !!v && typeof v === 'object' && !Array.isArray(v);
        return map(data) && map(data.json) && map(data.images) && map(data.photos);
    }

    /**
     * Take the data pack (parsed) and the images pack (an ArrayBuffer).
     * False, and nothing installed, when the data is not a data pack.
     */
    static install(data, buffer) {
        if (!Assets.isDataPack(data) || !buffer) return false;
        Assets.files = data.json;
        Assets.images = { index: data.images, blob: new Blob([buffer]) };
        Assets.photos = { index: data.photos, blob: null };
        return true;
    }

    /**
     * Take the photos pack (an ArrayBuffer); its index came with the data
     * pack. Null when the pack could not be had: the photos are then the
     * loose files, and the index is let go of.
     */
    static installPhotos(buffer) {
        if (!Assets.photos) return;
        if (buffer) Assets.photos.blob = new Blob([buffer]);
        else Assets.photos = null;
    }

    /**
     * A load has finished: revoke the blob: URLs handed out and let go of the
     * packs. The photos index is kept until the photos pack has been
     * installed and used, since the photos load after the boot.
     */
    static release() {
        for (const url of Assets.urls) URL.revokeObjectURL(url);
        Assets.urls = [];
        Assets.files = null;
        Assets.images = null;
        if (Assets.photos && Assets.photos.blob) Assets.photos = null;
    }
}

if (typeof window !== 'undefined') window.Assets = Assets;
