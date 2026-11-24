"""Scratch 3.0 competition task definitions registry."""

from . import (
    task_01_pizza,
    task_03_checkerboard,
    task_04_bricks,
    task_07_bath,
    task_08_metronome,
    task_09_traffic_light,
    task_10_auto_door,
    task_15_stopwatch,
    task_16_mash_speed,
    task_17_center_stop,
    task_18_roulette,
    task_19_bomb_game,
    task_24_domino,
    task_25_fireworks,
    task_26_balloon,
    task_27_vacuum_robot,
)

ALL_TASKS = [
    task_01_pizza,
    task_03_checkerboard,
    task_04_bricks,
    task_07_bath,
    task_08_metronome,
    task_09_traffic_light,
    task_10_auto_door,
    task_15_stopwatch,
    task_16_mash_speed,
    task_17_center_stop,
    task_18_roulette,
    task_19_bomb_game,
    task_24_domino,
    task_25_fireworks,
    task_26_balloon,
    task_27_vacuum_robot,
]

# Backward-compatible alias
PILOT_TASKS = ALL_TASKS

__all__ = [
    "ALL_TASKS",
    "PILOT_TASKS",
    "task_01_pizza",
    "task_03_checkerboard",
    "task_04_bricks",
    "task_07_bath",
    "task_08_metronome",
    "task_09_traffic_light",
    "task_10_auto_door",
    "task_15_stopwatch",
    "task_16_mash_speed",
    "task_17_center_stop",
    "task_18_roulette",
    "task_19_bomb_game",
    "task_24_domino",
    "task_25_fireworks",
    "task_26_balloon",
    "task_27_vacuum_robot",
]
