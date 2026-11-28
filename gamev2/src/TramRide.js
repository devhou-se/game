/**
 * TramRide — riding a streetcar (issue #245).
 *
 * A shuttle of src/AmbientTrams.js that is standing at a stop or a terminus is
 * solid, and the player who bumps it is on board. While riding, the player's
 * sprite is hidden and kept at the car's middle on the rail row, and `gridX` /
 * `gridY` are the cell under it - so the camera's follow, chunk streaming, the
 * district in the HUD and the map dot all go along without knowing. It is free.
 *
 * No new key: the menu (ESC) opens as ever, the direction keys do not walk, and
 * at a halt up / down gets off on that side of the street - on that side only.
 * A blocked side says so and keeps the rider: put off on the other side with
 * the key still held, they would walk straight back into the car and on board.
 */
class TramRide {
    constructor(scene) {
        this.scene = scene;
        this.car = null;            // the line state (AmbientTrams.lines[i]) being ridden: not its image, which a re-sent line replaces
        this.carried = false;       // the key that boarded is still down: it does not get off
        this.halted = false;        // the car was standing last frame
    }

    /** Is a car being ridden? */
    get riding() {
        return !!this.car;
    }

    /** The player bumped a cell: board the car standing on it. True when they did. */
    check(gridX, gridY) {
        const scene = this.scene;
        const car = scene.ambientTrams ? scene.ambientTrams.carAt(gridX, gridY) : null;
        if (!car || scene.roomManager.isTransitioning) return false;
        this.car = car;
        this.carried = true;
        this.halted = true;
        scene.player.sprite.setVisible(false);
        this.say(`On the ${car.line.name} · ↑/↓: get off at a stop`);
        this.update();
        return true;
    }

    /** Every frame (GameScene.update, after the cars have moved): the rider goes where the car is. */
    update() {
        const car = this.car;
        if (!car) return;
        const scene = this.scene, player = scene.player, GS = scene.GRID_SIZE;
        // the line was cleared or re-sent under the rider: the ride ends where they are
        if (!car.image || !car.plan) { this.end(); return; }
        player.sprite.setVisible(false);
        player.sprite.x = car.image.x + car.image.width / 2;
        player.sprite.y = (car.line.row + 0.5) * GS;
        player.gridX = Math.floor(player.sprite.x / GS);
        player.gridY = car.line.row;
        const halted = this.standing();
        if (halted && !this.halted) this.say('↑/↓: get off');
        this.halted = halted;
    }

    /** The direction keys while riding (InputHandler.routeInput), as InputHandler.heading(true) reads them. */
    handleInput(heading) {
        const out = TramRide.step(this.carried, heading, this.standing());
        this.carried = out.carried;
        if (out.side) this.alight(out.side);
    }

    /** Get off on `side` (-1 north, 1 south) of the standing car, onto the free cell nearest its middle. */
    alight(side) {
        const scene = this.scene, player = scene.player, GS = scene.GRID_SIZE, car = this.car;
        const foot = AmbientTrams.footprint(car.line.row, car.image.x, GS, car.image.width, car.image.height);
        const cell = TramRide.alightCell(foot, side, (x, y) => scene.checkCollision(player, x, y, x, y));
        if (!cell) { this.say('No room to get off on this side'); return; }
        player.gridX = cell.x;
        player.gridY = cell.y;
        player.sprite.x = cell.x * GS + GS / 2;
        player.sprite.y = cell.y * GS + GS / 2;
        player.facingX = 0;                         // their back to the car
        player.facingY = side;
        player.updateDirectionSprite(0, side);
        this.end();
        scene.checkTransporter();                   // as a finished step does: a door beside a stop is walked through
    }

    /** The room is being swapped (RoomManager.applyRoomSwap, which places the player): a ride in progress is over. */
    onRoomChange() {
        if (this.car) this.end();
    }

    /** Off the car, wherever the player is now. */
    end() {
        const player = this.scene.player;
        this.car = null;
        this.carried = false;
        this.halted = false;
        player.setIdleFrame();
        player.sprite.setVisible(true);
    }

    /** Is the ridden car standing (at a stop or a terminus) right now? */
    standing() {
        const car = this.car;
        return !!(car && car.plan && AmbientTrams.at(car.plan, car.t).stopped);
    }

    say(keyboardText) {
        const scene = this.scene;
        if (scene.shop) scene.shop.toast(Hints.text(scene, keyboardText));
    }
}

/**
 * What the direction held this frame (`heading`, { x, y } of -1 / 0 / 1) does
 * to a rider: { carried, side }. `carried` is "the key that boarded has not
 * been let go yet" - that key walked the player into the car, so held on it
 * gets nobody off - and it ends with the first frame nothing is held. After
 * that, up or down while the car is `halted` is a `side` to get off on (-1
 * north, 1 south); left and right, and anything while the car moves, are
 * nothing (side 0).
 */
TramRide.step = (carried, heading, halted) => {
    if (!heading.x && !heading.y) return { carried: false, side: 0 };
    if (carried) return { carried: true, side: 0 };
    return { carried: false, side: halted && heading.y ? Math.sign(heading.y) : 0 };
};

/**
 * The cell a rider is put off on: beside the car's footprint `foot`
 * ({ x0, x1, y0, y1 } cells, AmbientTrams.footprint) on `side` (-1 the row
 * north of it, 1 the row south), the column nearest the car's middle that
 * `free(x, y)` allows, west first of two as near. { x, y }, or null when the
 * whole side is blocked: it never falls to the other side.
 */
TramRide.alightCell = (foot, side, free) => {
    const y = side < 0 ? foot.y0 - 1 : foot.y1 + 1;
    const mid = Math.floor((foot.x0 + foot.x1) / 2);
    const columns = [];
    for (let x = foot.x0; x <= foot.x1; x++) columns.push(x);
    columns.sort((a, b) => Math.abs(a - mid) - Math.abs(b - mid) || a - b);
    for (const x of columns) if (free(x, y)) return { x, y };
    return null;
};

if (typeof window !== 'undefined') window.TramRide = TramRide;
