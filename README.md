# ErgoSNM Keyboard

![](https://i.imgur.com/ovP1uKJ.jpg)

*ErgoSNM* \- an ergonomic split keyboard that aims to make people leave their mouse behind.

Features introduction, build guides and more information can be found in the [Wiki:book:](https://github.com/ziteh/ergo-snm-keyboard/wiki)

## Footprint 

If `key-switches.pretty` folder is empty, run `git submodule update --init` to clone submodule.

## Related Repositories

- Hardware
  - [ergo-snm-keyboard](https://github.com/ziteh/ergo-snm-keyboard) (*this repo*): Hardware design files for the ErgoSNM keyboard. Main repo for ErgoSNM.
  - [rp-micro](https://github.com/ziteh/rp-micro): A Pro Micro compatible RP2040 board PCB files. Used as a core control board for the keyboards.
  - [mdbt-micro](https://github.com/ziteh/mdbt-micro): A Pro Micro comatible nRF52840 board PCB files. Used as a control board for Bluetooth/wireless keyboards.
  - [next-micro](https://github.com/ziteh/next-micro): A Pro Micro/Elite-C compatible ATmega32U4 board design for keyboards, has USB-C and 25 available pins.
  - [pmw3360-pcb](https://github.com/ziteh/pmw3360-pcb): PMW3360 optical mouse sensor breakout board PCB files. Used for trackball.
  - [key-switches.pretty](https://github.com/ziteh/key-switches.pretty): Mechanical keyboard switches KiCad footprint library.
- Firmware
  - [ziteh/vial-qmk (*zite/ergosnm* branch)](https://github.com/ziteh/vial-qmk/tree/zite/ergosnm/keyboards/zite/ergosnm): The Vial QMK firmware for ErgoSNM.
