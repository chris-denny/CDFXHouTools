"""
Utility functions for color conversion.

Parameters:
    color (dict):
        A dictionary of color values, where the keys are the names of the color channels
        and the values are the color channel values.
    conversion_func (callable):
        A function that takes a color value as input and returns the converted color value
        based on the conversion function.

Returns:
    A dictionary of color values converted based on the specified conversion function.
"""


def convert_color(color: dict, conversion_func: callable) -> dict:
    """Apply a conversion function to each color in a dictionary"""

    # Check is the values in the color dictionary are numbers
    if not all(isinstance(value, (int, float)) for value in color.values()):
        raise ValueError("Color values must be numbers")
    else:
        # Convert the color values using the conversion function and return the result
        return {name: conversion_func(value) for name, value in color.items()}


def convert_srgb_to_linear(color) -> float:
    """Convert sRGB color to linear color space"""
    if color <= 0:
        return 0
    elif color <= 0.04045:
        return color / 12.92
    else:
        return ((color + 0.055) / 1.055) ** 2.4


def convert_linear_to_srgb(color) -> float:
    """Convert linear color to sRGB color space"""
    if color <= 0:
        return 0
    elif color <= 0.0031308:
        return color * 12.92
    else:
        return 1.055 * (color ** (1 / 2.4)) - 0.055
