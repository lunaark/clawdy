#!/usr/bin/env python3
"""Clawdy Desktop Pet — 入口文件（向后兼容）"""

from clawdy.app import ClawdPet

if __name__ == '__main__':
    pet = ClawdPet()
    pet.run()
