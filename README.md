# Open Cog Invasion Online #

This repository is derived from the defunct and open-source version of [Cog Invasion Online](https://github.com/Cog-Invasion-Online/cio-src).

However, this version has been upgraded to **Python 3.9.1** with the latest engine, and doesn't support the dependencies and **Panda3D** version included in the official **Cog Invasion Online**.

## To-Do List
- [x] Upgrade to **Python 3.9.1**
- [x] Upgrade to the latest version of **Panda3D**
- [ ] Improve core game code (**IN PROGRESS**)
- [ ] Fully support OSX/Darwin
- [ ] Rewrite libpandabsp (*Switch to Render Pipeline?*)
- [ ] Remove references to Disney characters
- [ ] Add localization/multiple language support
- [ ] Remake Uno as a tabletop game
- [ ] Introduce the new **Minigame Area**
- [ ] Recreate Make-A-Toon
- [ ] Delete low-quality and repetitive copied Disney code for zones
- [ ] Setup a build bot to build the game and the dependencies

### Notice
This version uses the `OPENCIOENGINE` environment variable instead of the `CIOENGINE` environment variable. Point that variable to the directoy where you built a 64-bit version of Panda3D. Click [here](https://github.com/xMakerx/OpenCIO-Panda3D) to visit the maintained **Panda3D** repository for this project.

**WARNING: ** origin/master contains Python 2.7 code. Pull from the `py3` branch to get the Python 3.9 code.

### Attention Darwin/OSX Users
This project doesn't currently support the Mac operating system because of its reliance on [**Zoner's Half Life Tools**](http://zhlt.info/) which is included in `libpandabsp`. Until that is rewritten and/or removed I cannot natively support Mac like I intend to. Linux/Ubuntu; however, *should* work okay.
