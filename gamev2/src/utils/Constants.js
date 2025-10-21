/**
 * Constants - Game-wide constant values
 */

/**
 * Depth layer constants for rendering order
 * Lower values render behind higher values
 */
const DEPTH = {
    BACKGROUND: -1000,
    FLOOR_LAYER_BASE: -500,  // Base for floor layers (z < 2)
    OBJECTS: 0,
    TRANSPORTERS: 0,
    PLAYER: 100,
    ABOVE_PLAYER_BASE: 200,  // Base for layers above player (z >= 2)
    NPC_LABELS: 10,
    TRANSPORTER_LABELS: 10,
    HUD_BACKGROUND: 1000,
    HUD_TEXT: 1001,
    CREDITS_OVERLAY: 2000,
    CREDITS_PANEL: 2001,
    CREDITS_TEXT: 2002
};

/**
 * Timing constants (in milliseconds)
 */
const TIMING = {
    ROOM_FADE_OUT: 250,
    ROOM_FADE_HOLD: 250,
    ROOM_FADE_IN: 250,
    DEFAULT_MOVE_DURATION: 200,
    DEFAULT_NPC_WANDER_INTERVAL: 5000
};

/**
 * Color constants (hex values)
 */
const COLORS = {
    HUD_BACKGROUND: 0x000000,
    HUD_TEXT: '#ffffff',
    CAMERA_BACKGROUND: '#000000',
    CREDITS_OVERLAY: 0x000000,
    CREDITS_PANEL: 0x1a1a1a,
    CREDITS_BORDER: 0x666666,
    NPC_LABEL_TEXT: '#ffffff',
    NPC_LABEL_BG: '#000000',
    TRANSPORTER_LABEL_TEXT: '#00ff00',
    TRANSPORTER_LABEL_BG: '#000000'
};

/**
 * UI dimension constants
 */
const UI = {
    HUD_HEIGHT: 40,
    HUD_ALPHA: 0.8,
    HUD_PADDING: 10,
    CREDITS_PANEL_WIDTH: 400,
    CREDITS_PANEL_HEIGHT: 300,
    CREDITS_LINE_HEIGHT: 24,
    CREDITS_OVERLAY_ALPHA: 0.85,
    CREDITS_BORDER_WIDTH: 2
};

/**
 * Font constants
 */
const FONTS = {
    HUD: 'PressStart2P',
    HUD_SIZE: '16px',
    NPC_LABEL: 'PixelOperatorMonoBold',
    NPC_LABEL_SIZE: '16px',
    TRANSPORTER_LABEL: 'PixelOperatorMonoBold',
    TRANSPORTER_LABEL_SIZE: '16px',
    CREDITS_TITLE: 'PixelOperatorMonoBold',
    CREDITS_TITLE_SIZE: '32px',
    CREDITS_TEXT: 'PixelOperatorMono',
    CREDITS_TEXT_BOLD: 'PixelOperatorMonoBold',
    CREDITS_TEXT_SIZE: '24px'
};

/**
 * Game mechanics constants
 */
const MECHANICS = {
    DEFAULT_GRID_SIZE: 64,
    DEFAULT_WORLD_WIDTH: 960,
    DEFAULT_WORLD_HEIGHT: 640,
    DEFAULT_DEADZONE_CELLS: 4,
    DEFAULT_NPC_WANDER_RADIUS: 2,
    SPEED_MULTIPLIER_SHIFT: 2,
    MAX_LAYER_ROWS: 30,  // For Y-sorting within layers
    LAYER_DEPTH_SPACING: 100  // Depth units between layers
};

/**
 * Animation constants
 */
const ANIMATION = {
    DEFAULT_FRAME_RATE: 10,
    LOOP_FOREVER: -1,
    PLAY_ONCE: 0
};

/**
 * Direction constants
 */
const DIRECTION = {
    UP: 'up',
    DOWN: 'down',
    LEFT: 'left',
    RIGHT: 'right',
    DEFAULT: 'down'
};

/**
 * NPC wander directions
 * 0 = stay in place, 1-4 = cardinal directions
 */
const WANDER_DIRECTION = {
    STAY: 0,
    LEFT: 1,
    RIGHT: 2,
    UP: 3,
    DOWN: 4
};
