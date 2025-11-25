# eis-quads
A windows desktop tool with hovering four-quadrant task management panel (Eisenhower matrix).

It is aimed for a **simple** desktop widget rather than a complicated task managing system.

![usage example](https://github.com/user-attachments/assets/194cf266-6cda-4507-87a4-69dbf6eb754b)

## Usage
After running, it shows up as a docking tab. Drag it anywhere. Press Esc or right click on the tab to quit.

### Tasks
- **Create**: double-click anywhere on the empty canvas. A wild dialog appears; name your task then press enter.
- **Move**: click and drag can move a dot around. It avoids crossing two quadrants or overlapping with other tasks by itself.
- **Complete**: double-click a task dot. It gets struck through, fading into irrelevance like my hopes and dreams.
- **Delete**: currently no explicit "delete" for tasks. A completed and isolated task (i.e. not linked with other tasks) will be removed on next startup. You can also 'undo' a recent task. 

### Links
- **Add Link**: middle-click and drag from a dot to another will create an arrowed curve in between, if you'd like to also keep tasks' causalities.
- **Remove Link**: double-click the arrow line itself. Yes it requires a bit of precision.

### Commands
Type these blindly into the window. There is no command bar. (Just have faith)
- `clr`: clear **all** tasks. Careful about this.
- `exit`: quit the application.
- `lock`: lock tasks in place.
- `free`: unlock tasks.
- `reload`: reload tasks from disk immediately. It then reads JSON storage, and also removes completed tasks.
- `recover`: reset all tasks to last startup status, useful when you play randomly with your tasks.
- `bg`: open a file dialog to set a custom background image.

Other shortcuts:
- `Ctrl+Z`: undo.
- `Ctrl+Y` `Ctrl+Shift+Z`: redo. I vote for the latter.
- `Esc`: exit app.
- `F5`: same as "reload".

### Background Image
Load a new image by blindly typing `bg`, select img, then:
- **Pan**: Left-click and drag.
- **Zoom**: Scroll wheel.
- **Opacity**: `Alt` + Scroll wheel.
- **Confirm**: Press `Enter` to save the background state and return to task management.

### Misc
There is known problem with multiple monitor support. It flies everywhere.

***

Vibe-coded with gemini 3 pro.
M 2025.11
