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


def apply_threshold(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    avg = 0
    for i in range(gray.shape[0]):
        for j in range(gray.shape[1]):
            avg += gray[i][j]
    avg = int(avg / gray.shape[0] / gray.shape[1])
    return cv2.threshold(gray, avg, 255, cv2.THRESH_BINARY)[1]


def get_km_img(img):
    return img[2020:2105, 1490:1515]


def pdf_to_images(pdf_path, pdf_images_dir=None):
    if not pdf_images_dir:
        pdf_images_dir = './pdf_images'
    pdf_path = os.path.abspath(pdf_path)
    pdf_images_dir = os.path.abspath(pdf_images_dir)
    if not os.path.exists(pdf_images_dir):
        os.mkdir(pdf_images_dir)
    count = 0
    for page in pdf2image.convert_from_path(pdf_path, 200):
        page.save(os.path.join(pdf_images_dir, str(count) + '.jpg'), dpi=(32, 32), quality=95)
        count += 1
    result = []
    for i in range(count):
        result.append(cv2.imread(os.path.join(pdf_images_dir, str(i) + '.jpg')))
    return result

def crop_image_to_lines(img):
    img = img[:, 0:420]
    height, width, _ = img.shape
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

def generate_new_img_with_white_borders(img, i, white_column_indexes):
    new_img = np.ones((img.shape[0] * 2, white_column_indexes[i] - white_column_indexes[i - 1] - 1 + 20), np.uint8)

    for k in range(new_img.shape[0]):
        for l in range(new_img.shape[1]):
            new_img[k, l] = 255

    for k in range(int(img.shape[0] / 2) - 1, int(img.shape[0] / 2) - 1 + img.shape[0]):
        for l in range(10, white_column_indexes[i] - 1 - white_column_indexes[i - 1] + 10):
            new_img[k][l] = img[k - int(img.shape[0] / 2) + 1, l - 10 + white_column_indexes[i - 1] + 1]

    return new_img

def line_to_symbols(line):
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
    if white_column_indexes[0] != 0:
        new_img = generate_new_img_with_white_borders(line, 0, white_column_indexes)
        result.append(pytesseract.image_to_string(get_blur_img(new_img), 'rus', config="--psm 7 --oem 3"))
    cnt = 1
    white_col_cnts = []
    for i in range(1, len(white_column_indexes)):
        if white_column_indexes[i] == white_column_indexes[i - 1] + 1:
            cnt += 1
        else:
            if cnt > 10:
                result.append(' ')
            cnt = 1    


            new_img = generate_new_img_with_white_borders(line, i, white_column_indexes)

            result.append(pytesseract.image_to_string(get_blur_img(new_img), 'rus', config="--psm 7 --oem 3"))
    return result



jpgs = pdf_to_images('01.pdf')
lines = crop_image_to_lines(jpgs[0])

for i in range(1, 11):
    chars = line_to_symbols(lines[i])
    print(chars)