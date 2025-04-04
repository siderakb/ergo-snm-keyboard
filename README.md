# ErgoSNM Keyboard

[![license](https://img.shields.io/badge/License-CERN--OHL--P_v2-limegreen)](https://github.com/siderakb/ergo-snm-keyboard/blob/main/LICENSE-CERN-OHL-P)
[![docs.rs](https://img.shields.io/badge/Docs-latest-blue)](https://siderakb.ziteh.dev/docs/ergosnm/intro)
[![kicad](https://img.shields.io/badge/KiCad-v7-orange)](https://github.com/siderakb/ergo-snm-keyboard/tree/main/ErgoSNM_Keyboard)

![](https://imgur.com/hzSMu2A.jpg)

*ErgoSNM* \- a split ergonomic keyboard integrated with a trackball, designed to encourage people to leave their mouse behind.

- 64 keys in total.
    - Left half 29 + 6 keys.
    - Right half 29 keys + trackball.
- Cherry MX style switches, hot-swap available.
- USB Type-C.
- Column-staggered layout.
- The trackball can replace all mouse operations, allowing your right hand to stay on the *home row*.
    - Cursor movement and scrolling.
    - With the Combos feature:
        - *J*+*K* performs the left click
        - *K*+*L* performs the right click
        - *J*+*L* performs the middle click.

Introduction Video:

<a href="https://youtu.be/mWoAi_D721U" target="_blank">
  <img src="https://i.imgur.com/3YvQYrx.png" alt="Thumbnail" width="480">
</a>



| Rev   | MCU                       | Note                                     | Video                                               |
| ----- | ------------------------- | ---------------------------------------- | --------------------------------------------------- |
| `1.x` | Pro Micro (ATmega32U4)    | Experimental version                     |                                                     |
| `2.x` | RaspberryPi **RP2040**    | The first version suitable for daily use | [demo](https://youtu.be/1BXKdrCFn6c)                |
| `3.x` | Nordic **nRF52840** (E73) | First wireless experimental version      | [demo](https://www.youtube.com/watch?v=TtJiaOGiEaQ) |
| `4.x` | ???                       | ⚡In progress                             |                                                     |

Build guide and more information can be found in the [📖Docs](https://siderakb.ziteh.dev/docs/ergosnm/intro)

## Clone

```bash
git clone --recurse-submodules https://github.com/siderakb/ergo-snm-keyboard.git
```

If `key-switches.pretty` folder is empty, run:

```bash
git submodule update --init --recursive
```

## Firmware

- Vial QMK: [siderakb/vial-qmk](https://github.com/siderakb/vial-qmk/tree/siderakb/main/keyboards/siderakb/ergosnm) (*siderakb/main* branch)
- nRF: [siderakb/ergo-snm-nrf-firmware](https://github.com/siderakb/ergo-snm-nrf-firmware)

## License

Hardware available under the [CERN-OHL-P v2](/LICENSE) permissive license.
