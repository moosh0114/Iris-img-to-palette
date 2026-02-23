# Iris-Color-Processor

[![GitHub last commit](https://img.shields.io/github/last-commit/moosh0114/Iris-img-to-palette.svg)](https://github.com/moosh0114/Iris-img-to-palette)
[![GitHub repo size](https://img.shields.io/github/repo-size/moosh0114/Iris-img-to-palette.svg)](https://github.com/moosh0114/Iris-img-to-palette)
[![Lyra](https://img.shields.io/badge/Designed_with-Lyra-FFC6EC?logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAwIiBoZWlnaHQ9IjEzMDAiIHZpZXdCb3g9IjAgMCA4MDAgMTMwMCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHJlY3QgeD0iNzUiIHk9Ijc1IiB3aWR0aD0iNjUwIiBoZWlnaHQ9IjExNTAiIHN0cm9rZT0idXJsKCNwYWludDBfbGluZWFyXzIxNjVfNykiIHN0cm9rZS13aWR0aD0iMTUwIi8+CjxkZWZzPgo8bGluZWFyR3JhZGllbnQgaWQ9InBhaW50MF9saW5lYXJfMjE2NV83IiB4MT0iNDAwIiB5MT0iMCIgeDI9IjQwMCIgeTI9IjEzMDAiIGdyYWRpZW50VW5pdHM9InVzZXJTcGFjZU9uVXNlIj4KPHN0b3Agc3RvcC1jb2xvcj0iI0JCRkZFRCIvPgo8c3RvcCBvZmZzZXQ9IjAuNjk3MTE1IiBzdG9wLWNvbG9yPSIjRkZFQ0Y0Ii8+CjwvbGluZWFyR3JhZGllbnQ+CjwvZGVmcz4KPC9zdmc+)](https://github.com/zzztzzzt/Lyra-AI)

<br>
<img src="https://github.com/moosh0114/Iris-img-to-palette/blob/main/logo/logo.png" alt="Iris-Color-Processor" style="height: 280px; width: auto;" />

### Refinement Network for Image Color-Extraction

IMPORTANT : This project is still in the development and testing stages, licensing terms may be updated in the future. Please don't do any commercial usage currently.

## Project Dependencies Guide

[![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)](https://github.com/django/django)
[![scikit-learn](https://img.shields.io/badge/scikit_learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)](https://github.com/scikit-learn/scikit-learn)
[![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)](https://github.com/opencv/opencv)
[![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://github.com/pytorch/pytorch)

**( GUI )**

[![Alpine.js](https://img.shields.io/badge/Alpine.js-8BC0D0?style=for-the-badge&logo=alpinedotjs&logoColor=white)](https://github.com/alpinejs/alpine)
[![HTMX](https://img.shields.io/badge/HTMX-3366CC?style=for-the-badge&logo=htmx&logoColor=white)](https://github.com/bigskysoftware/htmx)
[![Tailwind CSS](https://img.shields.io/badge/tailwind_css-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)](https://github.com/tailwindlabs/tailwindcss)

**[ for Dependencies Details please see the end of this README ]**

Iris-Color-Processor uses Django for GUI backend and uses scikit-learn & OpenCV for image color extraction, leverages K-Means clustering, and outputs results in the OKLCH color space to ensure perceptual uniformity and high-fidelity color analysis. It now also incorporates PyTorch for potential deep learning-based color analysis workflows. Django & scikit-learn are licensed under the BSD 3-Clause License. OpenCV is licensed under the Apache-2.0 License. PyTorch is BSD-style licensed.

Iris-Color-Processor uses uv for dependency and environment management. uv has multiple licenses.

Iris-Color-Processor uses Alpine.js, HTMX & Tailwind CSS for GUI showing. Alpine.js & Tailwind CSS licensed under the MIT License. HTMX licensed under Zero-Clause BSD License.

## Install ( PyPI )
### Install Iris-Color-Processor As Package

## Try GUI To Test

For Python Version : 

1. install Python : [https://www.python.org/downloads/](https://www.python.org/downloads/)

## Run Scripts To Test ( Python )

upgrade : `python -m pip install --upgrade pip`

use uv : `python -m pip install uv` & `python -m uv sync`

run scripts : `python -m uv run scripts/[your_py_scripts.py]`

extract dominant colors : `python -m uv run scripts/extract_colors.py` ( processes `test.jpg` and outputs dominant colors )

## Color Standard: OKLCH

This project uses $Oklch$ ($L, c, h$) coordinates for better alignment with human visual perception.

For achromatic colors ($c < 10^{-9}$), hue is normalized automatically to $h=0.0$.

Color values are reported with 6-decimal precision for scientific consistency.

## Project Dependencies Details

Django License : [https://github.com/django/django/blob/main/LICENSE](https://github.com/django/django/blob/main/LICENSE)
<br>

scikit-learn License : [https://github.com/scikit-learn/scikit-learn?tab=BSD-3-Clause-1-ov-file#readme](https://github.com/scikit-learn/scikit-learn?tab=BSD-3-Clause-1-ov-file#readme)
<br>

OpenCV License : [https://github.com/opencv/opencv/blob/4.x/LICENSE](https://github.com/opencv/opencv/blob/4.x/LICENSE)
<br>

PyTorch License : [https://github.com/pytorch/pytorch/blob/main/LICENSE](https://github.com/pytorch/pytorch/blob/main/LICENSE)
<br>

uv License : [https://github.com/astral-sh/uv/blob/main/LICENSE-MIT](https://github.com/astral-sh/uv/blob/main/LICENSE-MIT) & another Apache-2.0 [License](https://github.com/astral-sh/uv/blob/main/LICENSE-APACHE)
<br>

Alpine.js License : [https://github.com/alpinejs/alpine/blob/main/LICENSE.md](https://github.com/alpinejs/alpine/blob/main/LICENSE.md)
<br>

HTMX License : [https://github.com/bigskysoftware/htmx/blob/master/LICENSE](https://github.com/bigskysoftware/htmx/blob/master/LICENSE)
<br>

Tailwind CSS License : [https://github.com/tailwindlabs/tailwindcss/blob/main/LICENSE](https://github.com/tailwindlabs/tailwindcss/blob/main/LICENSE)
