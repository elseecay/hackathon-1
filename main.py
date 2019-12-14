import pandas as pd
import cv2
from cv2 import imwrite, imread
from PIL import Image
import glob, os, sys
import numpy as np
import math
from pathlib import Path
import pdf2image
import pytesseract
import random
import string


def apply_threshold(gray_img):
    avg = 0
    for i in range(gray_img.shape[0]):
        for j in range(gray_img.shape[1]):
            avg += gray_img[i][j]
    avg = int(avg / gray_img.shape[0] / gray_img.shape[1])
    return cv2.threshold(gray_img, avg, 255, cv2.THRESH_BINARY)[1]


def pdf_to_images(pdf_path, pdf_images_dir=None):
    if not pdf_images_dir:
        pdf_images_dir = './pdf_images'
    pdf_path = os.path.abspath(pdf_path)
    pdf_images_dir = os.path.abspath(pdf_images_dir)
    if not os.path.exists(pdf_images_dir):
        os.mkdir(pdf_images_dir)
    count = 0
    for page in pdf2image.convert_from_path(pdf_path, 200):
        page.save(os.path.join(pdf_images_dir, str(count) + '.jpg'), quality=95)
        count += 1
    result = []
    for i in range(count):
        result.append(cv2.cvtColor(cv2.imread(os.path.join(pdf_images_dir, str(i) + '.jpg')), cv2.COLOR_BGR2GRAY))
    return result


def crop_image_to_lines(img):
    img = img[:, 0:420]
    height, width = img.shape
    img = apply_threshold(img)
    split_rows = []
    for i in range(height):
        is_white = True
        for j in range(width):
            if img[i, j] == 0:
                is_white = False
                break
        if is_white:
            split_rows.append(i)
    cnt = 1
    delete_indexes = []
    for i in range(1, len(split_rows)):
        if split_rows[i] == split_rows[i - 1] + 1:
            cnt += 1
        else:
            if cnt > 6:
                for line in range(i - cnt - 1, i):
                    if line == i - cnt + 3 or line == i - 4:
                        continue
                    delete_indexes.append(split_rows[line])
            cnt = 1
    indexes = list(filter(lambda x: x not in delete_indexes, split_rows))
    imgs = []
    for i in range(len(indexes) - 1):
        cropped = np.array(img[indexes[i]:indexes[i + 1], :])
        h = indexes[i + 1] - indexes[i]
        w = width
        cnt = 0
        for k in range(h):
            is_white = True
            for l in range(w):
                if cropped[k, l] == 0:
                    is_white = False
                    break
            if is_white:
                cnt += 1
        if cnt != h:
            imgs.append(cropped)
    return imgs


def get_blur_img(img):
    kernel = np.ones((2, 2), np.float32) / 4
    return cv2.filter2D(img, -1, kernel)


def line_to_symbols(line):
    line = cv2.copyMakeBorder(line, 0, 0, 1, 1, cv2.BORDER_CONSTANT, value=255)
    result = []
    white_column_indexes = []
    for c in range(line.shape[1]):
        is_white = True
        for r in range(line.shape[0]):
            if line[r, c] == 0:
                is_white = False
                break
        if is_white:
            white_column_indexes.append(c)
    cnt = 1
    for i in range(1, len(white_column_indexes)):
        if white_column_indexes[i] == white_column_indexes[i - 1] + 1:
            cnt += 1
        else:
            if cnt > 10:
                result.append(' ')
            cnt = 1
            char_img = cv2.copyMakeBorder(line[:, white_column_indexes[i - 1] + 1:white_column_indexes[i]], 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=255)
            result.append(pytesseract.image_to_string(get_blur_img(char_img), 'rus', config="--psm 7 --oem 3"))
    if len(result) and result[0] == ' ':
        del result[0];
    if len(result) and result[-1] == ' ':
        del result[-1]
    return result


def get_page_km(page_img) -> int:
    line = page_img[2020:2105, 1490:1515]
    line = cv2.rotate(line, cv2.ROTATE_90_COUNTERCLOCKWISE)
    chars = line_to_symbols(line)
    try:
        return int(''.join(chars))
    except:
        return None


def random_string(length=10):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def save_pdf_bytearray(pdf: bytearray) -> str:
    name = random_string()
    with open(f'{name}.pdf', 'wb') as f:
        f.write(pdf)
    return f'{name}.pdf'


def get_ush_row(splitted):
    if len(splitted) != 6:
        return None
    if splitted[1] != 'УШ':
        return None
    result = {'type': 'BRD'}
    names = {0: 'meter', 1: 'type', 2: 'main_val', 3: 'val1', 4:'val2', 5: 'val3'}
    indexes = [0, 2, 3, 4, 5]
    for i in indexes:
        try:
            result[names[i]] = int(splitted[i])
        except:
            return None
    return result


def analyze_pdf(pdf_path):
    result = []
    pages = pdf_to_images(pdf_path, f'./{random_string()}')
    for p in pages:
        lines = crop_image_to_lines(p)
        for line_index, l in enumerate(lines):
            if line_index >= len(lines) - 2:
                continue
            splitted = ''.join(line_to_symbols(l)).upper().split(' ')
            ush_row = get_ush_row(splitted)
            km = get_page_km(p)
            if not ush_row or not km:
                continue
            ush_row['meter'] += km * 1000
            result.append(ush_row)
    return result


x = analyze_pdf('01_январь.pdf')
print(x)

#for i in analyze_pdf('01_январь.pdf'):
#    print(i)

#jpgs = pdf_to_images('01_январь.pdf')
#for i in range(5, 15):
#    print(get_page_km(jpgs[i]))
# lines = crop_image_to_lines(jpgs[0])
# for i in range(1, 11):
#     chars = line_to_symbols(lines[i])
#     print(chars)



